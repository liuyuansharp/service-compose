#!/bin/bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$(readlink -f "${BASH_SOURCE[0]}")")" && pwd)"
cd "$SCRIPT_DIR"

# 激活虚拟环境（如果存在）
if [ -f "$SCRIPT_DIR/venv/bin/activate" ]; then
    source "$SCRIPT_DIR/venv/bin/activate"
fi

# 读取 .env 配置
ENV_FILE="$SCRIPT_DIR/.env"
if [ -f "$ENV_FILE" ]; then
    set -a
    source "$ENV_FILE"
    set +a
fi

# 自动检测配置文件：命令行参数 > .env > 自动检测 yaml/json
if [ -n "${1:-}" ]; then
    CONFIG_FILE="$1"
elif [ -z "${CONFIG_FILE:-}" ]; then
    if [ -f "$SCRIPT_DIR/examples/services.yaml" ]; then
        CONFIG_FILE="$SCRIPT_DIR/examples/services.yaml"
    elif [ -f "$SCRIPT_DIR/examples/services.json" ]; then
        CONFIG_FILE="$SCRIPT_DIR/examples/services.json"
    else
        echo "错误：未找到 services.yaml 或 services.json 配置文件"
        exit 1
    fi
fi

# 相对路径转绝对路径
[[ "$CONFIG_FILE" != /* ]] && CONFIG_FILE="$SCRIPT_DIR/$CONFIG_FILE"

echo "停止所有服务..."
python3 -c "
import importlib
import os
import sys
sys.path.insert(0, os.path.abspath('$SCRIPT_DIR'))
mod = importlib.import_module('backend.service_compose')
sys.argv = ['service_compose', 'stop', '--config', '$CONFIG_FILE']
mod.main()
" 2>/dev/null || true

# 停止后端 API 进程
pkill -f "backend.app" 2>/dev/null || true

echo "所有服务已停止"
