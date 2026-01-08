#!/usr/bin/env bash
set -euo pipefail

# Start both the WebSocket controller server and the static web server.
# - WebSocket server (game controller): src/controller_server/main.py
# - Web client server (static files): web_server.py

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_DIR="${ROOT_DIR}/.venv"
WS_HOST="${WS_HOST:-0.0.0.0}"
WS_PORT="${WS_PORT:-8765}"
WEB_PORT="${WEB_PORT:-8000}"
MAX_PORT_SCAN=20
INPUT_GROUP="input"
UINPUT_RULE="/etc/udev/rules.d/99-uinput.rules"

require() {
	if ! command -v "$1" >/dev/null 2>&1; then
		echo "[ERROR] Missing required command: $1" >&2
		exit 1
	fi
}

activate_venv() {
	if [ -f "${VENV_DIR}/bin/activate" ]; then
		echo "[INFO] Activating virtual environment at ${VENV_DIR}"
		source "${VENV_DIR}/bin/activate"
	else
		echo "[ERROR] Virtual environment not found at ${VENV_DIR}" >&2
		echo "        Please run: python3 -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt" >&2
		exit 1
	fi
}

start_ws_server() {
	echo "[INFO] Starting WebSocket controller server on ${WS_HOST}:${WS_PORT}" 
	cd "${ROOT_DIR}"
	source "${VENV_DIR}/bin/activate"
	PYTHONPATH="${ROOT_DIR}" exec python3 -m src.controller_server.main --host "${WS_HOST}" --port "${WS_PORT}" 
}

start_web_server() {
	echo "[INFO] Serving web client on http://localhost:${WEB_PORT}" 
	cd "${ROOT_DIR}"
	source "${VENV_DIR}/bin/activate"
	PYTHONPATH="${ROOT_DIR}" exec python3 -m http.server "${WEB_PORT}" --directory "${ROOT_DIR}/web"
}

check_controller_env() {
	local user="${SUDO_USER:-${USER}}"

	if [ ! -e /dev/uinput ]; then
		echo "[ERROR] /dev/uinput not found. Run ./init.sh (requires sudo)." >&2
		exit 1
	fi

	# Check permissions FIRST (more specific error)
	local perms
	perms=$(stat -c "%a %G" /dev/uinput 2>/dev/null || true)
	if [ -n "${perms}" ]; then
		local mode group
		mode=$(echo "${perms}" | awk '{print $1}')
		group=$(echo "${perms}" | awk '{print $2}')
		if [ "${group}" != "${INPUT_GROUP}" ] || [ "${mode}" != "660" -a "${mode}" != "0660" ]; then
			echo "[ERROR] /dev/uinput has permissions '${perms}' (expected 660 ${INPUT_GROUP})." >&2
			echo "        Run ./init.sh to fix permissions." >&2
			if ! id -nG "${user}" | grep -qw "${INPUT_GROUP}"; then
				echo "        Note: You are also not in '${INPUT_GROUP}' group. After init.sh, re-login." >&2
			fi
			exit 1
		fi
	fi

	# Check group membership
	if ! id -nG "${user}" | grep -qw "${INPUT_GROUP}"; then
		echo "[ERROR] User '${user}' is not in '${INPUT_GROUP}' group." >&2
		echo "        Run ./init.sh and re-login." >&2
		exit 1
	fi

	if [ ! -f "${UINPUT_RULE}" ]; then
		echo "[WARN] udev rule ${UINPUT_RULE} not found; /dev/uinput permissions may reset on reboot." >&2
	fi
}

is_port_free() {
	local port=$1
	if command -v ss >/dev/null 2>&1; then
		! ss -ltn | awk '{print $4}' | grep -E "[:.]${port}$" >/dev/null 2>&1
	else
		! lsof -Pi :"${port}" -sTCP:LISTEN -t >/dev/null 2>&1
	fi
}

pick_port() {
	local base=$1
	local picked=$base
	for _ in $(seq 0 "${MAX_PORT_SCAN}"); do
		if is_port_free "${picked}"; then
			echo "${picked}"
			return 0
		fi
		picked=$((picked + 1))
	done
	echo "[ERROR] No free port found starting at ${base} within ${MAX_PORT_SCAN} attempts" >&2
	exit 1
}

main() {
	require python3
	activate_venv
	check_controller_env

	if ! command -v ss >/dev/null 2>&1 && ! command -v lsof >/dev/null 2>&1; then
		echo "[WARN] Neither 'ss' nor 'lsof' found; port availability checks disabled"
	else
		WS_PORT=$(pick_port "${WS_PORT}")
		WEB_PORT=$(pick_port "${WEB_PORT}")
	fi

	trap 'echo "[INFO] Stopping servers..."; jobs -p | xargs -r kill' INT TERM EXIT

	start_ws_server 2>&1 | sed 's/^/[WS ] /' &
	WS_PID=$!

	start_web_server 2>&1 | sed 's/^/[WEB] /' &
	WEB_PID=$!

	echo "[INFO] Servers running (WS PID=${WS_PID}, WEB PID=${WEB_PID})"
	echo ""
	echo "=========================================="
	echo "🎮 Controller Access URLs:"
	echo "=========================================="
	
	# Get all network interfaces and their IPs
	if command -v ip >/dev/null 2>&1; then
		# Use ip command to get all IPv4 addresses
		while IFS= read -r line; do
			iface=$(echo "$line" | awk '{print $2}')
			ip_addr=$(echo "$line" | awk '{print $4}' | cut -d'/' -f1)
			if [ -n "$ip_addr" ] && [ "$ip_addr" != "127.0.0.1" ]; then
				echo "  📡 $iface: http://$ip_addr:${WEB_PORT}"
			fi
		done < <(ip -4 addr show | grep -E "^\s*inet " | grep -v "127.0.0.1")
	elif command -v ifconfig >/dev/null 2>&1; then
		# Fallback to ifconfig
		while IFS= read -r line; do
			iface=$(echo "$line" | awk '{print $1}' | tr -d ':')
			ip_addr=$(echo "$line" | grep -oE 'inet [0-9.]+' | awk '{print $2}')
			if [ -n "$ip_addr" ] && [ "$ip_addr" != "127.0.0.1" ]; then
				echo "  📡 $iface: http://$ip_addr:${WEB_PORT}"
			fi
		done < <(ifconfig | grep -E "^[a-z]|inet ")
	fi
	
	# Always show localhost
	echo "  🏠 Localhost: http://localhost:${WEB_PORT}"
	echo "  🏠 Loopback: http://127.0.0.1:${WEB_PORT}"
	echo ""
	echo "WebSocket Endpoint: ws://${WS_HOST}:${WS_PORT}"
	echo "=========================================="
	echo "[INFO] Press Ctrl+C to stop both servers."

	wait
}

main "$@"
