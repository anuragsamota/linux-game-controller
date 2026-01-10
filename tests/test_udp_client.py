#!/usr/bin/env python3
"""
Test client for LibrePad UDP protocol (v0.3)

Tests basic session establishment (HELLO/WELCOME) and input events (BUTTON/AXIS).
"""

import asyncio
import struct
import logging
from typing import Tuple

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# Message Types (from protocol spec)
MSG_HELLO = 0x01
MSG_WELCOME = 0x02
MSG_PING = 0x03
MSG_PONG = 0x04
MSG_CONNECT = 0x10
MSG_DISCONNECT = 0x11
MSG_BUTTON = 0x20
MSG_AXIS = 0x21
MSG_MOUSE_MOVE = 0x22
MSG_MOUSE_BUTTON = 0x23
MSG_MOUSE_SCROLL = 0x26
MSG_ERROR = 0x30
MSG_STATUS = 0x32
MSG_BATCH = 0x40

# Control Codes - All Gamepad Buttons
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

# Control Codes - All Gamepad Axes
CTRL_AXIS_LX = 0x0101
CTRL_AXIS_LY = 0x0102
CTRL_AXIS_RX = 0x0103
CTRL_AXIS_RY = 0x0104
CTRL_AXIS_LT = 0x0105
CTRL_AXIS_RT = 0x0106
CTRL_AXIS_DPAD_X = 0x0107
CTRL_AXIS_DPAD_Y = 0x0108

# Mouse Control Codes
CTRL_MOUSE_LEFT = 0x0201
CTRL_MOUSE_RIGHT = 0x0202
CTRL_MOUSE_MIDDLE = 0x0203

PROTOCOL_VERSION = 1


