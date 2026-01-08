# Development Guide

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

- Static web server only:
```bash
PYTHONPATH=. python web_server.py --port 8000
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
