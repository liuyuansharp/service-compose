#!/bin/bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$(readlink -f "${BASH_SOURCE[0]}")")" && pwd)"
cd "$SCRIPT_DIR"

# 激活虚拟环境（如果存在）
if [ -f "$SCRIPT_DIR/venv/bin/activate" ]; then
    source "$SCRIPT_DIR/venv/bin/activate"
fi

CONFIG_FILE="${1:-$SCRIPT_DIR/examples/services.yaml}"

echo "停止所有服务..."
python3 -c "
import importlib
import os
import sys
sys.path.insert(0, os.path.abspath('$SCRIPT_DIR'))
mod = importlib.import_module('manage_services')
sys.argv = ['manage_services', 'stop', '--config', '$CONFIG_FILE']
mod.main()
" 2>/dev/null || true

# 停止后端 API 进程
pkill -f "backend.app" 2>/dev/null || true

echo "所有服务已停止"
