#!/usr/bin/env bash
set -euo pipefail

# 🎮 LibrePad Server Manager
# Beautiful, colorful, interactive CLI wrapper

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SCRIPTS_DIR="${ROOT_DIR}/scripts/linux"

# Double Ctrl+C handling
CTRL_C_COUNT=0
trap_handler() {
  CTRL_C_COUNT=$((CTRL_C_COUNT + 1))
  if [ $CTRL_C_COUNT -ge 2 ]; then
    echo -e "\n${GREEN}${ICON_CHECK} Goodbye!${RESET}\n"
    exit 0
  else
    echo -e "\n${YELLOW}${ICON_WARN} Press Ctrl+C again to exit${RESET}"
    sleep 2
    CTRL_C_COUNT=0  # Reset counter after timeout
  fi
}
trap trap_handler INT

# Color definitions
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
MAGENTA='\033[0;35m'
CYAN='\033[0;36m'
WHITE='\033[1;37m'
BOLD='\033[1m'
DIM='\033[2m'
RESET='\033[0m'

# Emoji/Icons
ICON_CONTROLLER="🎮"
ICON_ROCKET="🚀"
ICON_GEAR="⚙️"
ICON_TRASH="🗑️"
ICON_CHECK="✓"
ICON_CROSS="✗"
ICON_WARN="⚠️"
ICON_INFO="ℹ️"

print_header() {
  echo -e "${CYAN}${BOLD}"
  cat <<'EOF'
╔═══════════════════════════════════════════════════════╗
║                                                       ║
║   🎮  LIBREPAD SERVER MANAGER  🎮                    ║
║                                                       ║
║   Control your Linux virtual gamepad with ease       ║
║                                                       ║
╚═══════════════════════════════════════════════════════╝
EOF
  echo -e "${RESET}"
}

print_menu() {
  echo -e "${WHITE}${BOLD}Available Commands:${RESET}\n"
  
  echo -e "  ${GREEN}${BOLD}1)${RESET} ${ICON_GEAR}  ${CYAN}init${RESET}   ${DIM}→${RESET} Initialize controller environment"
  echo -e "     ${DIM}├─ Load uinput kernel module${RESET}"
  echo -e "     ${DIM}├─ Create/join input group${RESET}"
  echo -e "     ${DIM}└─ Setup udev permissions${RESET}"
  echo ""
  
  echo -e "  ${GREEN}${BOLD}2)${RESET} ${ICON_ROCKET}  ${CYAN}start${RESET}  ${DIM}→${RESET} Start WebSocket + Web servers"
  echo -e "     ${DIM}├─ Check environment setup${RESET}"
  echo -e "     ${DIM}├─ Auto-detect free ports${RESET}"
  echo -e "     ${DIM}└─ Launch controller service${RESET}"
  echo ""
  
  echo -e "  ${GREEN}${BOLD}3)${RESET} ${ICON_TRASH}  ${CYAN}reset${RESET}  ${DIM}→${RESET} Revert environment changes"
  echo -e "     ${DIM}├─ Remove user from input group${RESET}"
  echo -e "     ${DIM}├─ Delete udev rules${RESET}"
  echo -e "     ${DIM}└─ Unload uinput module${RESET}"
  echo ""
  
  echo -e "  ${GREEN}${BOLD}4)${RESET} ${ICON_INFO}  ${CYAN}help${RESET}   ${DIM}→${RESET} Show detailed help"
  echo -e "  ${GREEN}${BOLD}0)${RESET} ${ICON_CROSS}  ${CYAN}exit${RESET}   ${DIM}→${RESET} Exit this menu"
  echo ""
}

