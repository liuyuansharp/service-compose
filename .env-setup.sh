#!/bin/bash

# 虚拟环境激活脚本
# 使用方法: source .env-setup.sh

VENV_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/venv"

if [ ! -d "$VENV_DIR" ]; then
    echo "❌ 虚拟环境不存在: $VENV_DIR"
    echo "请先运行: python3 -m venv venv"
    return 1
fi

# 激活虚拟环境
source "$VENV_DIR/bin/activate"

echo "✅ 虚拟环境已激活: $VENV_DIR"
echo "Python 版本: $(python --version)"
echo "提示: 运行 'deactivate' 可退出虚拟环境"
