# User Guide

This guide covers setup and usage of the virtual controller.

## 1. Initialize the Environment
This requires sudo. It will:
- Load `uinput` kernel module
- Ensure user is in the `input` group
- Install a udev rule for `/dev/uinput` permissions

```bash
./init.sh
```

If you see permission errors, re-login after running the script.

## 2. Start the Servers
Starts the WebSocket controller server and static web server.

```bash
./ctl.sh start
```

Default ports:
- WebSocket: `8765`
- Web UI: `8000`

Ports automatically fallback to the next free one within 20 tries. Override with:
```bash
WS_PORT=9000 WEB_PORT=8088 ./ctl.sh start
```

## 3. Use the Web UI
Open the URL printed by `ctl.sh` (typically `http://localhost:8000`).
- The client auto-detects the server hostname from the page URL.
- Connect a device (`standard`) and send `button`/`axis` events.

## 4. Reset the Environment
To revert uinput setup and permissions:
```bash
./reset.sh
```

## Notes
- The server handles clean disconnects gracefully — no terminal exceptions on shutdown.
- Device names in uinput are immutable; set via the `connect` event.