class LibrePadUDPClient:
    """Test client for LibrePad UDP protocol."""
    
    def __init__(self, host: str = "127.0.0.1", port: int = 9775):
        self.host = host
        self.port = port
        self.transport = None
        self.protocol = None
        self.session_id = 0
        self.device_id = 0
        self.seq = 0
        
    async def connect(self):
        """Connect to server and establish session."""
        loop = asyncio.get_event_loop()
        
        # Create UDP socket
        self.transport, self.protocol = await loop.create_datagram_endpoint(
            lambda: _TestProtocol(self),
            remote_addr=(self.host, self.port)
        )
        
        logger.info("Connected to %s:%d", self.host, self.port)
        
    def send_raw(self, msg_type: int, payload: bytes = b''):
        """Send raw message with common header."""
        # Common header: version | msg_type | flags | session_id | seq
        header = struct.pack('<BBHII',
                           PROTOCOL_VERSION,
                           msg_type,
                           0,  # flags
                           self.session_id,
                           self.seq)
        
        self.seq += 1
        self.transport.sendto(header + payload)
        
    def send_hello(self, client_name: str = "TestClient"):
        """Send HELLO message to initiate session."""
        # Payload: caps_len (u16) | caps_bits (u8[]) | name_len (u8) | client_name
        payload = struct.pack('<H', 1)  # caps_len = 1
        payload += bytes([0x01])  # caps_bits = CAP_ACK
        
        name_bytes = client_name.encode('utf-8')
        payload += bytes([len(name_bytes)])
        payload += name_bytes
        
        logger.info("Sending HELLO (client_name='%s')", client_name)
        self.send_raw(MSG_HELLO, payload)
        
    def send_ping(self):
        """Send PING message."""
        logger.info("Sending PING")
        self.send_raw(MSG_PING, b'')
        
    def send_connect(self, device_type: str = "standard"):
        """Send CONNECT message to acquire device."""
        # Payload: type_len (u8) | device_type | name_len (u8) | display_name
        device_bytes = device_type.encode('utf-8')
        payload = bytes([len(device_bytes)])
        payload += device_bytes
        
        display_name = f"Test {device_type}".encode('utf-8')
        payload += bytes([len(display_name)])
        payload += display_name
        
        logger.info("Sending CONNECT (%s)", device_type)
        self.send_raw(MSG_CONNECT, payload)
        
    def send_button(self, control_code: int, pressed: bool, device_id: int = 0):
        """Send BUTTON message - digital input."""
        # Payload: device_id (u16) | control_code (u16) | pressed (u8)
        payload = struct.pack('<HHB',
                            device_id,
                            control_code,
                            1 if pressed else 0)
        
        logger.info("Sending BUTTON (code=0x%04x, pressed=%s)", control_code, pressed)
        self.send_raw(MSG_BUTTON, payload)
        
    def send_axis(self, control_code: int, value: float, device_id: int = 0):
        """Send AXIS message - analog input."""
        # Payload: device_id (u16) | control_code (u16) | value (i16)
        # Normalize float to i16 [-1.0, 1.0] -> [-32767, 32767]
        i16_value = int(value * 32767)
        i16_value = max(-32767, min(32767, i16_value))
        
        payload = struct.pack('<HHh',
                            device_id,
                            control_code,
                            i16_value)
        
        logger.info("Sending AXIS (code=0x%04x, value=%.2f)", control_code, value)
        self.send_raw(MSG_AXIS, payload)
    
    def send_mouse_move(self, dx: int, dy: int):
        """Send MOUSE_MOVE message - relative mouse movement."""
        # Payload: dx (i16) | dy (i16)
        payload = struct.pack('<hh', dx, dy)
        logger.info("Sending MOUSE_MOVE (dx=%d, dy=%d)", dx, dy)
        self.send_raw(MSG_MOUSE_MOVE, payload)
    
    def send_mouse_button(self, control_code: int, pressed: bool):
        """Send MOUSE_BUTTON message - mouse button press."""
        # Payload: control_code (u16) | pressed (u8)
        payload = struct.pack('<HB', control_code, 1 if pressed else 0)
        logger.info("Sending MOUSE_BUTTON (code=0x%04x, pressed=%s)", control_code, pressed)
        self.send_raw(MSG_MOUSE_BUTTON, payload)
    
    def send_mouse_scroll(self, scroll_x: int, scroll_y: int):
        """Send MOUSE_SCROLL message - mouse wheel scroll."""
        # Payload: scroll_x (i16) | scroll_y (i16)
        payload = struct.pack('<hh', scroll_x, scroll_y)
        logger.info("Sending MOUSE_SCROLL (scroll_x=%d, scroll_y=%d)", scroll_x, scroll_y)
        self.send_raw(MSG_MOUSE_SCROLL, payload)
    
    def send_batch(self, events: list):
        """Send BATCH message - multiple events in one packet.
        
        Each event is a tuple: (event_type, payload_bytes)
        where event_type is one of MSG_BUTTON, MSG_AXIS, MSG_MOUSE_MOVE, etc.
        and payload_bytes is the event-specific payload (without header).
        """
        # Build batch payload: event_count (u8) | [events...]
        batch_payload = bytes([len(events)])  # event_count
        
        for event_type, event_payload in events:
            batch_payload += event_payload
        
        logger.info("Sending BATCH with %d events (total %d bytes)", len(events), len(batch_payload))
        self.send_raw(MSG_BATCH, batch_payload)
        
    def batch_button(self, control_code: int, pressed: bool, device_id: int = 0) -> tuple:
        """Create a batched BUTTON event tuple."""
        # Format: device_id (u16) | control_code (u16) | pressed (u8)
        payload = struct.pack('<HHB', device_id, control_code, 1 if pressed else 0)
        return (MSG_BUTTON, payload)
    
    def batch_axis(self, control_code: int, value: float, device_id: int = 0) -> tuple:
        """Create a batched AXIS event tuple."""
        # Format: device_id (u16) | control_code (u16) | value (i16)
        i16_value = int(value * 32767)
        i16_value = max(-32767, min(32767, i16_value))
        payload = struct.pack('<HHh', device_id, control_code, i16_value)
        return (MSG_AXIS, payload)
    
    def batch_mouse_move(self, dx: int, dy: int) -> tuple:
        """Create a batched MOUSE_MOVE event tuple."""
        # Format: dx (i16) | dy (i16)
        payload = struct.pack('<hh', dx, dy)
        return (MSG_MOUSE_MOVE, payload)
    
    def batch_mouse_button(self, control_code: int, pressed: bool) -> tuple:
        """Create a batched MOUSE_BUTTON event tuple."""
        # Format: control_code (u16) | pressed (u8)
        payload = struct.pack('<HB', control_code, 1 if pressed else 0)
        return (MSG_MOUSE_BUTTON, payload)
    
    def batch_mouse_scroll(self, scroll_x: int, scroll_y: int) -> tuple:
        """Create a batched MOUSE_SCROLL event tuple."""
        # Format: scroll_x (i16) | scroll_y (i16)
        payload = struct.pack('<hh', scroll_x, scroll_y)
        return (MSG_MOUSE_SCROLL, payload)
        
    def handle_message(self, data: bytes, addr: Tuple[str, int]):
        """Handle incoming message from server."""
        try:
            if len(data) < 12:
                logger.warning("Packet too small: %d bytes", len(data))
                return
            
            # Parse common header
            version = data[0]
            msg_type = data[1]
            flags = struct.unpack('<H', data[2:4])[0]
            session_id = struct.unpack('<I', data[4:8])[0]
            seq = struct.unpack('<I', data[8:12])[0]
            
            payload = data[12:]
            
            logger.info("Received message: type=0x%02x, session_id=%d, seq=%d", 
                       msg_type, session_id, seq)
            
            if msg_type == MSG_WELCOME:
                self._handle_welcome(payload, session_id)
            elif msg_type == MSG_PONG:
                logger.info("Received PONG")
            elif msg_type == MSG_STATUS:
                self._handle_status(payload)
            elif msg_type == MSG_ERROR:
                self._handle_error(payload)
            else:
                logger.warning("Unexpected message type: 0x%02x", msg_type)
                
        except Exception as e:
            logger.error("Error handling message: %s", e, exc_info=True)
    
    def _handle_welcome(self, payload: bytes, session_id: int):
        """Parse WELCOME message."""
        try:
            # Payload: session_id (u32) | caps_len | accepted_caps | dev_count | devices[]
            if len(payload) < 7:
                raise ValueError("Invalid WELCOME payload")
            
            received_session_id = struct.unpack('<I', payload[0:4])[0]
            self.session_id = received_session_id
            
            caps_len = struct.unpack('<H', payload[4:6])[0]
            offset = 6
            
            if caps_len > 0:
                accepted_caps = payload[offset]
                offset += caps_len
            
            dev_count = payload[offset]
            offset += 1
            
            logger.info("WELCOME: session_id=%d, devices=%d", received_session_id, dev_count)
            
            # Parse devices
            for i in range(dev_count):
                if offset >= len(payload):
                    break
                
                type_len = payload[offset]
                offset += 1
                
                device_type = payload[offset:offset+type_len].decode('utf-8')
                offset += type_len
                
                device_id = struct.unpack('<H', payload[offset:offset+2])[0]
                offset += 2
                
                logger.info("  Device %d: type='%s', device_id=%d", i, device_type, device_id)
                
                if device_type == "standard":
                    self.device_id = device_id
                    
        except Exception as e:
            logger.error("Error parsing WELCOME: %s", e)
    
    def _handle_status(self, payload: bytes):
        """Parse STATUS message."""
        try:
            status_code = struct.unpack('<H', payload[0:2])[0]
            msg_len = payload[2]
            message = payload[3:3+msg_len].decode('utf-8') if msg_len > 0 else ""
            
            logger.info("STATUS: code=0x%04x, message='%s'", status_code, message)
            
        except Exception as e:
            logger.error("Error parsing STATUS: %s", e)
    
    def _handle_error(self, payload: bytes):
        """Parse ERROR message."""
        try:
            code = struct.unpack('<H', payload[0:2])[0]
            msg_len = payload[2]
            message = payload[3:3+msg_len].decode('utf-8') if msg_len > 0 else ""
            
            logger.error("ERROR: code=0x%04x, message='%s'", code, message)
            
        except Exception as e:
            logger.error("Error parsing ERROR: %s", e)
    
    def send_disconnect(self):
        """Send DISCONNECT message to release device and end session."""
        # DISCONNECT message has no payload, just the common header
        logger.info("Sending DISCONNECT (session_id=%d)", self.session_id)
        self.send_raw(MSG_DISCONNECT, b'')
    
    def close(self):
        """Close connection."""
        if self.transport:
            self.transport.close()


