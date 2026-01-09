# Linux Game Controller (Virtual)

A modern, customizable virtual gamepad system with a React-based web interface for controlling Linux games over WebSocket.

## Features

- **Modern Web Client**: Built with Vite, React, and Tailwind CSS
- **Multiple Controller Configurations**: Create and save unlimited custom layouts
- **Edit Mode**: Drag, resize, add, and remove buttons in real-time
- **Responsive Design**: Optimized for mobile landscape mode with touch support
- **WebSocket Communication**: Low-latency input transmission
- **Import/Export**: Share configurations as JSON files
- **Default Templates**: Pre-configured Standard Gamepad and Minimal layouts
- **Joystick Support**: Analog stick controls with visual feedback

## Requirements
- Linux with `uinput` support
- Python 3.13+
- Node.js 18+ (for web client development)
- Virtual environment in `.venv`
- Sudo privileges (for initialization)

## Quickstart
Clone and prepare the project in the current directory, then auto-launch the interactive CLI:

```bash
curl -sSL https://raw.githubusercontent.com/anuragsamota/linux-game-controller/master/setup_project.sh | bash
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

# 4) Install web client dependencies
cd web
npm install
cd ..

# 5) Initialize controller environment (requires sudo)
./init.sh

# 6) Start servers (WebSocket + Web UI)
./ctl.sh start
```

After setup completes (one‑liner or manual), the interactive CLI (`ctl.sh`) lets you initialize the environment or start the servers.

Environment variables:
- `WS_HOST` (default: `0.0.0.0`)
- `WS_PORT` (default: `8765`, with port fallback scanning)
- `WEB_PORT` (default: `8000`, with port fallback scanning)

Example:
```bash
WS_PORT=9000 WEB_PORT=8088 ./ctl.sh start
```

## Scripts Overview
- `ctl.sh`: Interactive, colorful CLI to run `init`, `start`, `reset`.
- `init.sh`: Sets up `uinput`, `input` group membership, and udev rules.
- `start.sh`: Activates `.venv` and runs WebSocket and Vite dev servers.
- `build.sh`: Builds production-ready web client.
- `reset.sh`: Reverts initialization (group, rules, module).
- `setup_project.sh`: Bootstrap script to clone, setup venv, and launch CLI.

## Documentation
- User Guide: [docs/UserGuide.md](docs/UserGuide.md)
- Developer Guide: [docs/Development.md](docs/Development.md)
- Web Client Development: [docs/WebClientDevelopment.md](docs/WebClientDevelopment.md)
- WebSocket API: [docs/WebSocketAPI.md](docs/WebSocketAPI.md)
- Troubleshooting: [docs/Troubleshooting.md](docs/Troubleshooting.md)

## Architecture
- WebSocket server: forwards `button` and `axis` events to virtual devices.
- Device registry: manages acquisition/release of uinput-backed devices.
- Web client: sends controller/touchpad events; auto-detects server hostname.

## Graceful Shutdown
Ctrl+C cleanly stops servers. The WebSocket server suppresses tracebacks on shutdown.
