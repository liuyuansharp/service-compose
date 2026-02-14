#!/bin/bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$(readlink -f "${BASH_SOURCE[0]}")")" && pwd)"
cd "$SCRIPT_DIR"

# 激活虚拟环境（如果存在）
if [ -f "$SCRIPT_DIR/venv/bin/activate" ]; then
    source "$SCRIPT_DIR/venv/bin/activate"
fi

CONFIG_FILE="${1:-$SCRIPT_DIR/examples/services.yaml}"

python3 -m backend.app --config "$CONFIG_FILE" --host 0.0.0.0 --port 8080
