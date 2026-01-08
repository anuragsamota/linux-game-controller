#!/usr/bin/env python3
"""
UDP-based game controller server for ultra-low latency.

Advantages over WebSocket:
- No TCP handshake overhead
- No retransmissions (lost packets acceptable for real-time input)
- Smaller packet headers
- 5-20ms lower latency typically

Protocol uses binary format instead of JSON for minimal overhead.
"""

import asyncio
import logging
import struct
from typing import Dict, Optional, Tuple

from .devices import StandardGamepad
from .devices.base_controller import BaseController

logger = logging.getLogger(__name__)


# Binary protocol constants
PACKET_CONNECT = 0x01
PACKET_DISCONNECT = 0x02
PACKET_BUTTON = 0x03
PACKET_AXIS = 0x04
PACKET_PING = 0x05
PACKET_PONG = 0x06

# Response codes
RESPONSE_OK = 0x00
RESPONSE_ERROR = 0xFF


class DeviceRegistryUDP:
    """Manages virtual devices for UDP connections."""
    
    def __init__(self):
        self._constructors = {
            "standard": StandardGamepad,
        }
        self._instances: Dict[str, BaseController] = {}
        self._client_counts: Dict[str, int] = {}
        self._client_devices: Dict[Tuple[str, int], str] = {}  # (ip, port) -> device_name

    def acquire(self, name: str, display_name: str, client_addr: Tuple[str, int]) -> BaseController:
        """Get or create device for client."""
        key = name.lower()
        if key not in self._constructors:
            raise KeyError(f"Unknown controller type '{name}'")
        
        # Create device if doesn't exist
        if key not in self._instances:
            logger.info("Creating UDP device: %s", key)
            self._instances[key] = self._constructors[key](name=display_name or key)
            self._client_counts[key] = 0
        
        # Track this client
        self._client_devices[client_addr] = key
        self._client_counts[key] += 1
        logger.info("Device %s now has %d UDP client(s)", key, self._client_counts[key])
        
        return self._instances[key]

    def release(self, client_addr: Tuple[str, int]) -> None:
        """Release device when client disconnects."""
        if client_addr not in self._client_devices:
            return
        
        key = self._client_devices[client_addr]
        del self._client_devices[client_addr]
        
        if key in self._client_counts:
            self._client_counts[key] = max(0, self._client_counts[key] - 1)
            logger.info("Device %s now has %d UDP client(s)", key, self._client_counts[key])
            
            # Destroy device when last client leaves
            if self._client_counts[key] == 0:
                logger.info("Destroying UDP device: %s (no clients)", key)
                device = self._instances.pop(key)
                device.close()

    def get_device(self, client_addr: Tuple[str, int]) -> Optional[BaseController]:
        """Get device for connected client."""
        key = self._client_devices.get(client_addr)
        if key:
            return self._instances.get(key)
        return None


