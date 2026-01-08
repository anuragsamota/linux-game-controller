#!/usr/bin/env bash
set -euo pipefail

# Revert controller environment setup
# - Removes udev rule for uinput (if installed)
# - Removes current user from input group (if present)
# - Attempts to unload uinput module
# Note: Does NOT delete the input group

TARGET_USER="${SUDO_USER:-${USER}}"
TARGET_GROUP="input"
UINPUT_RULE="/etc/udev/rules.d/99-uinput.rules"

require() {
	if ! command -v "$1" >/dev/null 2>&1; then
		echo "[ERROR] Missing required command: $1" >&2
		exit 1
	fi
}

main() {
	echo "[INFO] Reverting controller environment for user: ${TARGET_USER}"

	require sudo
	require udevadm

	echo "[INFO] Requesting sudo privileges"
	sudo -v

	if id -nG "${TARGET_USER}" | grep -qw "${TARGET_GROUP}"; then
		echo "[INFO] Removing user '${TARGET_USER}' from group '${TARGET_GROUP}'"
		sudo gpasswd -d "${TARGET_USER}" "${TARGET_GROUP}" || true
		echo "[NOTE] Log out and back in to apply group removal"
	else
		echo "[OK] User '${TARGET_USER}' is not in group '${TARGET_GROUP}'"
	fi

	if [ -f "${UINPUT_RULE}" ]; then
		echo "[INFO] Removing udev rule ${UINPUT_RULE}"
		sudo rm -f "${UINPUT_RULE}"
		sudo udevadm control --reload-rules
		sudo udevadm trigger --subsystem-match=input
		echo "[OK] udev rules reloaded"
	else
		echo "[OK] No udev rule to remove at ${UINPUT_RULE}"
	fi

	if lsmod | grep -q '^uinput'; then
		echo "[INFO] Attempting to unload uinput module"
		if sudo rmmod uinput 2>/dev/null; then
			echo "[OK] uinput module unloaded"
		else
			echo "[WARN] Could not unload uinput (possibly in use); leave as is"
		fi
	else
		echo "[OK] uinput module not loaded"
	fi

	echo "[DONE] Controller environment reset complete."
}

main "$@"
