# Development Guide

Platform support: Linux is fully supported via `uinput`. The registry is now platform-aware so a Windows backend (e.g., ViGEm/vJoy) can be added without changing the server protocol.

Code organization:
- `server.py` handles WebSocket transport and message parsing
- Platform backends live under `platforms/<os>/devices/` (Linux uses uinput; Windows stubbed)
- Shared interfaces are in `devices/base_controller.py`

## Prerequisites
- Python 3.13+
- Linux with `uinput`
- Virtualenv at `.venv`

## Setup
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Run Servers (individually)
- WebSocket server only:
```bash
PYTHONPATH=. python -m src.controller_server.main --host 0.0.0.0 --port 8765
```
[WEB] python3: can't open file '/home/anurag/Downloads/librepad-server/web_server.py': [Errno 2] No such file or directory

- Static web server only (serves ./web):
```bash
python -m http.server 8000 --directory web
```

## Using Helper Scripts
- Interactive menu:
```bash
./ctl.sh
```
- Direct commands:
```bash
./init.sh
./ctl.sh start
./reset.sh
```

## Environment Variables
- `WS_HOST` (default: 0.0.0.0)
- `WS_PORT` (default: 8765)
- `WEB_PORT` (default: 8000)

## Logging
Server logs use `[timestamp] LEVEL logger: message` format. Normal shutdown logs are clean and do not print tracebacks.

## Code Structure
- `src/controller_server/server.py`: WebSocket server and device handling
- `src/controller_server/main.py`: CLI entrypoint
- `web/`: static client files (JS/CSS/HTML)
- Root scripts (`init.sh`, `ctl.sh`, `start.sh`, `reset.sh`): bash scripts for env and runtime management
