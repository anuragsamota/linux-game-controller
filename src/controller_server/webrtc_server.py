#!/usr/bin/env python3
"""WebRTC data-channel controller server.

Uses WebSocket signaling and a WebRTC data channel to receive controller
events via UDP (through STUN for NAT traversal and TURN for relay).
This keeps browser clients on UDP while reusing the same JSON event schema.
"""

from __future__ import annotations

import asyncio
import json
import logging
from typing import Any, Dict, Optional

import websockets
from aiortc import RTCConfiguration, RTCIceCandidate, RTCIceServer, RTCPeerConnection, RTCSessionDescription
from aiortc.rtcicetransport import Candidate
from websockets.server import WebSocketServerProtocol

from .device_registry import DeviceRegistry

logger = logging.getLogger(__name__)


# Default ICE servers: Google public STUN servers for NAT traversal
# Plus an open TURN relay for restrictive NATs (no relay required for most home/office networks)
DEFAULT_ICE_SERVERS = [
    RTCIceServer(
        urls=[
            "stun:stun.l.google.com:19302",
            "stun:stun1.l.google.com:19302",
            "stun:stun2.l.google.com:19302",
            "stun:stun3.l.google.com:19302",
            "stun:stun4.l.google.com:19302",
        ]
    ),
    # Public TURN relay for clients behind symmetric NAT or firewalls
    RTCIceServer(
        urls=[
            "turn:global.relay.metered.ca:80",
            "turn:global.relay.metered.ca:443",
            "turn:global.relay.metered.ca:443?transport=tcp",
        ],
        username="openrelayproject",
        credential="openrelayproject",
    ),
]


