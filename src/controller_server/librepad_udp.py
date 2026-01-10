#!/usr/bin/env python3
"""
LibrePad UDP Control Protocol v0.3 Implementation

Implements the complete UDP protocol for low-latency native client support.
Supports gamepad (buttons, axes, D-pad), mouse, and keyboard input.

Protocol Reference: docs/UDPProtocol.md
"""

import asyncio
import logging
import platform
import struct
import time
from typing import Dict, Optional, Tuple
from dataclasses import dataclass

from .devices.base_controller import BaseController

logger = logging.getLogger(__name__)


# ============================================================================
# Protocol Constants
# ============================================================================

# Message Types
MSG_HELLO = 0x01
MSG_WELCOME = 0x02
MSG_PING = 0x03
MSG_PONG = 0x04
MSG_SESSION_END = 0x05
MSG_CONNECT = 0x10
MSG_DISCONNECT = 0x11
MSG_BUTTON = 0x20
MSG_AXIS = 0x21
MSG_MOUSE_MOVE = 0x22
MSG_MOUSE_BUTTON = 0x23
MSG_KEY_EVENT = 0x24
MSG_TEXT_INPUT = 0x25
MSG_MOUSE_SCROLL = 0x26
MSG_ERROR = 0x30
MSG_STATUS = 0x32
MSG_BATCH = 0x40

# Flags
FLAG_ACK_REQUEST = 0x0001
FLAG_HAS_TIMESTAMP = 0x0002

# Capability Bits
CAP_ACK = 0x01
CAP_TIMESTAMP = 0x02
CAP_BATCH = 0x08
CAP_FEEDBACK = 0x10

# Control Codes - Gamepad Buttons (0x0001-0x0011)
CTRL_BTN_A = 0x0001
CTRL_BTN_B = 0x0002
CTRL_BTN_X = 0x0003
CTRL_BTN_Y = 0x0004
CTRL_BTN_L1 = 0x0005
CTRL_BTN_R1 = 0x0006
CTRL_BTN_L2 = 0x0007
CTRL_BTN_R2 = 0x0008
CTRL_BTN_DPAD_UP = 0x0009
CTRL_BTN_DPAD_DOWN = 0x000A
CTRL_BTN_DPAD_LEFT = 0x000B
CTRL_BTN_DPAD_RIGHT = 0x000C
CTRL_BTN_BACK = 0x000D
CTRL_BTN_START = 0x000E
CTRL_BTN_GUIDE = 0x000F
CTRL_BTN_L3 = 0x0010
CTRL_BTN_R3 = 0x0011

# Control Codes - Gamepad Axes (0x0101-0x0108)
CTRL_AXIS_LX = 0x0101
CTRL_AXIS_LY = 0x0102
CTRL_AXIS_RX = 0x0103
CTRL_AXIS_RY = 0x0104
CTRL_AXIS_LT = 0x0105
CTRL_AXIS_RT = 0x0106
CTRL_AXIS_DPAD_X = 0x0107
CTRL_AXIS_DPAD_Y = 0x0108

# Control Codes - Mouse (0x0201-0x0205)
CTRL_MOUSE_LEFT = 0x0201
CTRL_MOUSE_RIGHT = 0x0202
CTRL_MOUSE_MIDDLE = 0x0203
CTRL_MOUSE_SCROLL_X = 0x0204
CTRL_MOUSE_SCROLL_Y = 0x0205

