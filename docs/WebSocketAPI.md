# WebSocket API Specification

Server address: `ws://<host>:<port>` (default: `ws://localhost:8765`)

On connection, the server sends a `welcome` message:
```json
{
  "type": "welcome",
  "devices": ["standard"],
  "schema": {
    "connect": {"device": "standard"},
    "disconnect": {},
    "rename": {"name": "My Gamepad"},
    "button": {"device": "standard", "name": "a", "pressed": true},
    "axis": {"device": "standard", "name": "lx", "value": 0.25},
    "ping": {}
  }
}
```

## Message Envelope
- Client → Server messages contain: `event`
- Server → Client messages contain: `type`

## Client → Server

### `connect`
Acquire a device to control.
```json
{"event": "connect", "device": "standard", "name": "Player 1"}
```
Response:
```json
{"type": "ok", "connected": "standard", "name": "Player 1"}
```

### `disconnect`
Release the currently connected device.
```json
{"event": "disconnect"}
```
Response:
```json
{"type": "ok"}
```

### `button`
Set a button press state.
```json
{"event": "button", "device": "standard", "name": "a", "pressed": true}
```
Response:
```json
{"type": "ok"}
```

**Available Buttons for `standard` device:**
- Face buttons: `a`, `b`, `x`, `y`
- Shoulder buttons: `l1`, `r1` (also known as LB/RB)
- Trigger buttons (click): `l2_click`, `r2_click` (also known as LT/RT click)
- Thumbstick buttons: `l3`, `r3` (press down on joysticks)
- D-pad buttons: `dpad_up`, `dpad_down`, `dpad_left`, `dpad_right`
- Menu buttons: `start`, `back` (also known as Menu/View or Select)

### `axis`
Set an axis value (float, typically -1.0 to 1.0 range).
```json
{"event": "axis", "device": "standard", "name": "lx", "value": 0.25}
```
Response:
```json
{"type": "ok"}
```

**Available Axes for `standard` device:**
- Left joystick: `lx` (left -1.0, right +1.0), `ly` (up -1.0, down +1.0)
- Right joystick: `rx` (left -1.0, right +1.0), `ry` (up -1.0, down +1.0)
- Triggers: `lt` (0.0 to 1.0), `rt` (0.0 to 1.0)
- D-pad axes: `dpad_x` (left -1.0, right +1.0), `dpad_y` (up -1.0, down +1.0)
  - **Note:** D-pad axes are mirrored to button events automatically
  - Sending `dpad_x: -1.0` triggers `dpad_left` button press
  - Sending `dpad_x: 0.0` releases both `dpad_left` and `dpad_right`
- Touchpad: `px` (-1.0 to 1.0), `py` (-1.0 to 1.0)

**Axis Value Conventions:**
- Joysticks: -1.0 (full left/up) to +1.0 (full right/down), 0.0 centered
- Triggers: 0.0 (not pressed) to 1.0 (fully pressed)
- D-pad axes: -1.0, 0.0, or +1.0 (discrete positions)
- Touchpad: -1.0 to +1.0 for both x and y coordinates

### `rename`
Note: device names are immutable; this returns an error.
```json
{"event": "rename", "name": "New Name"}
```
Response:
```json
{"type": "error", "message": "Device names cannot be changed after creation. Use 'name' in the connect event."}
```

### `ping`
Keepalive / latency check.
```json
{"event": "ping"}
```
Response:
```json
{"type": "pong"}
```

## Errors
Errors use a consistent envelope:
```json
{"type": "error", "code": "invalid_json", "message": "Could not decode message as JSON"}
```
Common codes:
- `invalid_json`: failed to parse JSON
- `invalid_message`: unsupported event or bad payload

## Connection & Timeouts
- `max_size`: 128KB
- `ping_interval`: 20s
- `ping_timeout`: 10s
- `close_timeout`: 5s

## Disconnections
- Normal closes are logged as info; no server exceptions.
- Server safely releases devices in `finally`.
- Sends are guarded; attempting to send after disconnection is ignored.
