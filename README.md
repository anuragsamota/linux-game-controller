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

```bash
# From project root
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Initialize environment (loads uinput, sets permissions)
./scripts/init.sh

# Start both servers (WebSocket + Web UI)
./scripts/ctl.sh start
# Web UI will be at http://localhost:8000 (default)
```

### Bootstrap via one‑liner
Run the setup script directly from GitHub to clone and prepare the project in the current directory:

```bash
curl -sSL https://raw.githubusercontent.com/<owner>/<repo>/main/scripts/setup_project.sh \
	| bash -s -- https://github.com/<owner>/<repo>.git <target-dir>
```

Notes:
- Replace `<owner>/<repo>` with your repository path.
- Omit `<target-dir>` to use the repo name by default.
- You can select a Python version via `PYTHON_BIN` and virtualenv name via `VENV_NAME`:

```bash
PYTHON_BIN=python3.11 VENV_NAME=.venv \
	curl -sSL https://raw.githubusercontent.com/<owner>/<repo>/main/scripts/setup_project.sh \
	| bash -s -- https://github.com/<owner>/<repo>.git
```

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