# Map control codes to button/axis names
CONTROL_CODE_MAP = {
    # Gamepad Buttons
    CTRL_BTN_A: ("button", "a"),
    CTRL_BTN_B: ("button", "b"),
    CTRL_BTN_X: ("button", "x"),
    CTRL_BTN_Y: ("button", "y"),
    CTRL_BTN_L1: ("button", "l1"),
    CTRL_BTN_R1: ("button", "r1"),
    CTRL_BTN_L2: ("button", "l2_click"),
    CTRL_BTN_R2: ("button", "r2_click"),
    CTRL_BTN_DPAD_UP: ("button", "dpad_up"),
    CTRL_BTN_DPAD_DOWN: ("button", "dpad_down"),
    CTRL_BTN_DPAD_LEFT: ("button", "dpad_left"),
    CTRL_BTN_DPAD_RIGHT: ("button", "dpad_right"),
    CTRL_BTN_BACK: ("button", "back"),
    CTRL_BTN_START: ("button", "start"),
    CTRL_BTN_GUIDE: ("button", "guide"),
    CTRL_BTN_L3: ("button", "l3"),
    CTRL_BTN_R3: ("button", "r3"),
    # Gamepad Axes
    CTRL_AXIS_LX: ("axis", "lx"),
    CTRL_AXIS_LY: ("axis", "ly"),
    CTRL_AXIS_RX: ("axis", "rx"),
    CTRL_AXIS_RY: ("axis", "ry"),
    CTRL_AXIS_LT: ("axis", "lt"),
    CTRL_AXIS_RT: ("axis", "rt"),
    CTRL_AXIS_DPAD_X: ("axis", "dpad_x"),
    CTRL_AXIS_DPAD_Y: ("axis", "dpad_y"),
    # Mouse Buttons
    CTRL_MOUSE_LEFT: ("button", "left"),
    CTRL_MOUSE_RIGHT: ("button", "right"),
    CTRL_MOUSE_MIDDLE: ("button", "middle"),
}

# Protocol Version
PROTOCOL_VERSION = 1


# ============================================================================
# Data Classes
# ============================================================================

@dataclass
class Session:
    """Represents an active client session."""
    session_id: int
    client_addr: Tuple[str, int]
    device: Optional[BaseController] = None
    device_id: int = 0
    device_type: str = ""  # Track which device type is connected
    last_seen: float = 0.0
    caps: int = 0
    client_name: str = "Unknown"


# ============================================================================
# LibrePad UDP Protocol Handler
# ============================================================================

