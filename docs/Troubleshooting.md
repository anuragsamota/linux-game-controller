# Troubleshooting

## ModuleNotFoundError: websockets
Ensure the virtual environment is active and dependencies are installed:
```bash
source .venv/bin/activate
pip install -r requirements.txt
```

## /dev/uinput not found
Run initialization (requires sudo):
```bash
./scripts/init.sh
```
If still missing, ensure `uinput` is available on your kernel and distribution.

## Permission denied on /dev/uinput
- Verify group membership:
```bash
id -nG | grep -qw input || echo "Not in 'input' group"
```
- Re-login after `init.sh` to refresh group membership.
- Confirm udev rule exists: `/etc/udev/rules.d/99-uinput.rules`.

## Port conflicts
Ports auto-scan up to 20 increments. Override defaults:
```bash
WS_PORT=9000 WEB_PORT=8088 ./scripts/ctl.sh start
```

## Clean Shutdown Shows Traceback
Fixed: the server handles `asyncio.CancelledError` and `KeyboardInterrupt` gracefully. Update to the latest code and re-run.

## Web UI cannot connect
- Ensure the web UI uses the same hostname as the page URL (auto-detected).
- Verify WebSocket URL: `ws://<host>:<port>` matches server settings.
- Check firewall rules blocking ports.
