#!/bin/bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$(readlink -f "${BASH_SOURCE[0]}")")" && pwd)"
cd "$SCRIPT_DIR"

# 激活虚拟环境（如果存在）
if [ -f "$SCRIPT_DIR/venv/bin/activate" ]; then
    source "$SCRIPT_DIR/venv/bin/activate"
fi

CONFIG_FILE="${1:-$SCRIPT_DIR/examples/services.yaml}"

echo "启动服务管理器..."
nohup python3 -c "
import importlib
import os
import sys
sys.path.insert(0, os.path.abspath('$SCRIPT_DIR'))
mod = importlib.import_module('backend.service_compose')
sys.argv = ['service_compose', 'start', '--config', '$CONFIG_FILE', '--daemon']
mod.main()
" &>/dev/null &

echo "启动后端 API..."
nohup python3 -m backend.app --config "$CONFIG_FILE" --host 0.0.0.0 --port 8080 &>/dev/null &

echo "所有服务已启动"
echo "  API 地址: http://0.0.0.0:8080"
echo "  API 文档: http://0.0.0.0:8080/api/docs"
