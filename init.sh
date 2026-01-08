#!/usr/bin/env bash
set -euo pipefail

# Initialize environment for virtual controller (uinput)
# - Ensures uinput kernel module is loaded
# - Ensures input group exists and current user is a member
# - Installs udev rule for /dev/uinput permissions

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
  echo "[INFO] Preparing controller environment for user: ${TARGET_USER}" 

  # Check for basic commands
  require sudo
  require getent

  # Ask for sudo once up front (needed for system commands and setup)
  echo "[INFO] Requesting sudo privileges (needed for group/udev setup)" 
  sudo -v

  # Note: modprobe and udevadm are checked when used (will fail clearly if missing)

  # Ensure input group exists
  if getent group "${TARGET_GROUP}" >/dev/null; then
    echo "[OK] Group '${TARGET_GROUP}' already exists"
  else
    echo "[INFO] Creating group '${TARGET_GROUP}'"
    sudo groupadd "${TARGET_GROUP}"
  fi

  # Add user to input group
  if id -nG "${TARGET_USER}" | grep -qw "${TARGET_GROUP}"; then
    echo "[OK] User '${TARGET_USER}' already in group '${TARGET_GROUP}'"
  else
    echo "[INFO] Adding user '${TARGET_USER}' to group '${TARGET_GROUP}'"
    sudo usermod -aG "${TARGET_GROUP}" "${TARGET_USER}"
    echo "[NOTE] You must log out and back in for group changes to take effect"
  fi

  # Install udev rule BEFORE loading module (so it applies on module load)
  RULE_CONTENT='KERNEL=="uinput", MODE:="0660", GROUP:="input"'

  if [ -f "${UINPUT_RULE}" ]; then
    echo "[OK] udev rule already present: ${UINPUT_RULE}"
  else
    echo "[INFO] Installing udev rule at ${UINPUT_RULE}"
    echo "${RULE_CONTENT}" | sudo tee "${UINPUT_RULE}" >/dev/null
    sudo udevadm control --reload-rules
    echo "[OK] udev rules reloaded"
  fi

  # Ensure uinput kernel module is loaded
  module_was_loaded=false
  if lsmod | grep -q 'uinput'; then
    echo "[OK] uinput module already loaded"
    module_was_loaded=true
  else
    echo "[INFO] Loading uinput kernel module"
    sudo modprobe uinput
  fi

  # Trigger udev to apply rules to existing devices
  sudo udevadm trigger --name-match=uinput 2>/dev/null || true
  sleep 1  # Give udev a moment to apply rules

  # Always check and fix permissions
  if [ -e /dev/uinput ]; then
    current_perms=$(stat -c "%a %G" /dev/uinput 2>/dev/null || echo "unknown")
    echo "[INFO] Current /dev/uinput permissions: ${current_perms}"
    
    # Check if permissions are correct
    current_mode=$(stat -c "%a" /dev/uinput 2>/dev/null || echo "000")
    current_group=$(stat -c "%G" /dev/uinput 2>/dev/null || echo "unknown")
    
    if [ "${current_mode}" != "660" ] || [ "${current_group}" != "${TARGET_GROUP}" ]; then
      echo "[INFO] Fixing /dev/uinput permissions (expected: 660 ${TARGET_GROUP})"
      sudo chown root:"${TARGET_GROUP}" /dev/uinput
      sudo chmod 660 /dev/uinput
    else
      echo "[OK] /dev/uinput permissions already correct"
    fi
    
    # Verify final permissions
    final_perms=$(stat -c "%a %G" /dev/uinput 2>/dev/null || echo "unknown")
    echo "[OK] Final /dev/uinput permissions: ${final_perms}"
    ls -l /dev/uinput
  else
    echo "[WARN] /dev/uinput not found. It should appear after loading the module."
  fi

  echo "[DONE] Controller environment initialization complete."
}

main "$@"