class _TestProtocol(asyncio.DatagramProtocol):
    """UDP protocol for test client."""
    
    def __init__(self, client):
        self.client = client
    
    def datagram_received(self, data: bytes, addr: Tuple[str, int]):
        self.client.handle_message(data, addr)


async def test_basic_session():
    """Test basic session establishment."""
    logger.info("=== Test: Basic Session ===")
    
    client = LibrePadUDPClient()
    await client.connect()
    
    # Send HELLO
    client.send_hello("TestClient")
    await asyncio.sleep(0.5)
    
    # Send PING
    client.send_ping()
    await asyncio.sleep(0.5)
    
    # Clean up session
    client.send_disconnect()
    await asyncio.sleep(0.2)
    client.close()


async def test_gamepad_input():
    """Test gamepad input (buttons and axes)."""
    logger.info("=== Test: Gamepad Input ===")
    
    client = LibrePadUDPClient()
    await client.connect()
    
    # Establish session
    client.send_hello("GamepadTest")
    await asyncio.sleep(0.5)
    
    # Connect to device
    client.send_connect("standard")
    await asyncio.sleep(0.5)
    
    # Send button presses
    for button_code in [CTRL_BTN_A, CTRL_BTN_B, CTRL_BTN_X, CTRL_BTN_Y]:
        client.send_button(button_code, True)  # Press
        await asyncio.sleep(0.1)
        client.send_button(button_code, False)  # Release
        await asyncio.sleep(0.1)
    
    # Send axis values (left stick)
    client.send_axis(CTRL_AXIS_LX, 0.5)  # Move right
    await asyncio.sleep(0.1)
    client.send_axis(CTRL_AXIS_LY, -0.5)  # Move up
    await asyncio.sleep(0.1)
    
    # Send axis values (right stick)
    client.send_axis(CTRL_AXIS_RX, 1.0)  # Full right
    await asyncio.sleep(0.1)
    client.send_axis(CTRL_AXIS_RY, -1.0)  # Full up
    await asyncio.sleep(0.1)
    
    # Center sticks
    client.send_axis(CTRL_AXIS_LX, 0.0)
    client.send_axis(CTRL_AXIS_LY, 0.0)
    client.send_axis(CTRL_AXIS_RX, 0.0)
    client.send_axis(CTRL_AXIS_RY, 0.0)
    await asyncio.sleep(0.5)
    
    # Clean up session
    client.send_disconnect()
    await asyncio.sleep(0.2)
    client.close()


