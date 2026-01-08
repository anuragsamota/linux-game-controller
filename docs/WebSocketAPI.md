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

### `axis`
Set an axis value (float).
```json
{"event": "axis", "device": "standard", "name": "lx", "value": 0.25}
```
Response:
```json
{"type": "ok"}
```

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
