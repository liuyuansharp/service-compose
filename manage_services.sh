#!/bin/bash
# 服务管理命令封装（兼容 .so 编译模式）
# 注意: 此脚本已由 service_compose 替代，保留仅为向后兼容
SCRIPT_DIR="$(cd "$(dirname "$(readlink -f "${BASH_SOURCE[0]}")")" && pwd)"
cd "$SCRIPT_DIR"

if [ -f "$SCRIPT_DIR/venv/bin/activate" ]; then
    source "$SCRIPT_DIR/venv/bin/activate"
fi

SERVICE_COMPOSE_DIR="$SCRIPT_DIR" python3 - "$@" << 'PY'
import importlib
import os
import sys

script_dir = os.environ.get("SERVICE_COMPOSE_DIR") or os.getcwd()
sys.path.insert(0, script_dir)

mod = importlib.import_module('backend.service_compose')
sys.argv = ['service_compose'] + sys.argv[1:]
mod.main()
PY
