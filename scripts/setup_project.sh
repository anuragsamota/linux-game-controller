#!/usr/bin/env bash
set -euo pipefail

# Bootstrap the project from a public git repository.
# - Checks for git and python3
# - Clones the repo if target directory is absent
# - Creates a Python virtual environment
# - Installs dependencies from requirements.txt (if present)
#
# Usage examples:
#   ./scripts/setup_project.sh https://github.com/anuragsamota/linux-game-controller.git my-project
#   ./scripts/setup_project.sh https://github.com/anuragsamota/linux-game-controller.git      # clones into repo name
#   ./scripts/setup_project.sh                            # uses default repo URL and directory name
#
# Optional env vars:
#   PYTHON_BIN=python3.11   # choose a specific python
#   VENV_NAME=.venv         # virtualenv directory name

DEFAULT_REPO="https://github.com/anuragsamota/linux-game-controller.git"
REPO_URL=${1:-$DEFAULT_REPO}
TARGET_DIR=${2:-}
PYTHON_BIN=${PYTHON_BIN:-python3}
VENV_NAME=${VENV_NAME:-.venv}

require() {
  if ! command -v "$1" >/dev/null 2>&1; then
    echo "[ERROR] Missing required command: $1" >&2
    exit 1
  fi
}

abort() {
  echo "[ERROR] $1" >&2
  exit 1
}

main() {
  require git
  require "$PYTHON_BIN"

  if [ "$REPO_URL" = "$DEFAULT_REPO" ]; then
    echo "[INFO] No repo URL provided; using default: $DEFAULT_REPO"
  fi

  if [ -z "$TARGET_DIR" ]; then
    TARGET_DIR=$(basename "$REPO_URL" .git)
  fi

  if [ -d "$TARGET_DIR" ]; then
    echo "[INFO] Target directory '$TARGET_DIR' already exists. Skipping clone."
  else
    echo "[INFO] Cloning $REPO_URL -> $TARGET_DIR"
    git clone "$REPO_URL" "$TARGET_DIR"
  fi

  cd "$TARGET_DIR"

  echo "[INFO] Creating virtual environment: $VENV_NAME using $PYTHON_BIN"
  "$PYTHON_BIN" -m venv "$VENV_NAME"
  # shellcheck disable=SC1090
  source "$VENV_NAME/bin/activate"

  echo "[INFO] Python: $(python -V)"
  echo "[INFO] PIP: $(pip -V)"

  if [ -f requirements.txt ]; then
    echo "[INFO] Installing requirements.txt"
    pip install --upgrade pip
    pip install -r requirements.txt
  else
    echo "[WARN] requirements.txt not found. Skipping dependency install."
  fi

  echo "[INFO] Setup complete. Activate env with: source $TARGET_DIR/$VENV_NAME/bin/activate"

  # Launch interactive controller manager
  if [ -x ./scripts/ctl.sh ]; then
    echo "[INFO] Launching interactive controller manager (./scripts/ctl.sh)"
    exec ./scripts/ctl.sh
  else
    echo "[WARN] scripts/ctl.sh not found or not executable. Start manually when available: ./scripts/ctl.sh"
  fi
}

main "$@"
