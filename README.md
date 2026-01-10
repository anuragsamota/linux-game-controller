# LibrePad Server

LibrePad Server is a modern, customizable virtual gamepad backend with a React-based web interface for controlling games over WebSocket.
Linux is fully supported today (uinput). The codebase is now structured so a Windows backend (e.g., ViGEm/vJoy) can be added without API changes.

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
- Linux with `uinput` support (Windows backend planned)
- Python 3.13+
- Node.js 18+ (for web client development)
- Virtual environment in `.venv`
- Sudo privileges (for initialization)

## Quickstart
Clone and prepare the project in the current directory, then auto-launch the interactive CLI:

```bash
curl -sSL https://raw.githubusercontent.com/anuragsamota/librepad-server/master/setup_project.sh | bash
```

### Manual setup (full)
Perform a clean local setup manually:

```bash
# 1) Clone the repo
git clone https://github.com/anuragsamota/librepad-server.git
cd librepad-server

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
bash scripts/linux/init.sh

# 6) Start servers (WebSocket + Web UI)
bash scripts/linux/start.sh
```

Or use the interactive manager:

```bash
./librepadserver.sh
```

**Environment variables:**
- `WS_HOST` (default: `0.0.0.0`)
- `WS_PORT` (default: `8765`, with port fallback scanning)
- `WEB_PORT` (default: `8000`, with port fallback scanning)

**Example:**
```bash
WS_PORT=9000 WEB_PORT=8088 bash scripts/linux/start.sh
```

## Scripts Overview

**Linux scripts** (`scripts/linux/`):
- `librepadserver.sh`: Interactive CLI to run init, start, reset.
- `init.sh`: Sets up uinput, input group membership, and udev rules.
- `start.sh`: Activates .venv and runs WebSocket and Web servers.
- `build.sh`: Builds production-ready web client.
- `reset.sh`: Reverts initialization (group, rules, module).

**Windows scripts** (`scripts/windows/`):
- `librepadserver.bat`: Interactive menu (Windows equivalent).
- `init.bat`: No-op on Windows (future ViGEm support).
- `start.bat`: Starts WebSocket and Web servers.
- `build.bat`: Builds production web client.
- `reset.bat`: No-op on Windows.

**Root-level launchers:**
- `librepadserver.sh` / `librepadserver.bat`: Main entry point (platform-aware).
- `setup_project.sh` / `setup_project.bat`: Bootstrap script to clone, setup venv, and launch CLI.

## Documentation
- User Guide: [docs/UserGuide.md](docs/UserGuide.md)
- Developer Guide: [docs/Development.md](docs/Development.md)
- Web Client Development: [docs/WebClientDevelopment.md](docs/WebClientDevelopment.md)
- WebSocket API: [docs/WebSocketAPI.md](docs/WebSocketAPI.md)
- Troubleshooting: [docs/Troubleshooting.md](docs/Troubleshooting.md)

## Architecture
- WebSocket server: transport and message handling for `button`/`axis`/lifecycle events.
- Device registry: manages acquisition/release of virtual devices with platform-aware backends (`src/controller_server/platforms/linux`, Windows stub for future work).
- Web client: sends controller/touchpad events; auto-detects server hostname.

## Graceful Shutdown
Ctrl+C cleanly stops servers. The WebSocket server suppresses tracebacks on shutdown.
