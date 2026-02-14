#!/bin/bash
# 服务管理命令封装（兼容 .so 编译模式）
SCRIPT_DIR="$(cd "$(dirname "$(readlink -f "${BASH_SOURCE[0]}")")" && pwd)"
cd "$SCRIPT_DIR"

if [ -f "$SCRIPT_DIR/venv/bin/activate" ]; then
    source "$SCRIPT_DIR/venv/bin/activate"
fi

MANAGE_SERVICES_DIR="$SCRIPT_DIR" python3 - "$@" << 'PY'
import importlib
import os
import sys

script_dir = os.environ.get("MANAGE_SERVICES_DIR") or os.getcwd()
sys.path.insert(0, script_dir)

mod = importlib.import_module('manage_services')
sys.argv = ['manage_services'] + sys.argv[1:]
mod.main()
PY