async def test_mouse_input():
    """Test mouse input (movement, buttons, scroll)."""
    logger.info("=== Test: Mouse Input ===")
    
    client = LibrePadUDPClient()
    await client.connect()
    
    # Establish session
    client.send_hello("MouseTest")
    await asyncio.sleep(0.5)
    
    # Connect to mouse device
    client.send_connect("mouse")
    await asyncio.sleep(0.5)
    
    # Send mouse movements
    logger.info("Moving mouse...")
    client.send_mouse_move(100, 50)    # Move right and down
    await asyncio.sleep(0.1)
    client.send_mouse_move(-50, -25)   # Move left and up
    await asyncio.sleep(0.1)
    client.send_mouse_move(0, 0)       # Stop
    await asyncio.sleep(0.2)
    
    # Send mouse button presses
    logger.info("Testing mouse buttons...")
    client.send_mouse_button(CTRL_MOUSE_LEFT, True)    # Left click
    await asyncio.sleep(0.1)
    client.send_mouse_button(CTRL_MOUSE_LEFT, False)   # Release
    await asyncio.sleep(0.1)
    
    client.send_mouse_button(CTRL_MOUSE_RIGHT, True)   # Right click
    await asyncio.sleep(0.1)
    client.send_mouse_button(CTRL_MOUSE_RIGHT, False)  # Release
    await asyncio.sleep(0.1)
    
    client.send_mouse_button(CTRL_MOUSE_MIDDLE, True)  # Middle click
    await asyncio.sleep(0.1)
    client.send_mouse_button(CTRL_MOUSE_MIDDLE, False) # Release
    await asyncio.sleep(0.2)
    
    # Send scroll wheel events
    logger.info("Testing mouse scroll...")
    client.send_mouse_scroll(0, 3)     # Scroll up
    await asyncio.sleep(0.1)
    client.send_mouse_scroll(0, -3)    # Scroll down
    await asyncio.sleep(0.1)
    client.send_mouse_scroll(2, 0)     # Scroll right
    await asyncio.sleep(0.1)
    client.send_mouse_scroll(-2, 0)    # Scroll left
    await asyncio.sleep(0.5)
    
    # Clean up session
    client.send_disconnect()
    await asyncio.sleep(0.2)
    client.close()