class LibrePadUDPProtocol(asyncio.DatagramProtocol):
    """Implements LibrePad UDP Control Protocol v0.3"""
    
    def __init__(self):
        self.transport = None
        self.sessions: Dict[int, Session] = {}
        self.addr_to_session: Dict[Tuple[str, int], int] = {}
        self.next_session_id = 1000
        self.device_registry = None
        
    def set_device_registry(self, registry):
        """Set the device registry for controller management."""
        self.device_registry = registry
        
    def connection_made(self, transport):
        """Called when protocol is started."""
        self.transport = transport
        logger.info("LibrePad UDP server ready")
        
    def datagram_received(self, data: bytes, addr: Tuple[str, int]):
        """Handle incoming UDP datagram."""
        try:
            if len(data) < 12:  # Minimum header size
                logger.warning("Packet too small from %s", addr)
                return
            
            # Parse common header
            version = data[0]
            msg_type = data[1]
            flags = struct.unpack('<H', data[2:4])[0]
            session_id = struct.unpack('<I', data[4:8])[0]
            seq = struct.unpack('<I', data[8:12])[0]
            
            if version != PROTOCOL_VERSION:
                logger.warning("Unsupported protocol version %d from %s", version, addr)
                self._send_error(addr, 0, "UnsupportedVersion", "Protocol version not supported")
                return
            
            # Update session timestamp
            if addr in self.addr_to_session:
                self.sessions[self.addr_to_session[addr]].last_seen = time.time()
            
            # Parse extended header if present
            payload_offset = 12
            if flags & FLAG_HAS_TIMESTAMP:
                payload_offset = 20
            
            payload = data[payload_offset:]
            
            # Dispatch by message type
            self._dispatch_message(msg_type, payload, addr, session_id, seq, flags)
            
        except Exception as e:
            logger.error("Error processing datagram from %s: %s", addr, e, exc_info=True)
            self._send_error(addr, 0, "InternalError", str(e))
    
    def _dispatch_message(self, msg_type: int, payload: bytes, addr: Tuple[str, int], 
                         session_id: int, seq: int, flags: int):
        """Dispatch message to appropriate handler."""
        
        if msg_type == MSG_HELLO:
            self._handle_hello(payload, addr, seq)
        elif msg_type == MSG_PING:
            self._handle_ping(addr, session_id, seq, flags)
        elif msg_type == MSG_CONNECT:
            self._handle_connect(payload, addr, session_id, seq)
        elif msg_type == MSG_DISCONNECT:
            self._handle_disconnect(addr, session_id)
        elif msg_type == MSG_BUTTON:
            self._handle_button(payload, addr, session_id)
        elif msg_type == MSG_AXIS:
            self._handle_axis(payload, addr, session_id)
        elif msg_type == MSG_MOUSE_MOVE:
            self._handle_mouse_move(payload, addr, session_id)
        elif msg_type == MSG_MOUSE_BUTTON:
            self._handle_mouse_button(payload, addr, session_id)
        elif msg_type == MSG_MOUSE_SCROLL:
            self._handle_mouse_scroll(payload, addr, session_id)
        elif msg_type == MSG_BATCH:
            self._handle_batch(payload, addr, session_id)
        elif msg_type == MSG_SESSION_END:
            self._handle_session_end(addr, session_id)
        else:
            logger.warning("Unknown message type 0x%02x from %s", msg_type, addr)
            self._send_error(addr, session_id, "UnknownMessage", f"Message type 0x{msg_type:02x} not supported")
    
    # ========================================================================
    # Message Handlers
    # ========================================================================
    
    def _handle_hello(self, payload: bytes, addr: Tuple[str, int], seq: int):
        """Handle HELLO message - client initiates session."""
        try:
            # Parse: caps_len (u16) | caps_bits (u8[]) | name_len (u8) | client_name
            if len(payload) < 4:
                raise ValueError("Invalid HELLO payload")
            
            caps_len = struct.unpack('<H', payload[0:2])[0]
            if len(payload) < 2 + caps_len + 1:
                raise ValueError("Invalid HELLO payload length")
            
            caps_bits = payload[2:2+caps_len] if caps_len > 0 else b'\x00'
            caps = caps_bits[0] if caps_bits else 0
            
            offset = 2 + caps_len
            name_len = payload[offset]
            if len(payload) < offset + 1 + name_len:
                raise ValueError("Invalid HELLO client name length")
            
            client_name = payload[offset+1:offset+1+name_len].decode('utf-8')
            
            # Create session
            session_id = self.next_session_id
            self.next_session_id += 1
            
            session = Session(
                session_id=session_id,
                client_addr=addr,
                last_seen=time.time(),
                caps=caps,
                client_name=client_name
            )
            
            self.sessions[session_id] = session
            self.addr_to_session[addr] = session_id
            
            logger.info("New session %d from %s (%s) - caps=0x%02x", 
                       session_id, addr, client_name, caps)
            
            # Send WELCOME
            self._send_welcome(addr, session_id, seq)
            
        except Exception as e:
            logger.error("HELLO error: %s", e)
            self._send_error(addr, 0, "InvalidMessage", str(e))
    
    def _handle_ping(self, addr: Tuple[str, int], session_id: int, seq: int, flags: int):
        """Handle PING message - respond with PONG."""
        self._send_pong(addr, session_id, seq, flags)
    
    def _handle_connect(self, payload: bytes, addr: Tuple[str, int], session_id: int, seq: int):
        """Handle CONNECT message - client acquires device."""
        try:
            if session_id not in self.sessions:
                raise ValueError("Unknown session")
            
            session = self.sessions[session_id]
            
            # Parse: type_len (u8) | device_type | name_len (u8) | display_name
            if len(payload) < 2:
                raise ValueError("Invalid CONNECT payload")
            
            type_len = payload[0]
            if len(payload) < 1 + type_len + 1:
                raise ValueError("Invalid CONNECT payload")
            
            device_type = payload[1:1+type_len].decode('utf-8')
            
            offset = 1 + type_len
            name_len = payload[offset]
            display_name = payload[offset+1:offset+1+name_len].decode('utf-8') if name_len > 0 else device_type
            
            # Schedule async acquire in the event loop
            asyncio.create_task(self._async_connect_device(session, device_type, display_name, addr))
            
            logger.info("Session %d connecting to %s (%s)", session_id, device_type, display_name)
            
        except Exception as e:
            logger.error("CONNECT error: %s", e)
            self._send_error(addr, session_id, "ConnectFailed", str(e))
    
    async def _async_connect_device(self, session: Session, device_type: str, display_name: str, addr: Tuple[str, int]):
        """Async handler to acquire device from registry."""
        try:
            if not self.device_registry:
                raise ValueError("Device registry not available")
            
            device = await self.device_registry.acquire(device_type, display_name=display_name)
            session.device = device
            session.device_type = device_type  # Store device type for cleanup
            session.device_id = 0  # First device
            
            logger.info("Session %d connected to %s (%s)", session.session_id, device_type, display_name)
            
            # Send STATUS
            self._send_status(addr, session.session_id, 0x0001, "device connected")
            
        except Exception as e:
            logger.error("Device acquisition error: %s", e)
            self._send_error(addr, session.session_id, "ConnectFailed", str(e))
    
    def _handle_disconnect(self, addr: Tuple[str, int], session_id: int):
        """Handle DISCONNECT message - client releases device."""
        try:
            if session_id not in self.sessions:
                return
            
            session = self.sessions[session_id]
            
            if session.device and self.device_registry and session.device_type:
                # Schedule async release - use the actual device type that was connected
                asyncio.create_task(self.device_registry.release(session.device_type))
                session.device = None
            
            logger.info("Session %d disconnected", session_id)
            
        except Exception as e:
            logger.error("DISCONNECT error: %s", e)
    
    def _handle_button(self, payload: bytes, addr: Tuple[str, int], session_id: int):
        """Handle BUTTON message - digital input."""
        try:
            if session_id not in self.sessions:
                raise ValueError("Unknown session")
            
            session = self.sessions[session_id]
            if not session.device:
                raise ValueError("No device connected")
            
            # Parse: device_id (u16) | control_code (u16) | pressed (u8)
            if len(payload) < 5:
                raise ValueError("Invalid BUTTON payload")
            
            device_id = struct.unpack('<H', payload[0:2])[0]
            control_code = struct.unpack('<H', payload[2:4])[0]
            pressed = bool(payload[4])
            
            # Map control code to button name
            if control_code not in CONTROL_CODE_MAP:
                logger.warning("Unknown control code 0x%04x", control_code)
                return
            
            ctrl_type, ctrl_name = CONTROL_CODE_MAP[control_code]
            if ctrl_type != "button":
                logger.warning("Control code 0x%04x is not a button", control_code)
                return
            
            session.device.set_button(ctrl_name, pressed)
            
        except Exception as e:
            logger.error("BUTTON error: %s", e)
    
    def _handle_axis(self, payload: bytes, addr: Tuple[str, int], session_id: int):
        """Handle AXIS message - analog input."""
        try:
            if session_id not in self.sessions:
                raise ValueError("Unknown session")
            
            session = self.sessions[session_id]
            if not session.device:
                raise ValueError("No device connected")
            
            # Parse: device_id (u16) | control_code (u16) | value (i16)
            if len(payload) < 6:
                raise ValueError("Invalid AXIS payload")
            
            device_id = struct.unpack('<H', payload[0:2])[0]
            control_code = struct.unpack('<H', payload[2:4])[0]
            value = struct.unpack('<h', payload[4:6])[0]  # i16
            
            # Normalize i16 to float [-1.0, 1.0]
            value_float = max(-1.0, min(1.0, value / 32767.0))
            
            # Map control code to axis name
            if control_code not in CONTROL_CODE_MAP:
                logger.warning("Unknown control code 0x%04x", control_code)
                return
            
            ctrl_type, ctrl_name = CONTROL_CODE_MAP[control_code]
            if ctrl_type != "axis":
                logger.warning("Control code 0x%04x is not an axis", control_code)
                return
            
            session.device.set_axis(ctrl_name, value_float)
            
        except Exception as e:
            logger.error("AXIS error: %s", e)
    
    def _handle_mouse_move(self, payload: bytes, addr: Tuple[str, int], session_id: int):
        """Handle MOUSE_MOVE message - relative mouse movement."""
        try:
            if session_id not in self.sessions:
                raise ValueError("Unknown session")
            
            session = self.sessions[session_id]
            if not session.device:
                raise ValueError("No device connected")
            
            # Parse: dx (i16) | dy (i16)
            if len(payload) < 4:
                raise ValueError("Invalid MOUSE_MOVE payload")
            
            dx = struct.unpack('<h', payload[0:2])[0]
            dy = struct.unpack('<h', payload[2:4])[0]
            
            # Check if device has move_relative method (mouse controller)
            if hasattr(session.device, 'move_relative'):
                session.device.move_relative(dx, dy)
            elif hasattr(session.device, 'set_axis'):
                # Fallback to set_axis for compatibility
                if dx != 0:
                    session.device.set_axis("dx", float(dx))
                if dy != 0:
                    session.device.set_axis("dy", float(dy))
            
            logger.debug("Mouse move: dx=%d, dy=%d", dx, dy)
            
        except Exception as e:
            logger.error("MOUSE_MOVE error: %s", e)
    
    def _handle_mouse_button(self, payload: bytes, addr: Tuple[str, int], session_id: int):
        """Handle MOUSE_BUTTON message - mouse button press."""
        try:
            if session_id not in self.sessions:
                raise ValueError("Unknown session")
            
            session = self.sessions[session_id]
            if not session.device:
                raise ValueError("No device connected")
            
            # Parse: control_code (u16) | pressed (u8)
            if len(payload) < 3:
                raise ValueError("Invalid MOUSE_BUTTON payload")
            
            control_code = struct.unpack('<H', payload[0:2])[0]
            pressed = bool(payload[2])
            
            # Map control code to button name
            if control_code not in CONTROL_CODE_MAP:
                logger.warning("Unknown control code 0x%04x", control_code)
                return
            
            ctrl_type, ctrl_name = CONTROL_CODE_MAP[control_code]
            if ctrl_type != "button":
                logger.warning("Control code 0x%04x is not a button", control_code)
                return
            
            session.device.set_button(ctrl_name, pressed)
            logger.debug("Mouse button: %s %s", ctrl_name, "pressed" if pressed else "released")
            
        except Exception as e:
            logger.error("MOUSE_BUTTON error: %s", e)
    
    def _handle_mouse_scroll(self, payload: bytes, addr: Tuple[str, int], session_id: int):
        """Handle MOUSE_SCROLL message - mouse wheel scroll."""
        try:
            if session_id not in self.sessions:
                raise ValueError("Unknown session")
            
            session = self.sessions[session_id]
            if not session.device:
                raise ValueError("No device connected")
            
            # Parse: scroll_x (i16) | scroll_y (i16)
            if len(payload) < 4:
                raise ValueError("Invalid MOUSE_SCROLL payload")
            
            scroll_x = struct.unpack('<h', payload[0:2])[0]
            scroll_y = struct.unpack('<h', payload[2:4])[0]
            
            # Check if device has scroll method (mouse controller)
            if hasattr(session.device, 'scroll'):
                # Y scroll is more common, X is horizontal
                if scroll_y != 0:
                    session.device.scroll(scroll_y)
                if scroll_x != 0 and hasattr(session.device, 'set_axis'):
                    session.device.set_axis("hwheel", float(scroll_x))
            elif hasattr(session.device, 'set_axis'):
                # Fallback to set_axis
                if scroll_y != 0:
                    session.device.set_axis("wheel", float(scroll_y))
                if scroll_x != 0:
                    session.device.set_axis("hwheel", float(scroll_x))
            
            logger.debug("Mouse scroll: scroll_x=%d, scroll_y=%d", scroll_x, scroll_y)
            
        except Exception as e:
            logger.error("MOUSE_SCROLL error: %s", e)
    
    def _handle_batch(self, payload: bytes, addr: Tuple[str, int], session_id: int):
        """Handle BATCH message - multiple events in one packet.
        
        Format: event_count (u8) | [events...]
        
        Events in payload are encoded as:
        - BUTTON: device_id(u16) | control_code(u16) | pressed(u8)
        - AXIS: device_id(u16) | control_code(u16) | value(i16)
        - MOUSE_MOVE: dx(i16) | dy(i16)
        - MOUSE_BUTTON: control_code(u16) | pressed(u8)
        - MOUSE_SCROLL: scroll_x(i16) | scroll_y(i16)
        
        We deduce event type by size heuristics and try to parse intelligently.
        """
        try:
            if session_id not in self.sessions:
                raise ValueError("Unknown session")
            
            if len(payload) < 1:
                raise ValueError("Invalid BATCH payload")
            
            event_count = payload[0]
            offset = 1
            events_processed = 0
            
            # Parse events sequentially
            # Since we don't have explicit type markers in the batch format,
            # we need intelligent parsing. Most common sequence:
            # - BUTTON/AXIS (5-6 bytes each)
            # - MOUSE_MOVE (4 bytes)
            # - MOUSE_BUTTON (3 bytes)
            # - MOUSE_SCROLL (4 bytes)
            
            for i in range(event_count):
                if offset >= len(payload):
                    logger.warning("Batch payload truncated at event %d/%d", i, event_count)
                    break
                
                # Try to parse an event - use heuristics based on remaining bytes
                event_parsed = False
                
                # Try BUTTON (5 bytes: dev_id(2) + code(2) + pressed(1))
                if offset + 5 <= len(payload):
                    try:
                        device_id = struct.unpack('<H', payload[offset:offset+2])[0]
                        control_code = struct.unpack('<H', payload[offset+2:offset+4])[0]
                        pressed = bool(payload[offset+4])
                        
                        # Check if this looks like a valid button code
                        if control_code in CONTROL_CODE_MAP:
                            ctrl_type, _ = CONTROL_CODE_MAP[control_code]
                            if ctrl_type == "button":
                                # It's a BUTTON event
                                button_payload = payload[offset:offset+5]
                                self._handle_button(button_payload, addr, session_id)
                                offset += 5
                                events_processed += 1
                                event_parsed = True
                    except:
                        pass
                
                # Try AXIS (6 bytes: dev_id(2) + code(2) + value(2))
                if not event_parsed and offset + 6 <= len(payload):
                    try:
                        device_id = struct.unpack('<H', payload[offset:offset+2])[0]
                        control_code = struct.unpack('<H', payload[offset+2:offset+4])[0]
                        value = struct.unpack('<h', payload[offset+4:offset+6])[0]
                        
                        # Check if this looks like a valid axis code
                        if control_code in CONTROL_CODE_MAP:
                            ctrl_type, _ = CONTROL_CODE_MAP[control_code]
                            if ctrl_type == "axis":
                                # It's an AXIS event
                                axis_payload = payload[offset:offset+6]
                                self._handle_axis(axis_payload, addr, session_id)
                                offset += 6
                                events_processed += 1
                                event_parsed = True
                    except:
                        pass
                
                # Try MOUSE_MOVE (4 bytes: dx(2) + dy(2))
                if not event_parsed and offset + 4 <= len(payload):
                    try:
                        # Check if next two i16 values look like reasonable mouse deltas
                        dx = struct.unpack('<h', payload[offset:offset+2])[0]
                        dy = struct.unpack('<h', payload[offset+2:offset+4])[0]
                        
                        # Accept if both values are within reasonable mouse range (-1000 to 1000)
                        if abs(dx) <= 1000 and abs(dy) <= 1000:
                            mouse_move_payload = payload[offset:offset+4]
                            self._handle_mouse_move(mouse_move_payload, addr, session_id)
                            offset += 4
                            events_processed += 1
                            event_parsed = True
                    except:
                        pass
                
                # Try MOUSE_BUTTON (3 bytes: control_code(2) + pressed(1))
                if not event_parsed and offset + 3 <= len(payload):
                    try:
                        control_code = struct.unpack('<H', payload[offset:offset+2])[0]
                        pressed = bool(payload[offset+2])
                        
                        # Check if this is a mouse button code
                        if control_code in (CTRL_MOUSE_LEFT, CTRL_MOUSE_RIGHT, CTRL_MOUSE_MIDDLE):
                            mouse_button_payload = payload[offset:offset+3]
                            self._handle_mouse_button(mouse_button_payload, addr, session_id)
                            offset += 3
                            events_processed += 1
                            event_parsed = True
                    except:
                        pass
                
                # Try MOUSE_SCROLL (4 bytes: scroll_x(2) + scroll_y(2))
                if not event_parsed and offset + 4 <= len(payload):
                    try:
                        scroll_x = struct.unpack('<h', payload[offset:offset+2])[0]
                        scroll_y = struct.unpack('<h', payload[offset+2:offset+4])[0]
                        
                        # Accept if at least one is non-zero and in reasonable range
                        if (scroll_x != 0 or scroll_y != 0) and abs(scroll_x) <= 100 and abs(scroll_y) <= 100:
                            scroll_payload = payload[offset:offset+4]
                            self._handle_mouse_scroll(scroll_payload, addr, session_id)
                            offset += 4
                            events_processed += 1
                            event_parsed = True
                    except:
                        pass
                
                # If we couldn't parse any event, skip a byte and try again
                if not event_parsed:
                    logger.warning("Could not parse batched event %d at offset %d", i, offset)
                    offset += 1
            
            logger.debug("Processed %d/%d batched events (payload %d bytes)", 
                        events_processed, event_count, len(payload))
            
        except Exception as e:
            logger.error("BATCH error: %s", e)
    
    def _handle_session_end(self, addr: Tuple[str, int], session_id: int):
        """Handle SESSION_END message - client closes session."""
        try:
            if session_id not in self.sessions:
                return
            
            session = self.sessions[session_id]
            
            # Release device - use the actual device type that was connected
            if session.device and self.device_registry and session.device_type:
                asyncio.create_task(self.device_registry.release(session.device_type))
            
            # Clean up session
            del self.sessions[session_id]
            if addr in self.addr_to_session:
                del self.addr_to_session[addr]
            
            logger.info("Session %d ended", session_id)
            
        except Exception as e:
            logger.error("SESSION_END error: %s", e)
    
    # ========================================================================
    # Response Senders
    # ========================================================================
    
    def _send_welcome(self, addr: Tuple[str, int], session_id: int, seq: int):
        """Send WELCOME message."""
        try:
            # Build payload: session_id (u32) | caps_len | accepted_caps | dev_count | devices[]
            payload = struct.pack('<I', session_id)
            
            # Accepted capabilities
            accepted_caps = CAP_ACK | CAP_TIMESTAMP | CAP_BATCH
            payload += struct.pack('<H', 1)  # caps_len
            payload += bytes([accepted_caps])
            
            # Available devices
            payload += bytes([1])  # dev_count = 1 (standard gamepad)
            
            # Device: type_len | device_type | device_id
            device_type = b"standard"
            payload += bytes([len(device_type)])
            payload += device_type
            payload += struct.pack('<H', 0)  # device_id = 0
            
            self._send_message(addr, MSG_WELCOME, payload, session_id, seq)
            
        except Exception as e:
            logger.error("Error sending WELCOME: %s", e)
    
    def _send_pong(self, addr: Tuple[str, int], session_id: int, seq: int, flags: int):
        """Send PONG message."""
        try:
            payload = b""
            # If PING had timestamp, echo it back (would be in extended header)
            # For now, send minimal PONG
            self._send_message(addr, MSG_PONG, payload, session_id, seq, flags)
            
        except Exception as e:
            logger.error("Error sending PONG: %s", e)
    
    def _send_status(self, addr: Tuple[str, int], session_id: int, status_code: int, message: str):
        """Send STATUS message."""
        try:
            # Payload: status_code (u16) | msg_len (u8) | message
            payload = struct.pack('<H', status_code)
            msg_bytes = message.encode('utf-8')
            payload += bytes([len(msg_bytes)])
            payload += msg_bytes
            
            self._send_message(addr, MSG_STATUS, payload, session_id, 0)
            
        except Exception as e:
            logger.error("Error sending STATUS: %s", e)
    
    def _send_error(self, addr: Tuple[str, int], session_id: int, error_type: str, message: str):
        """Send ERROR message."""
        try:
            # Payload: code (u16) | msg_len (u8) | message
            error_codes = {
                "InvalidMessage": 0x0001,
                "UnknownDevice": 0x0002,
                "NotConnected": 0x0003,
                "ConnectFailed": 0x0001,
                "UnsupportedVersion": 0x0001,
                "UnknownMessage": 0x0001,
                "InternalError": 0x0005,
            }
            
            code = error_codes.get(error_type, 0x0005)
            payload = struct.pack('<H', code)
            msg_bytes = message.encode('utf-8')
            payload += bytes([len(msg_bytes)])
            payload += msg_bytes
            
            self._send_message(addr, MSG_ERROR, payload, session_id, 0)
            
        except Exception as e:
            logger.error("Error sending ERROR: %s", e)
    
    def _send_message(self, addr: Tuple[str, int], msg_type: int, payload: bytes, 
                     session_id: int, seq: int, flags: int = 0):
        """Send a message with common header."""
        try:
            # Common header: version | msg_type | flags | session_id | seq
            header = struct.pack('<BBHII',
                                PROTOCOL_VERSION,
                                msg_type,
                                flags,
                                session_id,
                                seq)
            
            packet = header + payload
            self.transport.sendto(packet, addr)
            
        except Exception as e:
            logger.error("Error sending message: %s", e)


class LibrePadUDPServer:
    """LibrePad UDP Control Server"""
    
    def __init__(self, host: str = "0.0.0.0", port: int = 9775):
        self.host = host
        self.port = port
        self.device_registry = None
    
    def set_device_registry(self, registry):
        """Set the device registry."""
        self.device_registry = registry
    
    async def start(self):
        """Start the UDP server."""
        logger.info("Starting LibrePad UDP server on %s:%d", self.host, self.port)
        
        loop = asyncio.get_event_loop()
        
        # Create UDP endpoint
        transport, protocol = await loop.create_datagram_endpoint(
            LibrePadUDPProtocol,
            local_addr=(self.host, self.port)
        )
        
        # Set device registry on protocol
        if self.device_registry:
            protocol.set_device_registry(self.device_registry)
        
        logger.info("LibrePad UDP server listening on %s:%d", self.host, self.port)
        
        try:
            await asyncio.Future()  # Run forever
        finally:
            transport.close()


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Simple test - requires device registry
    server = LibrePadUDPServer()
    asyncio.run(server.start())
