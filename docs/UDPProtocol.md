# LibrePad UDP Control Protocol (Design Spec)

**Status:** Draft v0.3 (Finalized Design)  
**Version:** 0.3  
**Scope:** Non-web native clients (e.g., Flutter) controlling LibrePad Server via UDP  
**Date:** January 10, 2026

## Table of Contents
1. [Goals & Non-Goals](#goals--non-goals)
2. [Transport](#transport)
3. [Message Structure](#message-structure)
4. [Message Type Reference](#message-type-reference)
5. [Control Code Registry](#control-code-registry)
6. [Session Lifecycle](#session-lifecycle)
7. [Event Batching](#event-batching)
8. [TLV Extensions](#tlv-extensions)
9. [Protocol Diagrams](#protocol-diagrams)
10. [Wire Frame Examples](#wire-frame-examples)
11. [Implementation Guide](#implementation-guide)

---

## Goals & Non-Goals

### Goals
- Very low-latency input transport for controller/touchpad events.
- Simple, compact, binary format with clear versioning.
- Resilient to packet loss with optional lightweight reliability.
- Easy to implement across platforms (Flutter/Dart, Python, C/C++).
- Backwards-compatible evolution via capability negotiation.
- Bidirectional: Client→Server input, Server→Client feedback and status.
- **Platform-independent:** All control codes defined by protocol, not OS-specific.

### Non-Goals
- Guaranteed delivery for all messages (UDP is lossy; we provide best-effort).
- Complex fragmentation/reassembly beyond typical MTU (~1200 bytes safe baseline).
- Transport encryption; recommend running on trusted LAN or add DTLS/TLS tunnel if needed.
- Built-in compression (binary format is already compact; adds latency).

---

## Transport
- **Protocol:** UDP
- **Default Port:** 9775 (configurable)
- **Endianness:** Little-endian for all multi-byte integers
- **MTU Guidance:** Keep packets ≤ 1200 bytes to avoid fragmentation on common networks

---

## Message Structure

All protocol messages begin with a fixed header, followed by optional extended header and message-specific payload.

### Packet Structure Diagram
```
┌─────────────────────────────────────────────────────────────┐
│                     UDP Header (8 bytes)                     │
├─────────────────────────────────────────────────────────────┤
│                  Common Header (12 bytes)                    │
│ ┌─────┬─────┬─────┬─────────────┬───────────────────────┐   │
│ │ ver │ typ │flags│ session_id  │         seq           │   │
│ │ u8  │ u8  │ u16 │     u32     │         u32           │   │
│ └─────┴─────┴─────┴─────────────┴───────────────────────┘   │
├─────────────────────────────────────────────────────────────┤
│         Extended Header (optional, 8 bytes if flags & 0x0002)│
│ ┌───────────────────────────────────────────────────────┐   │
│ │              timestamp_us (u64)                       │   │
│ └───────────────────────────────────────────────────────┘   │
├─────────────────────────────────────────────────────────────┤
│               Message-Specific Payload                       │
│                    (variable length)                         │
└─────────────────────────────────────────────────────────────┘
```

### Common Header (12 bytes)
### Common Header (12 bytes)

| Offset | Field       | Type | Description                                    |
|--------|-------------|------|------------------------------------------------|
| 0      | version     | u8   | Protocol version (initially 1)                 |
| 1      | msg_type    | u8   | Message type code (see reference table below)  |
| 2      | flags       | u16  | Bitfield flags                                 |
| 4      | session_id  | u32  | Server-allocated or client-chosen session ID   |
| 8      | seq         | u32  | Client sequence number (monotonic per client)  |

### Flags Bitfield (u16)

| Bit | Name          | Description                                      |
|-----|---------------|--------------------------------------------------|
| 0   | ACK_REQUEST   | Server should acknowledge this packet            |
| 1   | HAS_TIMESTAMP | Extended header with timestamp_us follows        |
| 2-15| Reserved      | Must be 0; available for future use              |

### Optional Extended Header (8 bytes, when flags & 0x0002)

| Offset | Field        | Type | Description                                |
|--------|--------------|------|--------------------------------------------|
| 12     | timestamp_us | u64  | Client send time in microseconds (telemetry)|

**Note:** After WELCOME, all input events use `device_id` (u16) not string-based device types to minimize overhead.

---

## Message Type Reference

### Complete Message Type Table

| Code   | Name               | Direction      | Description                                  | Payload Size     |
|--------|--------------------|----------------|----------------------------------------------|------------------|
| 0x01   | HELLO              | Client→Server  | Client announces itself and capabilities     | ~20-100 bytes    |
| 0x02   | WELCOME            | Server→Client  | Server response, assigns session             | ~30-150 bytes    |
| 0x03   | PING               | Client→Server  | Keepalive (minimal)                          | 0 bytes          |
| 0x04   | PONG               | Server→Client  | Keepalive response                           | 0 bytes          |
| 0x05   | SESSION_END        | Bidirectional  | Graceful session termination                 | 3+ bytes         |
| 0x10   | CONNECT            | Client→Server  | Acquire virtual device                       | 5-50 bytes       |
| 0x11   | DISCONNECT         | Client→Server  | Release device                               | 3-20 bytes       |
| 0x20   | BUTTON             | Client→Server  | Digital button press/release                 | 5 bytes          |
| 0x21   | AXIS               | Client→Server  | Analog axis value                            | 6 bytes          |
| 0x22   | MOUSE_MOVE         | Client→Server  | Relative mouse movement                      | 4 bytes          |
| 0x23   | MOUSE_BUTTON       | Client→Server  | Mouse button press/release                   | 3 bytes          |
| 0x26   | MOUSE_SCROLL       | Client→Server  | Mouse scroll wheel (horizontal/vertical)     | 4 bytes          |
| 0x24   | KEY_EVENT          | Client→Server  | Keyboard key press/release                   | 3 bytes          |
| 0x25   | TEXT_INPUT         | Client→Server  | Keyboard text input                          | 2+ text_len      |
| 0x30   | ERROR              | Server→Client  | Error response                               | 3+ msg_len       |
| 0x31   | INFO               | Server→Client  | Informational event                          | Variable         |
| 0x32   | STATUS             | Server→Client  | Device/session status update                 | 5+ msg_len       |
| 0x33   | CONTROLLER_INFO    | Server→Client  | Controller metadata                          | Variable         |
| 0x40   | BATCH              | Client→Server  | Multiple events in single datagram           | Variable         |
| 0x50   | FEEDBACK           | Server→Client  | Generic feedback envelope                    | Variable         |
| 0x51   | FEEDBACK_HAPTIC    | Server→Client  | Haptic/rumble parameters                     | 8+ bytes         |
| 0x52   | FEEDBACK_LED       | Server→Client  | LED color/pattern                            | 4+ bytes         |

---

## Control Code Registry

All control codes are **protocol-defined and platform-independent**. The server backend maps these codes to OS-specific input APIs (Linux uinput/evdev, Windows virtual key codes, macOS keycodes, etc.).

### Gamepad Control Codes

#### Buttons (0x0001–0x0011)

| Code   | Name       | Description          |
|--------|------------|----------------------|
| 0x0001 | A          | Face button A (South)|
| 0x0002 | B          | Face button B (East) |
| 0x0003 | X          | Face button X (West) |
| 0x0004 | Y          | Face button Y (North)|
| 0x0005 | L1         | Left shoulder        |
| 0x0006 | R1         | Right shoulder       |
| 0x0007 | L2         | Left trigger         |
| 0x0008 | R2         | Right trigger        |
| 0x0009 | DPAD_UP    | D-pad up             |
| 0x000A | DPAD_DOWN  | D-pad down           |
| 0x000B | DPAD_LEFT  | D-pad left           |
| 0x000C | DPAD_RIGHT | D-pad right          |
| 0x000D | BACK       | Back/Select button   |
| 0x000E | START      | Start button         |
| 0x000F | GUIDE      | Guide/Home button    |
| 0x0010 | L3         | Left stick click     |
| 0x0011 | R3         | Right stick click    |

#### Axes (0x0101–0x0108)

| Code   | Name    | Description              | Range          |
|--------|---------|--------------------------|----------------|
| 0x0101 | LX      | Left stick X             | -32768 to 32767|
| 0x0102 | LY      | Left stick Y             | -32768 to 32767|
| 0x0103 | RX      | Right stick X            | -32768 to 32767|
| 0x0104 | RY      | Right stick Y            | -32768 to 32767|
| 0x0105 | LT      | Left trigger analog      | -32768 to 32767|
| 0x0106 | RT      | Right trigger analog     | -32768 to 32767|
| 0x0107 | DPAD_X  | D-pad X axis             | -32768 to 32767|
| 0x0108 | DPAD_Y  | D-pad Y axis             | -32768 to 32767|

### Mouse Control Codes (0x0201–0x0205)

| Code   | Name      | Description          |
|--------|-----------|----------------------|
| 0x0201 | LEFT      | Left button          |
| 0x0202 | RIGHT     | Right button         |
| 0x0203 | MIDDLE    | Middle button        |
| 0x0204 | SCROLL_X  | Horizontal scroll    |
| 0x0205 | SCROLL_Y  | Vertical scroll      |

### Keyboard Control Codes (0x0300–0x03FF)

#### Letters (0x0301–0x031A)

| Code Range      | Keys |
|-----------------|------|
| 0x0301–0x031A   | A–Z  |

#### Numbers (0x031B–0x0324)

| Code Range      | Keys |
|-----------------|------|
| 0x031B–0x0324   | 0–9  |

#### Function Keys (0x0325–0x0330)

| Code Range      | Keys    |
|-----------------|---------|
| 0x0325–0x0330   | F1–F12  |

#### Navigation (0x0331–0x0338)

| Code   | Name      |
|--------|-----------|
| 0x0331 | UP        |
| 0x0332 | DOWN      |
| 0x0333 | LEFT      |
| 0x0334 | RIGHT     |
| 0x0335 | HOME      |
| 0x0336 | END       |
| 0x0337 | PAGE_UP   |
| 0x0338 | PAGE_DOWN |

#### Editing (0x0339–0x033E)

| Code   | Name      |
|--------|-----------|
| 0x0339 | ENTER     |
| 0x033A | BACKSPACE |
| 0x033B | DELETE    |
| 0x033C | TAB       |
| 0x033D | ESCAPE    |
| 0x033E | SPACE     |

#### Modifiers (0x033F–0x0346)

| Code   | Name    | Description           |
|--------|---------|-----------------------|
| 0x033F | SHIFT_L | Left Shift            |
| 0x0340 | SHIFT_R | Right Shift           |
| 0x0341 | CTRL_L  | Left Control          |
| 0x0342 | CTRL_R  | Right Control         |
| 0x0343 | ALT_L   | Left Alt              |
| 0x0344 | ALT_R   | Right Alt             |
| 0x0345 | META_L  | Left Meta (Win/Cmd)   |
| 0x0346 | META_R  | Right Meta (Win/Cmd)  |

#### Punctuation/Symbols (0x0347–0x0350)

| Code   | Name          | Symbol |
|--------|---------------|--------|
| 0x0347 | MINUS         | -      |
| 0x0348 | EQUALS        | =      |
| 0x0349 | BRACKET_LEFT  | [      |
| 0x034A | BRACKET_RIGHT | ]      |
| 0x034B | BACKSLASH     | \\     |
| 0x034C | SEMICOLON     | ;      |
| 0x034D | QUOTE         | '      |
| 0x034E | COMMA         | ,      |
| 0x034F | PERIOD        | .      |
| 0x0350 | SLASH         | /      |

#### Special (0x0351–0x0353)

| Code   | Name          |
|--------|---------------|
| 0x0351 | CAPS_LOCK     |
| 0x0352 | INSERT        |
| 0x0353 | PRINT_SCREEN  |

**Note:** Reserve 0x0300–0x03FF range for keyboard. Extend as needed for international layouts, numpad, etc.

### Backend Mapping Example

| Protocol Code | Linux evdev | Windows   | macOS           |
|---------------|-------------|-----------|-----------------|
| 0x0301 (A)    | KEY_A (30)  | VK_A (65) | kVK_ANSI_A (0)  |
| 0x0339 (ENTER)| KEY_ENTER (28)| VK_RETURN (13)| kVK_Return (36)|

**Fallback:** Unknown controls may be sent as TLV CONTROL_NAME (utf8) if needed, but prefer codes for efficiency.

---

---

## Session Lifecycle

### Lifecycle Flow Diagram
```
Client                                Server
  │                                     │
  │  1. HELLO (caps, name)              │
  ├──────────────────────────────────>  │
  │                                     │ ── Validate & allocate session
  │  2. WELCOME (session_id, devices)   │
  │  <──────────────────────────────────┤
  │                                     │
  │  3. CONNECT ("standard")            │
  ├──────────────────────────────────>  │
  │                                     │ ── Create virtual device
  │  4. STATUS (device_connected)       │
  │  <──────────────────────────────────┤
  │                                     │
  │  5. BUTTON/AXIS/KEY events          │
  ├──────────────────────────────────>  │
  │     (batched every 10ms)            │ ── Process inputs
  │                                     │
  │  6. PING (every 2s)                 │
  ├──────────────────────────────────>  │
  │                                     │
  │  7. PONG                            │
  │  <──────────────────────────────────┤
  │                                     │
  │  8. FEEDBACK_HAPTIC (optional)      │
  │  <──────────────────────────────────┤
  │                                     │
  │  9. SESSION_END (logout)            │
  ├──────────────────────────────────>  │
  │                                     │ ── Cleanup session
  │                                     │
```

### Lifecycle Steps
### Lifecycle Steps
1. Client sends `HELLO` with capability bits and client name.
2. Server replies `WELCOME` with `assigned_session_id`, accepted capabilities, and available devices with device_id assignments.
3. Client may send `CONNECT` for device(s) (e.g., "standard", "mouse").
4. Client sends input events (`BUTTON`, `AXIS`, `MOUSE_MOVE`, `KEY_EVENT`, etc.).
5. Server may send `STATUS`, `CONTROLLER_INFO`, or `FEEDBACK` at any time.
6. Either side may send `SESSION_END` to gracefully close. Otherwise, server expires after heartbeat timeout (e.g., 30s without `PING`).

### Message Payloads

#### HELLO Payload
```
┌────────────────────────────────────────┐
│ u16   caps_len                         │
│ u8[]  caps_bits (packed bitset)        │
│       Bit 0: Supports ACKs             │
│       Bit 1: Supports timestamps       │
│       Bit 2: Supports compression      │
│       Bit 3: Supports batched events   │
│       Bit 4: Supports feedback         │
│ u8    name_len                         │
│ utf8  client_name                      │
└────────────────────────────────────────┘
```

#### WELCOME Payload
```
┌────────────────────────────────────────┐
│ u32   assigned_session_id              │
│ u16   caps_len                         │
│ u8[]  accepted_caps_bits               │
│ u8    dev_count                        │
│ ┌────────────────────────────────────┐ │
│ │ For each device:                   │ │
│ │   u8   type_len                    │ │
│ │   utf8 type_name                   │ │
│ │   u16  device_id                   │ │
│ └────────────────────────────────────┘ │
└────────────────────────────────────────┘
```

#### CONNECT Payload
```
┌────────────────────────────────────────┐
│ u8    type_len                         │
│ utf8  device_type                      │
│       (e.g., "standard", "mouse")      │
│ u8    name_len                         │
│ utf8  display_name (optional)          │
└────────────────────────────────────────┘
```

#### DISCONNECT Payload
```
┌────────────────────────────────────────┐
│ u8    type_len                         │
│ utf8  device_type                      │
└────────────────────────────────────────┘
```

#### SESSION_END Payload
```
┌────────────────────────────────────────┐
│ u16   reason_code                      │
│       0x0000 normal                    │
│       0x0001 client logout             │
│       0x0002 server shutdown           │
│       0xFFFF unspecified               │
│ u8    msg_len                          │
│ utf8  reason_message (optional)        │
└────────────────────────────────────────┘
```

### Reliability & Ordering
- Clients include monotonically increasing `seq` per packet.
- Optional ACKs: If `flags & 0x0001` (ACK_REQUEST), server replies with `INFO` or piggybacks ACK info in `PONG`.
- Application-level idempotency: Button/axis events can be resent; server processes last-in-wins.
- No fragmentation: Clients should batch small sets of events per packet and avoid exceeding MTU.

### Latency Telemetry
**PING/PONG timestamps** (when `flags & 0x0002`):
- Client sends `PING` with header `flags=0x0002` + optional 8-byte `timestamp_us`.
- Server replies `PONG` with same `timestamp_us` field echoed back.
- Client measures round-trip latency as `now_us - sent_timestamp_us`.
- Servers/clients that don't need telemetry omit the flag, using only 12-byte header (40 bytes total per heartbeat including IP/UDP).

### Rate Limits & Keepalive
- Suggested client send rate: ≤ 250 packets/sec.
- Heartbeat: `PING` every 2s; server replies `PONG`. Unacknowledged for >10s → server may expire session.
- Server may also send `PONG` unsolicited or piggyback status updates.

---

## Input Events

All input messages use control codes and device IDs to eliminate string overhead. Payloads are minimal and fixed-size for most events.

### Event Payload Formats

#### BUTTON (digital) — 5 bytes typical
```
┌──────────────────────────────────────┐
│ u16   device_id                      │
│ u16   control_code (0x0001–0x0011)   │
│ u8    pressed (0 or 1)               │
│ [Optional TLVs: PRESSURE, TIMESTAMP] │
└──────────────────────────────────────┘
```

#### AXIS (analog) — 6 bytes typical
```
┌──────────────────────────────────────┐
│ u16   device_id                      │
│ u16   control_code (0x0101–0x0108)   │
│ i16   value (-32768 to 32767)        │
│       represents [-1.0, 1.0]         │
│ [Optional TLVs: PRESSURE, VELOCITY]  │
└──────────────────────────────────────┘
```

#### MOUSE_MOVE (relative) — 4 bytes
```
┌──────────────────────────────────────┐
│ i16   dx (delta X)                   │
│ i16   dy (delta Y)                   │
│ [Optional TLVs: VELOCITY, TIMESTAMP] │
└──────────────────────────────────────┘
```

#### MOUSE_BUTTON — 3 bytes typical
```
┌──────────────────────────────────────┐
│ u16   control_code (0x0201–0x0203)   │
│ u8    pressed (0 or 1)               │
│ [Optional TLVs: TIMESTAMP]           │
└──────────────────────────────────────┘
```

#### MOUSE_SCROLL — 4 bytes
```
┌──────────────────────────────────────┐
│ i16   scroll_x (horizontal delta)    │
│ i16   scroll_y (vertical delta)      │
│       Typical values: ±120 per notch │
│ [Optional TLVs: TIMESTAMP]           │
└──────────────────────────────────────┘
```

#### KEY_EVENT (keyboard) — 3 bytes typical
```
┌──────────────────────────────────────┐
│ u16   key_code (0x0301–0x03FF)       │
│ u8    pressed (0 or 1)               │
│ [Optional TLVs: TIMESTAMP]           │
└──────────────────────────────────────┘
```

#### TEXT_INPUT (keyboard text) — variable
```
┌──────────────────────────────────────┐
│ u16   text_len                       │
│ utf8  text                           │
│ [Optional TLVs: TIMESTAMP]           │
└──────────────────────────────────────┘
```

---

## Event Batching — Major Overhead Reduction

### Why Batch?
UDP overhead (28 bytes IP/UDP per packet) dominates small events. Batching 10 rapid events:
- **Unbatched:** 10 packets × 28 bytes overhead = **280 bytes wasted**
- **Batched:** 1 packet × 28 bytes = **28 bytes total overhead** → **~90% reduction**

### Batch Overhead Comparison
```
┌─────────────────────────────────────────────────────────────┐
│ Unbatched (3 separate packets):                             │
├─────────────────────────────────────────────────────────────┤
│ Packet 1: 28B overhead + 12B header + 5B BUTTON    = 45B   │
│ Packet 2: 28B overhead + 12B header + 6B AXIS      = 46B   │
│ Packet 3: 28B overhead + 12B header + 5B BUTTON    = 45B   │
│ TOTAL: 136 bytes                                            │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│ Batched (1 packet):                                         │
├─────────────────────────────────────────────────────────────┤
│ 28B overhead + 12B header + 1B count + 16B events  = 57B   │
│ TOTAL: 57 bytes (58% savings!)                              │
└─────────────────────────────────────────────────────────────┘
```

### BATCH Message Format (`msg_type = 0x40`)
```
┌──────────────────────────────────────────────────────────┐
│ u8    event_count                                        │
├──────────────────────────────────────────────────────────┤
│ Sequential events (no inner framing):                    │
│ ┌────────────────────────────────────────────────────┐   │
│ │ BUTTON:       [u16 dev_id][u16 code][u8 pressed]   │   │
│ │ AXIS:         [u16 dev_id][u16 code][i16 value]    │   │
│ │ MOUSE_MOVE:   [i16 dx][i16 dy]                     │   │
│ │ MOUSE_BUTTON: [u16 code][u8 pressed]               │   │
│ │ MOUSE_SCROLL: [i16 scroll_x][i16 scroll_y]         │   │
│ │ KEY_EVENT:    [u16 code][u8 pressed]               │   │
│ │ TEXT_INPUT:   [u16 len][utf8[len]]                 │   │
│ │ TLV:          [u8 header][u8[len] value]           │   │
│ └────────────────────────────────────────────────────┘   │
└──────────────────────────────────────────────────────────┘
```

### Client-Side Batching Strategy
1. **Buffer small events** temporarily (BUTTON, AXIS, MOUSE_MOVE, KEY_EVENT).
2. **Flush conditions** (whichever comes first):
   - **Time-based:** 10ms elapsed (typical RTT on LAN; balance latency vs packet overhead).
   - **Size-based:** Payload approaches 1200 bytes (MTU safety margin).
   - **Explicit:** User releases controller / long idle (5s → send pending).
3. **Large events** (TEXT_INPUT) may flush immediately since string data is unpredictable.

### Batch Flow Example
```
Timeline:
  t=0ms:  User presses Button A      → buffer [BUTTON event]
  t=2ms:  User moves LX analog       → buffer [BUTTON, AXIS]
  t=5ms:  User presses Button B      → buffer [BUTTON, AXIS, BUTTON]
  t=10ms: Timer fires                → flush BATCH(3 events) ✓
          Single UDP packet sent     → 57 bytes vs 136 unbatched
```

### Server Receiving Batched Events
- Parse `event_count`.
- Read events sequentially by their type.
- Treat each inner event as if it arrived independently (same state updates).
- Unknown/malformed events in batch: skip gracefully; process remainder.

---

## TLV Extensions

TLVs are appended at the end of a message payload and are fully optional.

### Compact TLV Format
```
┌────────────────────────────────────────┐
│ u8  tlv_header                         │
│     ┌─────────┬─────────┐              │
│     │ Type(4b)│ Len(4b) │              │
│     └─────────┴─────────┘              │
│     If len == 15: next u16 = actual    │
│ u8[] tlv_value                         │
└────────────────────────────────────────┘
```

### TLV Type Reference

| Type | Name               | Value Format        | Size      | Description                    |
|------|--------------------|---------------------|-----------|--------------------------------|
| 0x0  | RESERVED           | -                   | -         | Must not be used               |
| 0x1  | PRESSURE_I16       | i16                 | 2 bytes   | Button pressure (0–32767)      |
| 0x2  | VELOCITY_I16x2     | i16[2]              | 4 bytes   | Movement velocity (dx, dy)     |
| 0x3  | TIMESTAMP_US       | u64                 | 8 bytes   | Event timestamp (microseconds) |
| 0x4  | CONTROL_NAME_UTF8  | utf8                | Variable  | Fallback control name          |
| 0x5+ | Reserved           | -                   | -         | Available for future use       |

### TLV Example

**Pressure TLV** (pressure = 16384):
```
Header: (0x1 << 4) | 2 = 0x12
Value:  0x00 0x40 (16384 in little-endian i16)
Total:  3 bytes
```

**Timestamp TLV** (timestamp_us = 1704899400123456):
```
Header: (0x3 << 4) | 8 = 0x38
Value:  0x40 0x1F 0x5D 0x8C 0x01 0x06 0x00 0x00 (u64 little-endian)
Total:  9 bytes
```

---

### Complete Packet Example (BUTTON with Timestamp)
```
Byte Layout (31 bytes total):
┌──────────────────────────────────────────────────────────────┐
│ IP Header (20 bytes, not shown)                              │
├──────────────────────────────────────────────────────────────┤
│ UDP Header (8 bytes, not shown)                              │
├──────────────────────────────────────────────────────────────┤
│ Common Header (12 bytes):                                    │
│   0x01              version = 1                              │
│   0x20              msg_type = BUTTON                        │
│   0x02 0x00         flags = 0x0002 (has timestamp)           │
│   0xD2 0x04 0x00 0x00   session_id = 1234                    │
│   0x05 0x00 0x00 0x00   seq = 5                              │
├──────────────────────────────────────────────────────────────┤
│ Extended Header (8 bytes):                                   │
│   0x40 0x1F 0x5D 0x8C   timestamp_us = 1704899400123456      │
│   0x01 0x06 0x00 0x00                                        │
├──────────────────────────────────────────────────────────────┤
│ BUTTON Payload (5 bytes):                                    │
│   0x00 0x00         device_id = 0                            │
│   0x01 0x00         control_code = 0x0001 (A button)         │
│   0x01              pressed = 1                              │
├──────────────────────────────────────────────────────────────┤
│ TLV - PRESSURE (3 bytes):                                    │
│   0x12              header: type=0x1, len=2                  │
│   0x00 0x40         value = 16384 (i16)                      │
├──────────────────────────────────────────────────────────────┤
│ TLV - Extra TIMESTAMP (9 bytes, optional):                   │
│   0x38              header: type=0x3, len=8                  │
│   0x50 0x1F 0x5D 0x8C   timestamp_us = 1704899400123472      │
│   0x01 0x06 0x00 0x00                                        │
└──────────────────────────────────────────────────────────────┘
Total: 20 (IP) + 8 (UDP) + 12 (header) + 8 (ext) + 5 (payload) +
       3 (TLV) = 56 bytes (or 65 with extra timestamp TLV)
```

### Capability Negotiation Flow
```
Client                                Server
  │                                     │
  │  HELLO:                             │
  │  caps_bits = 0b00011111             │
  │  (ACK, timestamp, compress,         │
  │   batch, feedback)                  │
  ├──────────────────────────────────>  │
  │                                     │
  │                                     │ ── Check capabilities
  │                                     │    Accept: ACK, timestamp,
  │                                     │            batch, feedback
  │                                     │    Reject: compress (not impl)
  │                                     │
  │  WELCOME:                           │
  │  accepted_caps = 0b00010111         │
  │  (ACK, timestamp, batch, feedback)  │
  │  <──────────────────────────────────┤
  │                                     │
  │  Client now knows:                  │
  │  ✓ Can use batching                 │
  │  ✓ Can use timestamps               │
  │  ✓ Server supports feedback         │
  │  ✗ Compression not available        │
  │                                     │
```

---

## Server→Client Messages

### STATUS Payload
```
┌────────────────────────────────────────┐
│ u16   status_code                      │
│       0x0001 device connected          │
│       0x0002 device disconnected       │
│       0x0003 session paused            │
│       0x0004 session resumed           │
│ u8    type_len or u16 device_id        │
│ utf8  device_type (if type_len used)   │
│ u8    msg_len                          │
│ utf8  status_message                   │
└────────────────────────────────────────┘
```

### CONTROLLER_INFO Payload
```
┌────────────────────────────────────────┐
│ u16   info_flags (bitset)              │
│       Bit 0: name present              │
│       Bit 1: version present           │
│       Bit 2: feature list present      │
├────────────────────────────────────────┤
│ If name present:                       │
│   u8   name_len                        │
│   utf8 controller_name                 │
├────────────────────────────────────────┤
│ If version present:                    │
│   u16  version_major                   │
│   u16  version_minor                   │
│   u16  version_patch                   │
├────────────────────────────────────────┤
│ If features present:                   │
│   u8   feature_count                   │
│   For each feature:                    │
│     u8   feature_len                   │
│     utf8 feature_name                  │
└────────────────────────────────────────┘
```

### ERROR Payload
```
┌────────────────────────────────────────┐
│ u16   code                             │
│       0x0001 InvalidMessage            │
│       0x0002 UnknownDevice             │
│       0x0003 NotConnected              │
│       0x0004 RateLimited               │
│       0x0005 InternalError             │
│       0x0006 SessionExpired            │
│ u8    msg_len                          │
│ utf8  message                          │
└────────────────────────────────────────┘
```

### FEEDBACK_HAPTIC Payload
```
┌────────────────────────────────────────┐
│ u16   effect_id (client-local)         │
│ u16   amplitude (0–65535)              │
│ u16   duration_ms                      │
│ u16   frequency_hz (0 if N/A)          │
│ [Optional TLVs: DEVICE_ID, DEVICE_TYPE]│
└────────────────────────────────────────┘
```

### FEEDBACK_LED Payload
```
┌────────────────────────────────────────┐
│ u8    r (0–255)                        │
│ u8    g (0–255)                        │
│ u8    b (0–255)                        │
│ u8    pattern (0=solid, reserved)      │
│ [Optional TLVs: DEVICE_ID, DEVICE_TYPE]│
└────────────────────────────────────────┘
```

Clients SHOULD ignore unsupported feedback gracefully.

---

## Discovery

- **LAN broadcast:** Client sends `HELLO` to `255.255.255.255:9775`; servers reply `WELCOME`.
- **mDNS (optional):** `_librepad._udp.local` service advertisement.

---

## Security

- UDP is plaintext; recommend trusted LAN only.
- For WAN or untrusted networks, run behind VPN or add DTLS.
- Basic allowlist: Server may restrict accepted source IPs.

---

## Versioning & Extensibility

- `version` in header gates behavior.
- Unknown `msg_type`: Server replies `ERROR UnknownMessage` and ignores packet.
- Capability bits safeguard optional features.
- TLV fields unknown to a receiver are silently skipped.

---

## Wire Frame Examples

### 1) Client HELLO → Server WELCOME
```
Client → Server:
  version=1, msg_type=0x01 (HELLO), flags=0x0001 (ack)
  session_id=0, seq=1
  caps_bits=0b00010111 (ACK, timestamp, batch, feedback)
  client_name="Flutter Client v1.0"

Server → Client:
  version=1, msg_type=0x02 (WELCOME), flags=0x0000
  session_id=1234, seq=1
  accepted_caps=0b00010111
  dev_count=2:
    - type="standard", device_id=0
    - type="mouse", device_id=1
```

### 2) Latency Telemetry via PING/PONG
```
Client → Server:
  PING, flags=0x0002 (has timestamp)
  timestamp_us=1704899400123456, seq=2
  [Total: 20 bytes]

Server → Client:
  PONG, flags=0x0002
  timestamp_us=1704899400123456 (echoed)
  [Total: 20 bytes]

Client calculates RTT = now_us - 1704899400123456
```

### 3) Server Sends Controller Info
```
Server → Client:
  msg_type=0x33 (CONTROLLER_INFO)
  session_id=1234, seq=1
  info_flags=0x0007 (name+version+features)
  name="LibrePad Standard"
  version=0.1.0
  features=["gamepad", "keyboard", "mouse"]
```

### 4) Connect Gamepad, Press A Button
```
Client → Server:
  CONNECT: type="standard", name="My Gamepad"

Server → Client:
  WELCOME update: device_id=0 for "standard"

Client → Server:
  BUTTON: device_id=0, control_code=0x0001 (A), pressed=1
  [5 bytes payload]

Client → Server:
  BUTTON: device_id=0, control_code=0x0001 (A), pressed=0
  [5 bytes payload]
```

### 5) Rapid Gamepad Input (Batched)
```
Without batching (3 separate packets):
┌────────────────────────────────────────┐
│ Packet 1: BUTTON(A pressed)           │
│   28B overhead + 12B header + 5B = 45B │
│ Packet 2: AXIS(LX move)               │
│   28B overhead + 12B header + 6B = 46B │
│ Packet 3: BUTTON(B pressed)           │
│   28B overhead + 12B header + 5B = 45B │
│ TOTAL: 136 bytes                       │
└────────────────────────────────────────┘

With batching (1 packet):
┌────────────────────────────────────────┐
│ BATCH(3 events):                       │
│   28B overhead + 12B header +          │
│   1B count + 16B events = 57B          │
│ SAVINGS: 58% (79 bytes saved!)         │
└────────────────────────────────────────┘

Batch payload breakdown:
  event_count=3
  BUTTON(device=0, code=0x0001, pressed=1)   [5 bytes]
  AXIS(device=0, code=0x0101, value=1234)    [6 bytes]
  BUTTON(device=0, code=0x0002, pressed=0)   [5 bytes]
```

### 6) Touchpad Relative Move
```
Client → Server:
  MOUSE_MOVE: dx=12, dy=-7
  [4 bytes payload]

  (Fast touchpad movements may also batch)
```

### 6b) Mouse Scroll Wheel
```
Client → Server:
  MOUSE_SCROLL: scroll_x=0, scroll_y=120
  [4 bytes payload]
  
  Typical scroll_y values:
    +120 = scroll up one notch
    -120 = scroll down one notch
  
  Horizontal scroll (trackpads/mice):
    scroll_x: ±120 per gesture
```

### 7) Keyboard Events
```
Client → Server:
  KEY_EVENT: key_code=0x0301 (A), pressed=1  [3 bytes]
  KEY_EVENT: key_code=0x0301, pressed=0      [3 bytes]
  TEXT_INPUT: text_len=5, "Hello"            [7 bytes]
  
  (Key presses might batch if within 10ms window)
  
Server backend maps:
  0x0301 → Linux evdev KEY_A (30)
  0x0301 → Windows VK_A (0x41)
  0x0301 → macOS kVK_ANSI_A (0x00)
```

### 8) Server Sends Haptic Feedback
```
Server → Client:
  FEEDBACK_HAPTIC:
    effect_id=1
    amplitude=40000
    duration_ms=100
    frequency_hz=100
```

### 9) Graceful Session Close
```
Client → Server:
  SESSION_END:
    reason_code=0x0001 (client logout)
    reason="User logout"

Server processes and expires session
```

---

## Implementation Guide

### Client Implementation Checklist

**Initialization:**
- [ ] Create UDP socket, bind to ephemeral port
- [ ] Send `HELLO` to server (broadcast or known IP)
- [ ] Parse `WELCOME`, store session_id and device_id mappings
- [ ] Initialize event buffer for batching (10ms timer)

**Event Loop:**
- [ ] Read user input (gamepad, keyboard, mouse)
- [ ] Map physical controls to protocol codes (0x0001–0x03FF)
- [ ] Buffer events in batch queue
- [ ] Flush on: timer (10ms), size (1200B), or explicit trigger
- [ ] Send batched events as `BATCH` message or individual events

**Keepalive:**
- [ ] Send `PING` every 2 seconds
- [ ] Handle `PONG` responses (optionally measure RTT)
- [ ] Detect server timeout (>10s no PONG → reconnect)

**Cleanup:**
- [ ] Send `SESSION_END` on app exit
- [ ] Close UDP socket

**Optimizations:**
- [ ] Use platform-native timers for 10ms batching
- [ ] Pre-allocate packet buffers (1200 bytes)
- [ ] Avoid heap allocations in hot path

---

### Server Implementation Checklist

**Initialization:**
- [ ] Bind UDP socket to port 9775
- [ ] Initialize session registry (session_id → client state)
- [ ] Create control code → OS-specific code lookup tables
- [ ] Initialize virtual device manager (uinput/Windows/macOS)

**Message Handling:**
- [ ] Parse common header (12 bytes)
- [ ] Dispatch by msg_type (0x01–0x52)
- [ ] Handle `HELLO`: validate caps, send `WELCOME`
- [ ] Handle `CONNECT`: create virtual device, assign device_id
- [ ] Handle input events: map protocol codes → OS codes, inject
- [ ] Handle `BATCH`: parse event_count, process sequentially
- [ ] Handle `PING`: reply with `PONG` (echo timestamp if present)

**Session Management:**
- [ ] Track last_seen timestamp per session
- [ ] Expire sessions after 30s idle (no PING)
- [ ] Send `SESSION_END` on cleanup
- [ ] Clean up virtual devices on disconnect

**Rate Limiting:**
- [ ] Track packets/sec per source IP
- [ ] Send `ERROR RateLimited` if >250 pps
- [ ] Optional: token bucket per session

**Control Code Mapping:**
```python
# Example Python lookup table
PROTOCOL_TO_LINUX_EVDEV = {
    0x0001: 304,  # BTN_SOUTH (A button)
    0x0301: 30,   # KEY_A
    0x0339: 28,   # KEY_ENTER
    # ... full mapping
}

PROTOCOL_TO_WINDOWS_VK = {
    0x0301: 0x41,  # VK_A
    0x0339: 0x0D,  # VK_RETURN
    # ... full mapping
}
```

**Optimizations:**
- [ ] Use asyncio/trio for event loop (Python)
- [ ] Pre-parse common header before dispatch
- [ ] Pool packet buffers to avoid allocations
- [ ] Batch OS injections (e.g., uinput write_event)

---

## Testing Recommendations

1. **Packet Analysis:**
   - Use Wireshark with custom Lua dissector for `udp.port == 9775`
   - Verify little-endian encoding, control codes, batching

2. **Latency Testing:**
   - Enable timestamps (`flags & 0x0002`)
   - Measure PING/PONG RTT (expect <5ms on LAN)
   - Measure input→response latency (expect <15ms with batching)

3. **Stress Testing:**
   - Send 250 pps sustained (rate limit test)
   - Send rapid button presses (batching efficiency test)
   - Send malformed packets (error handling test)

4. **Fuzzing:**
   - Test overlong strings (name_len=255, text_len=65535)
   - Test invalid control codes (0xFFFF)
   - Test truncated packets (partial headers)

5. **Cross-Platform:**
   - Verify control code mapping on Linux, Windows, macOS
   - Test keyboard layout independence (protocol codes, not scancodes)

---

## Performance Benchmarks (Expected)

| Scenario                     | Latency   | Throughput | Notes                    |
|------------------------------|-----------|------------|--------------------------|
| Single button press          | 2-5ms     | -          | No batching              |
| Batched events (10ms window) | 10-15ms   | 100-250pps | 70-90% overhead reduction|
| PING/PONG RTT (LAN)          | <5ms      | -          | Typical home network     |
| Analog stick movement        | 10-15ms   | 60-100 Hz  | With batching            |
| Keyboard typing              | 10-20ms   | 10-50 cps  | Per-character, batched   |

---

## Future Enhancements (Out of Scope for v0.3)

- **Compression:** Zlib/LZ4 for large TEXT_INPUT or batch payloads
- **Encryption:** DTLS wrapper for untrusted networks
- **Multicast discovery:** Efficient LAN server discovery without broadcast
- **Extended TLVs:** Gyro/accelerometer data, touchpad pressure maps
- **Reliability layer:** Selective retransmission for critical messages
- **Vendor extensions:** Custom control codes (0x1000+) for specialized devices

---

## Revision History

| Version | Date       | Changes                                           |
|---------|------------|---------------------------------------------------|
| 0.1     | 2026-01-08 | Initial draft with basic message types            |
| 0.2     | 2026-01-09 | Added batching, platform-independent control codes|
| 0.3     | 2026-01-10 | Finalized with diagrams, tables, full reference   |

---