class UDPControllerProtocol(asyncio.DatagramProtocol):
    """UDP protocol handler for game controller."""
    
    def __init__(self, registry: DeviceRegistryUDP):
        self.registry = registry
        self.transport = None

    def connection_made(self, transport):
        """Called when protocol is started."""
        self.transport = transport
        logger.info("UDP server ready")

    def datagram_received(self, data: bytes, addr: Tuple[str, int]):
        """Handle incoming UDP datagram."""
        try:
            if len(data) < 1:
                return
            
            packet_type = data[0]
            
            if packet_type == PACKET_CONNECT:
                self._handle_connect(data[1:], addr)
            elif packet_type == PACKET_DISCONNECT:
                self._handle_disconnect(addr)
            elif packet_type == PACKET_BUTTON:
                self._handle_button(data[1:], addr)
            elif packet_type == PACKET_AXIS:
                self._handle_axis(data[1:], addr)
            elif packet_type == PACKET_PING:
                self._handle_ping(addr)
            else:
                logger.warning("Unknown packet type: 0x%02x from %s", packet_type, addr)
                
        except Exception as e:
            logger.error("Error processing datagram from %s: %s", addr, e)
            self._send_error(addr, str(e))

    def _handle_connect(self, payload: bytes, addr: Tuple[str, int]):
        """Handle connect packet.
        
        Format: CONNECT | device_name_len (1 byte) | device_name | display_name_len (1 byte) | display_name
        """
        try:
            if len(payload) < 2:
                raise ValueError("Invalid connect packet")
            
            device_name_len = payload[0]
            if len(payload) < 1 + device_name_len + 1:
                raise ValueError("Invalid connect packet length")
            
            device_name = payload[1:1+device_name_len].decode('utf-8')
            
            offset = 1 + device_name_len
            display_name_len = payload[offset]
            display_name = payload[offset+1:offset+1+display_name_len].decode('utf-8')
            
            # Acquire device
            device = self.registry.acquire(device_name, display_name, addr)
            
            # Send OK response
            response = bytes([RESPONSE_OK, PACKET_CONNECT])
            self.transport.sendto(response, addr)
            logger.info("UDP client connected from %s - device: %s", addr, display_name)
            
        except Exception as e:
            logger.error("Connect error: %s", e)
            self._send_error(addr, str(e))

    def _handle_disconnect(self, addr: Tuple[str, int]):
        """Handle disconnect packet."""
        self.registry.release(addr)
        response = bytes([RESPONSE_OK, PACKET_DISCONNECT])
        self.transport.sendto(response, addr)
        logger.info("UDP client disconnected: %s", addr)

    def _handle_button(self, payload: bytes, addr: Tuple[str, int]):
        """Handle button packet.
        
        Format: BUTTON | name_len (1 byte) | name | pressed (1 byte: 0 or 1)
        """
        try:
            device = self.registry.get_device(addr)
            if not device:
                raise ValueError("Not connected")
            
            if len(payload) < 2:
                raise ValueError("Invalid button packet")
            
            name_len = payload[0]
            if len(payload) < 1 + name_len + 1:
                raise ValueError("Invalid button packet length")
            
            name = payload[1:1+name_len].decode('utf-8')
            pressed = bool(payload[1+name_len])
            
            device.set_button(name, pressed)
            
        except Exception as e:
            logger.error("Button error: %s", e)

    def _handle_axis(self, payload: bytes, addr: Tuple[str, int]):
        """Handle axis packet.
        
        Format: AXIS | name_len (1 byte) | name | value (4 bytes float, little-endian)
        """
        try:
            device = self.registry.get_device(addr)
            if not device:
                raise ValueError("Not connected")
            
            if len(payload) < 6:  # 1 + min 1 char + 4 bytes float
                raise ValueError("Invalid axis packet")
            
            name_len = payload[0]
            if len(payload) < 1 + name_len + 4:
                raise ValueError("Invalid axis packet length")
            
            name = payload[1:1+name_len].decode('utf-8')
            value_bytes = payload[1+name_len:1+name_len+4]
            value = struct.unpack('<f', value_bytes)[0]  # Little-endian float
            
            device.set_axis(name, value)
            
        except Exception as e:
            logger.error("Axis error: %s", e)

    def _handle_ping(self, addr: Tuple[str, int]):
        """Handle ping packet - respond with pong."""
        response = bytes([RESPONSE_OK, PACKET_PONG])
        self.transport.sendto(response, addr)

    def _send_error(self, addr: Tuple[str, int], message: str):
        """Send error response."""
        msg_bytes = message.encode('utf-8')
        response = bytes([RESPONSE_ERROR]) + bytes([len(msg_bytes)]) + msg_bytes
        self.transport.sendto(response, addr)


class UDPControllerServer:
    """UDP-based controller server for minimal latency."""
    
    def __init__(self, host: str = "0.0.0.0", port: int = 8766):
        self.host = host
        self.port = port
        self.registry = DeviceRegistryUDP()

    async def start(self):
        """Start UDP server."""
        logger.info("Starting UDP controller server on %s:%s", self.host, self.port)
        
        loop = asyncio.get_event_loop()
        
        # Create UDP endpoint
        transport, protocol = await loop.create_datagram_endpoint(
            lambda: UDPControllerProtocol(self.registry),
            local_addr=(self.host, self.port)
        )
        
        logger.info("UDP server listening on %s:%s", self.host, self.port)
        
        try:
            await asyncio.Future()  # Run forever
        finally:
            transport.close()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    server = UDPControllerServer()
    asyncio.run(server.start())