print_help() {
  print_header
  echo -e "${WHITE}${BOLD}Usage:${RESET}"
  echo -e "  ${CYAN}./ctl.sh${RESET} ${YELLOW}<command>${RESET}\n"
  
  echo -e "${WHITE}${BOLD}Commands:${RESET}\n"
  
  echo -e "  ${CYAN}${BOLD}init${RESET}"
  echo -e "    ${DIM}Initialize the controller environment (requires sudo)${RESET}"
  echo -e "    ${DIM}This sets up uinput module, user groups, and permissions${RESET}"
  echo -e "    ${GREEN}Example:${RESET} ./ctl.sh init\n"
  
  echo -e "  ${CYAN}${BOLD}start${RESET}"
  echo -e "    ${DIM}Start the WebSocket controller server and web client${RESET}"
  echo -e "    ${DIM}Automatically finds free ports and validates setup${RESET}"
  echo -e "    ${GREEN}Example:${RESET} ./ctl.sh start"
  echo -e "    ${GREEN}Example:${RESET} WS_PORT=9000 WEB_PORT=8080 ./ctl.sh start\n"
  
  echo -e "  ${CYAN}${BOLD}reset${RESET}"
  echo -e "    ${DIM}Revert all environment changes (requires sudo)${RESET}"
  echo -e "    ${DIM}Removes user from group, deletes rules, unloads module${RESET}"
  echo -e "    ${GREEN}Example:${RESET} ./ctl.sh reset\n"
  
  echo -e "  ${CYAN}${BOLD}help${RESET}"
  echo -e "    ${DIM}Show this help message${RESET}\n"
  
  echo -e "${WHITE}${BOLD}Environment Variables:${RESET}"
  echo -e "  ${YELLOW}WS_HOST${RESET}    ${DIM}WebSocket bind address (default: 0.0.0.0)${RESET}"
  echo -e "  ${YELLOW}WS_PORT${RESET}    ${DIM}WebSocket port (default: 8765)${RESET}"
  echo -e "  ${YELLOW}WEB_PORT${RESET}   ${DIM}Web server port (default: 8000)${RESET}\n"
}

require_script() {
  if [ ! -x "$1" ]; then
    echo -e "${RED}${BOLD}${ICON_CROSS} ERROR:${RESET} Script not found or not executable: ${YELLOW}$1${RESET}" >&2
    exit 1
  fi
}

run_command() {
  local cmd=$1
  shift || true
  
  case "$cmd" in
    init)
      echo -e "\n${BLUE}${ICON_GEAR}  Running initialization...${RESET}\n"
      require_script "${SCRIPTS_DIR}/init.sh"
      bash "${SCRIPTS_DIR}/init.sh" "$@"
      echo -e "\n${DIM}Press Enter to return to menu...${RESET}"
      read -r
      return 0
      ;;
    start)
      echo -e "\n${BLUE}${ICON_ROCKET}  Starting servers...${RESET}\n"
      require_script "${SCRIPTS_DIR}/start.sh"
      bash "${SCRIPTS_DIR}/start.sh" "$@"
      echo -e "\n${DIM}Press Enter to return to menu...${RESET}"
      read -r
      return 0
      ;;
    reset)
      echo -e "\n${BLUE}${ICON_TRASH}  Resetting environment...${RESET}\n"
      require_script "${SCRIPTS_DIR}/reset.sh"
      bash "${SCRIPTS_DIR}/reset.sh" "$@"
      echo -e "\n${DIM}Press Enter to return to menu...${RESET}"
      read -r
      return 0
      ;;
    help|-h|--help)
      print_help
      return 0
      ;;
    exit|quit|q)
      echo -e "${GREEN}${ICON_CHECK} Goodbye!${RESET}"
      exit 0
      ;;
    *)
      echo -e "${RED}${BOLD}${ICON_CROSS} Unknown command:${RESET} ${YELLOW}$cmd${RESET}\n" >&2
      print_help
      exit 1
      ;;
  esac
}

interactive_menu() {
  while true; do
    clear
    print_header
    print_menu
    
    echo -e -n "${WHITE}${BOLD}Enter your choice [0-4]:${RESET} "
    read -r choice
    
    case "$choice" in
      1|init)
        run_command init
        ;;
      2|start)
        run_command start
        ;;
      3|reset)
        run_command reset
        ;;
      4|help)
        clear
        print_help
        echo -e -n "\n${DIM}Press Enter to return to menu...${RESET}"
        read -r
        ;;
      0|exit|quit|q)
        echo -e "\n${GREEN}${ICON_CHECK} Goodbye!${RESET}\n"
        exit 0
        ;;
      *)
        echo -e "\n${RED}${ICON_CROSS} Invalid choice. Please select 0-4.${RESET}"
        sleep 2
        ;;
    esac
  done
}

main() {
  if [ $# -lt 1 ]; then
    # No arguments - show interactive menu
    interactive_menu
  else
    # Direct command execution
    run_command "$@"
  fi
}

main "$@"
