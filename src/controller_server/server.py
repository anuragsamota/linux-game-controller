from __future__ import annotations

"""Async WebSocket server that forwards input events to virtual controllers."""

import asyncio
import json
import logging
from typing import Any, Dict, Optional

import websockets
from websockets.server import WebSocketServerProtocol

from .device_registry import DeviceRegistry

logger = logging.getLogger(__name__)



class ControllerServer:
    def __init__(self, host: str = "0.0.0.0", port: int = 8765) -> None:
        self.host = host
        self.port = port
        self.registry = DeviceRegistry()

    async def start(self) -> None:
        logger.info("Starting controller server on %s:%s", self.host, self.port)
        async with websockets.serve(
            self._handle,
            self.host,
            self.port,
            max_size=128 * 1024,  # Increased buffer size
            ping_interval=20,  # Keep connections alive
            ping_timeout=10,  # Faster timeout detection
            close_timeout=5,  # Faster cleanup
        ):
            try:
                await asyncio.Future()  # run forever
            except asyncio.CancelledError:
                # Graceful shutdown on cancellation (SIGTERM, task cancel, etc.)
                logger.info("Server task cancelled - shutting down gracefully")
                return

    async def _handle(self, websocket: WebSocketServerProtocol) -> None:
        client_device: Optional[str] = None
        remote_address = websocket.remote_address
        logger.info("New client connected from %s", remote_address)
        
        try:
            await self._send_json(websocket, {
                "type": "welcome",
                "devices": list(self.registry.available()),
                "schema": {
                    "connect": {"device": "standard"},
                    "disconnect": {},
                    "rename": {"name": "My Gamepad"},
                    "button": {"device": "standard", "name": "a", "pressed": True},
                    "axis": {"device": "standard", "name": "lx", "value": 0.25},
                    "ping": {},
                },
            })
            async for raw in websocket:
                try:
                    data = json.loads(raw)
                except json.JSONDecodeError:
                    await self._send_error(websocket, "invalid_json", "Could not decode message as JSON")
                    continue

                try:
                    response = await self._process_message(data, websocket, client_device)
                    if response and isinstance(response, tuple):
                        response, client_device = response
                except Exception as exc:  # noqa: BLE001
                    logger.exception("Failed to process message: %s", data)
                    await self._send_error(websocket, "invalid_message", str(exc))
                    continue

                if response is not None:
                    await self._send_json(websocket, response)
        except websockets.exceptions.ConnectionClosedOK:
            logger.info("Client disconnected normally from %s", remote_address)
        except websockets.exceptions.ConnectionClosedError as exc:
            logger.info("Client connection closed with error from %s: %s", remote_address, exc)
        except asyncio.CancelledError:
            logger.info("Client connection cancelled from %s", remote_address)
        except Exception as exc:
            logger.error("Unexpected error handling client from %s: %s", remote_address, exc)
        finally:
            # Clean up when client disconnects
            if client_device:
                try:
                    await self.registry.release(client_device)
                    logger.info("Released device: %s", client_device)
                except Exception as exc:
                    logger.error("Failed to release device %s: %s", client_device, exc)

    async def _process_message(
        self, data: Dict[str, Any], websocket: WebSocketServerProtocol, client_device: Optional[str]
    ) -> Optional[tuple | Dict[str, Any]]:
        msg_type = data.get("event")
        if msg_type is None:
            raise ValueError("Message missing 'event' field")

        # Handle lifecycle events
        if msg_type == "connect":
            if client_device:
                raise ValueError(f"Already connected to '{client_device}'; disconnect first")
            device_type = data.get("device", "standard")
            display_name = data.get("name")  # Optional display name for the device
            device = await self.registry.acquire(device_type, display_name=display_name)
            logger.info("Client connected to device: %s", device_type)
            return {"type": "ok", "connected": device_type, "name": device.name}, device_type

        if msg_type == "disconnect":
            if not client_device:
                raise ValueError("Not connected to any device")
            await self.registry.release(client_device)
            logger.info("Client disconnected from device: %s", client_device)
            return {"type": "ok"}, None

        if msg_type == "rename":
            if not client_device:
                raise ValueError("Not connected; call 'connect' first")
            # Note: device names are immutable in uinput; set name in 'connect' event instead
            new_name = data.get("name")
            if not new_name or not isinstance(new_name, str):
                raise ValueError("Rename requires a 'name' string")
            logger.warning("Device names are immutable in uinput. Set name via 'connect' event instead.")
            return {"type": "error", "message": "Device names cannot be changed after creation. Use 'name' in the connect event."}

        # Input events can optionally specify a device, otherwise use client_device
        if msg_type in ("button", "axis"):
            # Allow specifying device in the event (for multi-device support like touchpad + gamepad)
            target_device = data.get("device", client_device)
            
            if not target_device:
                raise ValueError("Not connected; call 'connect' first or specify 'device' in event")
            
            # Get or acquire the target device
            device = self.registry.get(target_device)
            if not device:
                # Auto-acquire if not already present (for touchpad use case)
                device = await self.registry.acquire(target_device)
                logger.info("Auto-acquired device: %s", target_device)

        if msg_type == "button":
            name = data.get("name")
            pressed = data.get("pressed")
            if name is None or pressed is None:
                raise ValueError("Button event requires 'name' and 'pressed'")
            device.set_button(name, bool(pressed))
            return {"type": "ok"}

        if msg_type == "axis":
            name = data.get("name")
            value = data.get("value")
            if name is None or value is None:
                raise ValueError("Axis event requires 'name' and 'value'")
            device.set_axis(name, float(value))
            return {"type": "ok"}

        if msg_type == "ping":
            return {"type": "pong"}

        raise ValueError(f"Unsupported event '{msg_type}'")


    @staticmethod
    async def _send_json(websocket: WebSocketServerProtocol, payload: Dict[str, Any]) -> None:
        try:
            await websocket.send(json.dumps(payload))
        except websockets.exceptions.ConnectionClosed:
            # Client disconnected before we could send
            pass

    @staticmethod
    async def _send_error(websocket: WebSocketServerProtocol, code: str, message: str) -> None:
        try:
            await websocket.send(json.dumps({"type": "error", "code": code, "message": message}))
        except websockets.exceptions.ConnectionClosed:
            # Client disconnected before we could send error
            pass


def run_server(host: str = "0.0.0.0", port: int = 8765) -> None:
    logging.basicConfig(level=logging.INFO, format="[%(asctime)s] %(levelname)s %(name)s: %(message)s")
    server = ControllerServer(host=host, port=port)
    try:
        asyncio.run(server.start())
    except (KeyboardInterrupt, asyncio.CancelledError):
        # Suppress traceback on Ctrl+C or cancellation; log friendly message
        logger.info("Server stopped by user")