async def test_batching():
    """Test event batching for overhead reduction."""
    logger.info("=== Test: Event Batching ===")
    
    client = LibrePadUDPClient()
    await client.connect()
    
    # Establish session
    client.send_hello("BatchTest")
    await asyncio.sleep(0.5)
    
    # Connect to gamepad device
    client.send_connect("standard")
    await asyncio.sleep(0.5)
    
    # Send multiple events as unbatched
    logger.info("Sending unbatched events...")
    client.send_button(CTRL_BTN_A, True)
    await asyncio.sleep(0.05)
    client.send_button(CTRL_BTN_A, False)
    await asyncio.sleep(0.05)
    client.send_axis(CTRL_AXIS_LX, 0.5)
    await asyncio.sleep(0.05)
    client.send_axis(CTRL_AXIS_LY, -0.5)
    await asyncio.sleep(0.2)
    
    # Send same events as a batch (simulates client-side batching)
    logger.info("Sending same events batched (50% packet overhead reduction)...")
    events = [
        client.batch_button(CTRL_BTN_B, True),
        client.batch_button(CTRL_BTN_B, False),
        client.batch_axis(CTRL_AXIS_RX, 1.0),
        client.batch_axis(CTRL_AXIS_RY, -1.0),
    ]
    client.send_batch(events)
    await asyncio.sleep(0.2)
    
    # Test batching with mouse events only (don't mix gamepad after mouse connect)
    logger.info("Batching mouse events...")
    client.send_connect("mouse")
    await asyncio.sleep(0.3)
    
    events = [
        client.batch_mouse_move(100, 50),
        client.batch_mouse_move(-50, -25),
        client.batch_mouse_button(CTRL_MOUSE_LEFT, True),
        client.batch_mouse_button(CTRL_MOUSE_LEFT, False),
        client.batch_mouse_button(CTRL_MOUSE_RIGHT, True),
        client.batch_mouse_button(CTRL_MOUSE_RIGHT, False),
        client.batch_mouse_scroll(0, 2),
        client.batch_mouse_scroll(0, -2),
    ]
    client.send_batch(events)
    await asyncio.sleep(0.5)
    
    # Clean up session
    client.send_disconnect()
    await asyncio.sleep(0.2)
    client.close()


