#!/usr/bin/env bash
set -euo pipefail

# Build the React web client for production

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WEB_DIR="${ROOT_DIR}/web"

echo "[INFO] Building web client for production..."

cd "${WEB_DIR}"

# Check for pnpm first, fallback to npm
if command -v pnpm >/dev/null 2>&1; then
    PKG_MANAGER="pnpm"
elif command -v npm >/dev/null 2>&1; then
    PKG_MANAGER="npm"
else
    echo "[ERROR] Neither pnpm nor npm found. Please install Node.js package manager." >&2
    exit 1
fi

echo "[INFO] Using package manager: ${PKG_MANAGER}"

if [ ! -d "node_modules" ]; then
    echo "[INFO] Installing dependencies..."
    ${PKG_MANAGER} install
fi

echo "[INFO] Running production build..."
${PKG_MANAGER} run build

echo ""
echo "=========================================="
echo "✅ Build Complete!"
echo "=========================================="
echo "Output directory: ${WEB_DIR}/dist"
echo ""
echo "To serve production build:"
echo "  cd ${WEB_DIR}/dist && python3 -m http.server 8000"
echo "=========================================="
