# Linux Game Controller (Virtual)

A lightweight system to control a Linux virtual gamepad over WebSocket/WebRTC from a web UI.

- Python asyncio WebSocket server for input events
- Static web client with auto-hostname detection and performance optimizations
- Helper scripts to initialize uinput, start services, and reset environment

## Requirements
- Linux with `uinput` support
- Python 3.13+
- Virtual environment in `.venv`
- Sudo privileges (for initialization)

## Quickstart
Clone and prepare the project in the current directory, then auto-launch the interactive CLI:

```bash
curl -sSL https://raw.githubusercontent.com/anuragsamota/linux-game-controller/master/scripts/setup_project.sh \
	| bash -s -- https://github.com/anuragsamota/linux-game-controller.git
```

### Manual setup (full)
Perform a clean local setup manually:

```bash
# 1) Clone the repo
git clone https://github.com/anuragsamota/linux-game-controller.git
cd linux-game-controller

# 2) Create and activate virtual environment
python3 -m venv .venv
source .venv/bin/activate

# 3) Install dependencies
pip install --upgrade pip
pip install -r requirements.txt

# 4) Initialize controller environment (requires sudo)
./scripts/init.sh

# 5) Start servers (WebSocket + Web UI)
./scripts/ctl.sh start
```

After setup completes (one‑liner or manual), the interactive CLI (`scripts/ctl.sh`) lets you initialize the environment or start the servers.

Environment variables:
- `WS_HOST` (default: `0.0.0.0`)
- `WS_PORT` (default: `8765`, with port fallback scanning)
- `WEB_PORT` (default: `8000`, with port fallback scanning)

Example:
```bash
WS_PORT=9000 WEB_PORT=8088 ./scripts/ctl.sh start
```

## Scripts Overview
- `scripts/ctl.sh`: Interactive, colorful CLI to run `init`, `start`, `reset`.
- `scripts/init.sh`: Sets up `uinput`, `input` group membership, and udev rules.
- `scripts/start.sh`: Activates `.venv` and runs WebSocket and static web servers.
- `scripts/reset.sh`: Reverts initialization (group, rules, module).

## Documentation
- User Guide: [docs/UserGuide.md](docs/UserGuide.md)
- Developer Guide: [docs/Development.md](docs/Development.md)
- WebSocket API: [docs/WebSocketAPI.md](docs/WebSocketAPI.md)
- Troubleshooting: [docs/Troubleshooting.md](docs/Troubleshooting.md)

## Architecture
- WebSocket server: forwards `button` and `axis` events to virtual devices.
- Device registry: manages acquisition/release of uinput-backed devices.
- Web client: sends controller/touchpad events; auto-detects server hostname.

## Graceful Shutdown
Ctrl+C cleanly stops servers. The WebSocket server suppresses tracebacks on shutdown.