async def test_all_gamepad_inputs():
    """Test ALL gamepad buttons and axes - both unbatched and batched."""
    logger.info("=== Test: All Gamepad Inputs (17 Buttons + 8 Axes) ===")
    
    client = LibrePadUDPClient()
    await client.connect()
    
    # Establish session
    client.send_hello("GamepadFullTest")
    await asyncio.sleep(0.5)
    
    # Connect to gamepad device
    client.send_connect("standard")
    await asyncio.sleep(0.5)
    
    # ========================================================================
    # PART 1: Test all buttons UNBATCHED
    # ========================================================================
    logger.info("--- Testing ALL 17 buttons (unbatched) ---")
    
    all_buttons = [
        (CTRL_BTN_A, "A"),
        (CTRL_BTN_B, "B"),
        (CTRL_BTN_X, "X"),
        (CTRL_BTN_Y, "Y"),
        (CTRL_BTN_L1, "L1"),
        (CTRL_BTN_R1, "R1"),
        (CTRL_BTN_L2, "L2"),
        (CTRL_BTN_R2, "R2"),
        (CTRL_BTN_DPAD_UP, "DPAD_UP"),
        (CTRL_BTN_DPAD_DOWN, "DPAD_DOWN"),
        (CTRL_BTN_DPAD_LEFT, "DPAD_LEFT"),
        (CTRL_BTN_DPAD_RIGHT, "DPAD_RIGHT"),
        (CTRL_BTN_BACK, "BACK"),
        (CTRL_BTN_START, "START"),
        (CTRL_BTN_GUIDE, "GUIDE"),
        (CTRL_BTN_L3, "L3"),
        (CTRL_BTN_R3, "R3"),
    ]
    
    for code, name in all_buttons:
        logger.info(f"Testing button: {name} (0x{code:04x})")
        client.send_button(code, True)   # Press
        await asyncio.sleep(0.03)
        client.send_button(code, False)  # Release
        await asyncio.sleep(0.03)
    
    logger.info(f"✓ All {len(all_buttons)} buttons tested (unbatched)")
    await asyncio.sleep(0.3)
    
    # ========================================================================
    # PART 2: Test all axes UNBATCHED
    # ========================================================================
    logger.info("--- Testing ALL 8 axes (unbatched) ---")
    
    all_axes = [
        (CTRL_AXIS_LX, "LX (left stick X)", [0.0, 0.5, 1.0, -0.5, -1.0, 0.0]),
        (CTRL_AXIS_LY, "LY (left stick Y)", [0.0, 0.5, 1.0, -0.5, -1.0, 0.0]),
        (CTRL_AXIS_RX, "RX (right stick X)", [0.0, 0.5, 1.0, -0.5, -1.0, 0.0]),
        (CTRL_AXIS_RY, "RY (right stick Y)", [0.0, 0.5, 1.0, -0.5, -1.0, 0.0]),
        (CTRL_AXIS_LT, "LT (left trigger)", [0.0, 0.5, 1.0, 0.0]),
        (CTRL_AXIS_RT, "RT (right trigger)", [0.0, 0.5, 1.0, 0.0]),
        (CTRL_AXIS_DPAD_X, "DPAD_X", [-1.0, 0.0, 1.0, 0.0]),
        (CTRL_AXIS_DPAD_Y, "DPAD_Y", [-1.0, 0.0, 1.0, 0.0]),
    ]
    
    for code, name, values in all_axes:
        logger.info(f"Testing axis: {name} (0x{code:04x})")
        for value in values:
            client.send_axis(code, value)
            await asyncio.sleep(0.02)
    
    logger.info(f"✓ All {len(all_axes)} axes tested (unbatched)")
    await asyncio.sleep(0.3)
    
    # ========================================================================
    # PART 3: Test all buttons BATCHED (17 buttons in one packet)
    # ========================================================================
    logger.info("--- Testing ALL 17 buttons (BATCHED in single packet) ---")
    
    batch_events = []
    for code, name in all_buttons:
        batch_events.append(client.batch_button(code, True))   # Press
        batch_events.append(client.batch_button(code, False))  # Release
    
    logger.info(f"Sending BATCH with {len(batch_events)} button events (34 press+release)")
    client.send_batch(batch_events)
    await asyncio.sleep(0.5)
    
    # ========================================================================
    # PART 4: Test all axes BATCHED (8 axes in one packet)
    # ========================================================================
    logger.info("--- Testing ALL 8 axes (BATCHED in single packet) ---")
    
    batch_events = []
    # Test each axis with multiple values
    for code, name, values in all_axes:
        for value in values:
            batch_events.append(client.batch_axis(code, value))
    
    logger.info(f"Sending BATCH with {len(batch_events)} axis events")
    client.send_batch(batch_events)
    await asyncio.sleep(0.5)
    
    # ========================================================================
    # PART 5: Test mixed batching (buttons + axes together, gamepad only)
    # ========================================================================
    logger.info("--- Testing MIXED batch (buttons + axes for gamepad) ---")
    
    mixed_batch = [
        # Face buttons
        client.batch_button(CTRL_BTN_A, True),
        client.batch_button(CTRL_BTN_A, False),
        client.batch_button(CTRL_BTN_B, True),
        client.batch_button(CTRL_BTN_B, False),
        # Sticks
        client.batch_axis(CTRL_AXIS_LX, 0.8),
        client.batch_axis(CTRL_AXIS_LY, -0.6),
        client.batch_axis(CTRL_AXIS_RX, -0.7),
        client.batch_axis(CTRL_AXIS_RY, 0.9),
        # Triggers (analog)
        client.batch_axis(CTRL_AXIS_LT, 0.5),
        client.batch_axis(CTRL_AXIS_RT, 0.5),
        # Trigger buttons
        client.batch_button(CTRL_BTN_L2, True),
        client.batch_button(CTRL_BTN_L2, False),
        # D-pad buttons
        client.batch_button(CTRL_BTN_DPAD_UP, True),
        client.batch_button(CTRL_BTN_DPAD_UP, False),
        # Shoulders
        client.batch_button(CTRL_BTN_L1, True),
        client.batch_button(CTRL_BTN_R1, True),
        client.batch_button(CTRL_BTN_L1, False),
        client.batch_button(CTRL_BTN_R1, False),
    ]
    
    logger.info(f"Sending MIXED BATCH with {len(mixed_batch)} gamepad events (buttons + axes)")
    client.send_batch(mixed_batch)
    await asyncio.sleep(0.5)
    
    logger.info("✓ All gamepad inputs tested successfully!")
    logger.info("✓ Summary: 17 buttons + 8 axes tested both unbatched and batched")
    
    # Clean up session
    client.send_disconnect()
    await asyncio.sleep(0.2)
    client.close()


async def main():
    """Run tests."""
    try:
        await test_basic_session()
        await asyncio.sleep(1)
        
        await test_gamepad_input()
        await asyncio.sleep(1)
        
        await test_mouse_input()
        await asyncio.sleep(1)
        
        await test_batching()
        await asyncio.sleep(1)
        
        await test_all_gamepad_inputs()
        
        logger.info("=== All Tests Complete ===")
        
    except Exception as e:
        logger.error("Test failed: %s", e, exc_info=True)
        await asyncio.sleep(1)
        
        await test_mouse_input()
        await asyncio.sleep(1)
        
        await test_batching()
        
        logger.info("=== Tests Complete ===")
        
    except Exception as e:
        logger.error("Test failed: %s", e, exc_info=True)


if __name__ == "__main__":
    asyncio.run(main())
