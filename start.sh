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

HOST="${HOST:-0.0.0.0}"
PORT="${PORT:-8080}"

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
nohup python3 -m backend.app --config "$CONFIG_FILE" --host "$HOST" --port "$PORT" &>/dev/null &

echo "所有服务已启动"
echo "  API 地址: http://${HOST}:${PORT}"
echo "  API 文档: http://${HOST}:${PORT}/api/docs"