class WebRTCControllerServer:
    """WebRTC signaling server backed by the shared DeviceRegistry.
    
    Uses UDP data channel (via STUN/TURN) for game controller input,
    providing ultra-low latency comparable to native clients while
    working from web browsers.
    """

    def __init__(self, host: str = "0.0.0.0", port: int = 8787, registry: Optional[DeviceRegistry] = None):
        self.host = host
        self.port = port
        self.registry = registry or DeviceRegistry()
        self.ice_servers = DEFAULT_ICE_SERVERS

    async def start(self) -> None:
        """Start WebSocket signaling for WebRTC."""
        logger.info("Starting WebRTC signaling on %s:%s (UDP backend via STUN/TURN)", self.host, self.port)
        async with websockets.serve(
            self._handle_signaling,
            self.host,
            self.port,
            max_size=256 * 1024,
            ping_interval=20,
            ping_timeout=10,  # Faster timeout detection
            close_timeout=5,  # Faster cleanup
            compression=None,  # Disable compression for lower latency
        ):
            logger.info("WebRTC signaling ready. Clients will negotiate UDP data channels.")
            await asyncio.Future()  # Run forever

    async def _handle_signaling(self, websocket: WebSocketServerProtocol) -> None:
        """Handle WebRTC signaling and data channel messages for one client."""
        pc = RTCPeerConnection(RTCConfiguration(self.ice_servers))
        client_device: Optional[str] = None
        channel_ready = asyncio.Event()
        channel_ref = None
        closed = False
        connection_id = id(websocket)  # For logging

        async def cleanup() -> None:
            nonlocal closed
            if closed:
                return
            closed = True
            logger.info("[%s] Cleaning up WebRTC session", connection_id)
            if client_device:
                await self.registry.release(client_device)
            await pc.close()
            try:
                await websocket.close()
            except Exception:
                pass

        async def send_json(payload: Dict[str, Any]) -> None:
            if channel_ref and channel_ref.readyState == "open":
                try:
                    channel_ref.send(json.dumps(payload))
                    logger.debug("[%s] Sent via data channel: %s", connection_id, payload.get("type"))
                except Exception as exc:  # noqa: BLE001
                    logger.error("[%s] Failed to send on data channel: %s", connection_id, exc)

        @pc.on("icecandidate")
        async def on_icecandidate(candidate: Optional[Candidate]) -> None:
            if candidate is None:
                return
            payload = {
                "type": "candidate",
                "candidate": {
                    "candidate": candidate.to_sdp(),
                    "sdpMid": candidate.sdp_mid,
                    "sdpMLineIndex": candidate.sdp_mline_index,
                },
            }
            try:
                await websocket.send(json.dumps(payload))
            except Exception as exc:
                logger.error("[%s] Failed to send ICE candidate: %s", connection_id, exc)

        @pc.on("connectionstatechange")
        async def on_connectionstatechange() -> None:
            state = pc.connectionState
            logger.info("[%s] WebRTC connection state: %s", connection_id, state)
            if state in {"closed", "failed", "disconnected"}:
                await cleanup()

        @pc.on("datachannel")
        def on_datachannel(channel) -> None:
            nonlocal channel_ref
            channel_ref = channel
            logger.info("[%s] WebRTC data channel connected: %s", connection_id, channel.label)

            async def handle_message(message: str) -> None:
                nonlocal client_device
                try:
                    payload = json.loads(message)
                except json.JSONDecodeError:
                    logger.warning("[%s] Malformed JSON from data channel", connection_id)
                    await send_json({"type": "error", "message": "invalid_json"})
                    return

                try:
                    response = await self._process_message(payload, client_device)
                    if response and isinstance(response, tuple):
                        response, client_device = response
                    if response is not None:
                        await send_json(response)
                except Exception as exc:  # noqa: BLE001
                    logger.exception("[%s] Failed to process data channel message", connection_id)
                    await send_json({"type": "error", "message": str(exc)})

            def handle_raw_message(message: Any) -> None:
                text = message if isinstance(message, str) else message.decode("utf-8")
                asyncio.create_task(handle_message(text))

            channel.on("message", handle_raw_message)
            channel.on("close", lambda: asyncio.create_task(cleanup()))
            channel_ready.set()
            
            # Send welcome immediately after data channel opens
            asyncio.create_task(
                send_json(
                    {
                        "type": "welcome",
                        "devices": list(self.registry.available()),
                        "schema": {
                            "connect": {"device": "standard"},
                            "disconnect": {},
                            "button": {"name": "a", "pressed": True},
                            "axis": {"name": "lx", "value": 0.25},
                            "ping": {},
                        },
                    }
                )
            )

        try:
            async for raw in websocket:
                try:
                    msg = json.loads(raw)
                except json.JSONDecodeError:
                    logger.warning("[%s] Ignoring malformed signaling message", connection_id)
                    continue

                mtype = msg.get("type")
                if mtype == "offer":
                    logger.info("[%s] Received WebRTC offer", connection_id)
                    offer = RTCSessionDescription(sdp=msg["sdp"], type=msg.get("sdpType", "offer"))
                    await pc.setRemoteDescription(offer)
                    # Don't wait for data channel here; it arrives AFTER answer is sent
                    # Create and send answer immediately
                    answer = await pc.createAnswer()
                    await pc.setLocalDescription(answer)
                    response = {
                        "type": "answer",
                        "sdp": pc.localDescription.sdp,
                        "sdpType": pc.localDescription.type,
                    }
                    await websocket.send(json.dumps(response))
                    logger.info("[%s] Sent WebRTC answer", connection_id)
                    # Now wait for data channel to be established
                    await channel_ready.wait()
                    logger.info("[%s] Data channel established", connection_id)
                elif mtype == "candidate":
                    cand = msg.get("candidate")
                    if cand:
                        try:
                            ice = RTCIceCandidate(
                                sdpMid=cand.get("sdpMid"),
                                sdpMLineIndex=cand.get("sdpMLineIndex"),
                                candidate=cand.get("candidate"),
                            )
                            await pc.addIceCandidate(ice)
                        except Exception as exc:
                            logger.error("[%s] Failed to add ICE candidate: %s", connection_id, exc)
                elif mtype == "bye":
                    logger.info("[%s] Received bye", connection_id)
                    await cleanup()
                    break
        except websockets.exceptions.ConnectionClosed:  # type: ignore[attr-defined]
            logger.info("[%s] Signaling connection closed", connection_id)
        except Exception as exc:
            logger.error("[%s] Signaling error: %s", connection_id, exc)
        finally:
            await cleanup()

    async def _process_message(
        self, data: Dict[str, Any], client_device: Optional[str]
    ) -> Optional[tuple | Dict[str, Any]]:
        msg_type = data.get("event")
        if msg_type is None:
            raise ValueError("Message missing 'event' field")

        if msg_type == "connect":
            if client_device:
                raise ValueError(f"Already connected to '{client_device}'; disconnect first")
            device_type = data.get("device", "standard")
            display_name = data.get("name")
            device = await self.registry.acquire(device_type, display_name=display_name)
            logger.info("WebRTC client connected to device: %s", device_type)
            return {"type": "ok", "connected": device_type, "name": device.name}, device_type

        if msg_type == "disconnect":
            if not client_device:
                raise ValueError("Not connected to any device")
            await self.registry.release(client_device)
            logger.info("WebRTC client disconnected from device: %s", client_device)
            return {"type": "ok"}, None

        if msg_type == "button":
            # Allow specifying device in the event (for multi-device support like touchpad + gamepad)
            target_device = data.get("device", client_device)
            
            if not target_device:
                raise ValueError("Not connected; call 'connect' first or specify 'device' in event")
            
            # Get or acquire the target device
            device = self.registry.get(target_device)
            if not device:
                # Auto-acquire if not already present (for touchpad use case)
                device = await self.registry.acquire(target_device)
                logger.info("WebRTC auto-acquired device: %s", target_device)
            
            name = data.get("name")
            pressed = data.get("pressed")
            if name is None or pressed is None:
                raise ValueError("Button event requires 'name' and 'pressed'")
            device.set_button(name, bool(pressed))
            return {"type": "ok"}

        if msg_type == "axis":
            # Allow specifying device in the event (for multi-device support like touchpad + gamepad)
            target_device = data.get("device", client_device)
            
            if not target_device:
                raise ValueError("Not connected; call 'connect' first or specify 'device' in event")
            
            # Get or acquire the target device
            device = self.registry.get(target_device)
            if not device:
                # Auto-acquire if not already present (for touchpad use case)
                device = await self.registry.acquire(target_device)
                logger.info("WebRTC auto-acquired device: %s", target_device)
            
            name = data.get("name")
            value = data.get("value")
            if name is None or value is None:
                raise ValueError("Axis event requires 'name' and 'value'")
            device.set_axis(name, float(value))
            return {"type": "ok"}

        if msg_type == "ping":
            return {"type": "pong"}

        raise ValueError(f"Unsupported event '{msg_type}'")


def run_webrtc_server(host: str = "0.0.0.0", port: int = 8787) -> None:
    logging.basicConfig(level=logging.INFO, format="[%(asctime)s] %(levelname)s %(name)s: %(message)s")
    server = WebRTCControllerServer(host=host, port=port)
    asyncio.run(server.start())


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="WebRTC signaling server for virtual controller")
    parser.add_argument("--host", default="0.0.0.0", help="Host interface to bind")
    parser.add_argument("--port", type=int, default=8787, help="Signaling port")
    args = parser.parse_args()
    run_webrtc_server(host=args.host, port=args.port)