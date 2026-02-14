#!/bin/bash
#
# 完整打包脚本
# 功能：
#   1. 使用 Cython 将 Python 文件编译为 .so 动态库
#   2. 编译前端（npm run build）
#   3. 打包生成安装包（tar.gz）
#
# 用法: ./build.sh [--skip-frontend] [--skip-cython] [--version VERSION]
#

set -euo pipefail

# ======================== 配置 ========================
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

VERSION="${VERSION:-1.0.0}"
BUILD_DIR="$SCRIPT_DIR/build_dist"
PACKAGE_NAME="services_flow"
SKIP_FRONTEND=false
SKIP_CYTHON=false

# 解析命令行参数
while [[ $# -gt 0 ]]; do
    case $1 in
        --skip-frontend) SKIP_FRONTEND=true; shift ;;
        --skip-cython)   SKIP_CYTHON=true; shift ;;
        --version)       VERSION="$2"; shift 2 ;;
        -h|--help)
            echo "用法: $0 [选项]"
            echo ""
            echo "选项:"
            echo "  --skip-frontend    跳过前端编译"
            echo "  --skip-cython      跳过 Cython 编译"
            echo "  --version VERSION  设置版本号 (默认: 1.0.0)"
            echo "  -h, --help         显示帮助"
            exit 0
            ;;
        *) echo "未知选项: $1"; exit 1 ;;
    esac
done

RELEASE_NAME="${PACKAGE_NAME}-${VERSION}"
RELEASE_DIR="$BUILD_DIR/$RELEASE_NAME"

# ======================== 辅助函数 ========================
log_info()  { echo -e "\033[32m[INFO]\033[0m  $*"; }
log_warn()  { echo -e "\033[33m[WARN]\033[0m  $*"; }
log_error() { echo -e "\033[31m[ERROR]\033[0m $*"; }

check_command() {
    if ! command -v "$1" &>/dev/null; then
        log_error "未找到命令: $1，请先安装"
        return 1
    fi
}

cleanup() {
    log_info "清理临时文件..."
    # 清理 setuptools 可能在源码目录残留的文件
    rm -rf "$SCRIPT_DIR/build" 2>/dev/null || true
    rm -rf "$SCRIPT_DIR"/*.egg-info 2>/dev/null || true
    # 构建临时目录已在 build_dist 内，随整体清理
}

# ======================== 前置检查 ========================
log_info "=========================================="
log_info " $PACKAGE_NAME 打包脚本 v${VERSION}"
log_info "=========================================="
echo ""

check_command python3

if [ "$SKIP_CYTHON" = false ]; then
    # 检查 Cython 是否安装
    if ! python3 -c "import Cython" 2>/dev/null; then
        log_warn "Cython 未安装，正在安装..."
        pip3 install cython setuptools
    fi
    # 检查 gcc
    check_command gcc
fi

if [ "$SKIP_FRONTEND" = false ]; then
    check_command node
    check_command npm
fi

# ======================== 清理旧构建 ========================
log_info "清理旧的构建目录..."
rm -rf "$BUILD_DIR"
mkdir -p "$RELEASE_DIR"

# Cython 构建临时目录（所有中间文件都在这里，不污染源码）
CYTHON_BUILD_DIR="$BUILD_DIR/_cython_build"

# ======================== 步骤 1: Cython 编译 ========================
if [ "$SKIP_CYTHON" = false ]; then
    log_info "[步骤 1/5] 使用 Cython 编译 Python 文件..."
    echo ""

    # 解决 Anaconda compiler_compat 链接器与系统 libc 不兼容的问题
    # 强制使用系统 ld 而非 Anaconda 自带的旧版 ld
    export CC="gcc -pthread"
    PYTHON_INCLUDE=$(python3 -c "import sysconfig; print(sysconfig.get_path('include'))")
    export LDSHARED="gcc -pthread -shared -L/usr/lib/x86_64-linux-gnu"
    export LDFLAGS="-L/usr/lib/x86_64-linux-gnu"

    # 在独立构建目录中编译，不污染源码目录
    python3 "$SCRIPT_DIR/setup_cython.py" "$CYTHON_BUILD_DIR"

    echo ""
    log_info "Cython 编译完成，生成的 .so 文件:"
    find "$CYTHON_BUILD_DIR/output" -name "*.so" -exec echo "  - {}" \;
    echo ""
else
    log_warn "[步骤 1/5] 跳过 Cython 编译"
fi

# ======================== 步骤 2: 编译前端 ========================
if [ "$SKIP_FRONTEND" = false ]; then
    log_info "[步骤 2/5] 编译前端..."
    cd "$SCRIPT_DIR/frontend"

    if [ ! -d "node_modules" ]; then
        log_info "安装前端依赖..."
        npm install
    fi

    npm run build
    cd "$SCRIPT_DIR"

    if [ ! -d "$SCRIPT_DIR/frontend/dist" ]; then
        log_error "前端编译失败：未找到 dist 目录"
        exit 1
    fi

    log_info "前端编译完成"
    echo ""
else
    log_warn "[步骤 2/5] 跳过前端编译"
fi

# ======================== 步骤 3: 打包 venv 依赖 ========================
log_info "[步骤 3/5] 打包 Python 虚拟环境依赖..."

VENV_DIR="$SCRIPT_DIR/venv"
if [ ! -d "$VENV_DIR" ]; then
    log_error "未找到 venv 目录: $VENV_DIR"
    log_error "请先创建虚拟环境并安装依赖：python3 -m venv venv && source venv/bin/activate && pip install -r requirements.txt"
    exit 1
fi

# 找到 site-packages 目录
SITE_PACKAGES=$(python3 -c "import site; print([p for p in site.getsitepackages() if 'site-packages' in p][0])" 2>/dev/null || true)
if [ -z "$SITE_PACKAGES" ] || [ ! -d "$SITE_PACKAGES" ]; then
    # fallback: 手动查找
    SITE_PACKAGES=$(find "$VENV_DIR" -type d -name "site-packages" | head -1)
fi

if [ -z "$SITE_PACKAGES" ] || [ ! -d "$SITE_PACKAGES" ]; then
    log_error "未找到 site-packages 目录"
    exit 1
fi

log_info "site-packages 目录: $SITE_PACKAGES"

# 打包 site-packages 为 tar（排除 pip/setuptools/cython 等构建工具）
VENDOR_DIR="$RELEASE_DIR/vendor"
mkdir -p "$VENDOR_DIR"

rsync -a --quiet \
    --exclude='pip' --exclude='pip-*' \
    --exclude='setuptools' --exclude='setuptools-*' \
    --exclude='pkg_resources' \
    --exclude='Cython' --exclude='cython' --exclude='Cython-*' --exclude='cython-*' \
    --exclude='_distutils_hack' \
    --exclude='__pycache__' \
    --exclude='*.pyc' \
    --exclude='*.pyo' \
    --exclude='*.dist-info/RECORD' \
    "$SITE_PACKAGES/" "$VENDOR_DIR/"

VENDOR_SIZE=$(du -sh "$VENDOR_DIR" | cut -f1)
VENDOR_PKG_COUNT=$(find "$VENDOR_DIR" -maxdepth 1 -type d | wc -l)
log_info "已打包 venv 依赖: $VENDOR_SIZE （约 $((VENDOR_PKG_COUNT - 1)) 个顶层目录）"
echo ""

# ======================== 步骤 4: 组装发布包 ========================
log_info "[步骤 4/5] 组装发布包..."

# --- 后端 .so 文件 ---
mkdir -p "$RELEASE_DIR/backend"

if [ "$SKIP_CYTHON" = false ]; then
    # 从构建目录拷贝编译后的 .so 文件
    if [ -d "$CYTHON_BUILD_DIR/output/backend" ]; then
        cp "$CYTHON_BUILD_DIR/output/backend/"*.so "$RELEASE_DIR/backend/" 2>/dev/null || true
    fi
    # 根目录的 .so（manage_services）
    find "$CYTHON_BUILD_DIR/output" -maxdepth 1 -name "*.so" -exec cp {} "$RELEASE_DIR/" \;

    # __init__.py: 包初始化文件必须保留源码
    cp "$SCRIPT_DIR/backend/__init__.py" "$RELEASE_DIR/backend/__init__.py"

    # app.py: FastAPI Depends() 与 Cython 不兼容，编译为 .pyc 字节码发布
    # 直接放在 backend/app.pyc（非 __pycache__），python -m 可无源码加载
    python3 -c "
import py_compile
py_compile.compile('$SCRIPT_DIR/backend/app.py', cfile='$RELEASE_DIR/backend/app.pyc', doraise=True)
print('  编译 app.py -> backend/app.pyc')
"
    python3 -c "
import py_compile
py_compile.compile('$SCRIPT_DIR/backend/auth.py', cfile='$RELEASE_DIR/backend/auth.pyc', doraise=True)
print('  编译 auth.py -> backend/auth.pyc')
"
    python3 -c "
import py_compile
py_compile.compile('$SCRIPT_DIR/manage_services.py', cfile='$RELEASE_DIR/manage_services.pyc', doraise=True)
print('  编译 manage_services.py -> manage_services.pyc')
"
else
    # 不编译模式：直接拷贝 .py 文件
    cp "$SCRIPT_DIR/manage_services.py" "$RELEASE_DIR/"
    cp "$SCRIPT_DIR/backend/"*.py "$RELEASE_DIR/backend/"
fi

# --- 前端 dist ---
if [ -d "$SCRIPT_DIR/frontend/dist" ]; then
    mkdir -p "$RELEASE_DIR/frontend"
    cp -r "$SCRIPT_DIR/frontend/dist" "$RELEASE_DIR/frontend/dist"
    # 拷贝 public/config.js（运行时配置）
    if [ -f "$SCRIPT_DIR/frontend/public/config.js" ]; then
        mkdir -p "$RELEASE_DIR/frontend/dist"
        cp "$SCRIPT_DIR/frontend/public/config.js" "$RELEASE_DIR/frontend/dist/config.js"
    fi
fi

# --- 示例和配置 ---
mkdir -p "$RELEASE_DIR/examples"
mkdir -p "$RELEASE_DIR/examples/.services"
mkdir -p "$RELEASE_DIR/examples/.services/logs"
cp -r "$SCRIPT_DIR/examples/"* "$RELEASE_DIR/examples/" 2>/dev/null || true

# 将配置文件中的硬编码源码路径替换为占位符，安装时再替换为实际路径
find "$RELEASE_DIR/examples" \( -name "*.json" -o -name "*.yaml" \) -exec \
    sed -i "s|${SCRIPT_DIR}|__INSTALL_DIR__|g" {} \;

# --- 依赖文件 ---
cp "$SCRIPT_DIR/requirements.txt" "$RELEASE_DIR/"

# --- 启动脚本（生成适配编译后的启动脚本） ---
cat > "$RELEASE_DIR/start_backend.sh" << 'SCRIPT_EOF'
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
SCRIPT_EOF
chmod +x "$RELEASE_DIR/start_backend.sh"

cat > "$RELEASE_DIR/start_all.sh" << 'SCRIPT_EOF'
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
mod = importlib.import_module('manage_services')
sys.argv = ['manage_services', 'start', '--config', '$CONFIG_FILE', '--daemon']
mod.main()
" &>/dev/null &

echo "启动后端 API..."
nohup python3 -m backend.app --config "$CONFIG_FILE" --host 0.0.0.0 --port 8080 &>/dev/null &

echo "所有服务已启动"
echo "  API 地址: http://0.0.0.0:8080"
echo "  API 文档: http://0.0.0.0:8080/api/docs"
SCRIPT_EOF
chmod +x "$RELEASE_DIR/start_all.sh"

cat > "$RELEASE_DIR/stop_all.sh" << 'SCRIPT_EOF'
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
SCRIPT_EOF
chmod +x "$RELEASE_DIR/stop_all.sh"

cat > "$RELEASE_DIR/manage_services.sh" << 'SCRIPT_EOF'
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
SCRIPT_EOF
chmod +x "$RELEASE_DIR/manage_services.sh"

ln -s "$RELEASE_DIR/manage_services.sh" "$RELEASE_DIR/examples/.services/manage_services"

# --- 安装脚本 ---
cat > "$RELEASE_DIR/install.sh" << 'INSTALL_EOF'
#!/bin/bash
#
# 安装脚本 - services_flow
# 使用打包好的依赖，无需联网安装
#
# 用法: ./install.sh --python /path/to/python3 [安装目录]
#

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PYTHON3=""
INSTALL_DIR=""

# 解析参数
while [[ $# -gt 0 ]]; do
    case $1 in
        --python|-p)
            PYTHON3="$2"; shift 2 ;;
        -h|--help)
            echo "用法: $0 --python /path/to/python3 [安装目录]"
            echo ""
            echo "参数:"
            echo "  --python, -p PATH  指定 python3 可执行文件路径（必需）"
            echo "  安装目录            安装目标路径（默认: ./services_flow）"
            echo ""
            echo "示例:"
            echo "  $0 --python /usr/bin/python3"
            echo "  $0 --python /opt/python3.9/bin/python3 /opt/services_flow"
            exit 0
            ;;
        -*)
            echo "未知选项: $1"; exit 1 ;;
        *)
            INSTALL_DIR="$1"; shift ;;
    esac
done

# 默认安装到当前目录下的 services_flow
INSTALL_DIR="${INSTALL_DIR:-$(pwd)/services_flow}"

log_info()  { echo -e "\033[32m[INFO]\033[0m  $*"; }
log_warn()  { echo -e "\033[33m[WARN]\033[0m  $*"; }
log_error() { echo -e "\033[31m[ERROR]\033[0m $*"; }

# 检查 python3 路径
if [ -z "$PYTHON3" ]; then
    log_error "必须指定 python3 路径"
    echo ""
    echo "用法: $0 --python /path/to/python3 [安装目录]"
    echo "示例: $0 --python /usr/bin/python3"
    exit 1
fi

if [ ! -x "$PYTHON3" ]; then
    log_error "python3 不存在或不可执行: $PYTHON3"
    exit 1
fi

PYTHON_VERSION=$("$PYTHON3" -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}')")
log_info "使用 Python: $PYTHON3 (版本 $PYTHON_VERSION)"

echo "=========================================="
echo " services_flow 安装程序"
echo "=========================================="
echo ""
echo "Python 路径: $PYTHON3"
echo "安装目录:    $INSTALL_DIR"
echo ""

# 创建安装目录
mkdir -p "$INSTALL_DIR"

# 拷贝所有文件（排除 vendor 目录，稍后单独处理）
log_info "拷贝文件到安装目录..."
for item in "$SCRIPT_DIR/"*; do
    base="$(basename "$item")"
    [ "$base" = "install.sh" ] && continue
    [ "$base" = "vendor" ] && continue
    cp -r "$item" "$INSTALL_DIR/"
done

# 替换配置文件中的路径占位符为实际安装路径
log_info "更新配置文件路径..."
find "$INSTALL_DIR" \( -name "*.json" -o -name "*.yaml" \) -exec \
    sed -i "s|__INSTALL_DIR__|${INSTALL_DIR}|g" {} \;

# 创建虚拟环境并安装打包好的依赖
log_info "创建 Python 虚拟环境..."
cd "$INSTALL_DIR"

if [ ! -d "venv" ]; then
    "$PYTHON3" -m venv venv
fi

# 将打包好的第三方包拷贝到 venv 的 site-packages
VENV_SITE_PACKAGES=$(
    "$INSTALL_DIR/venv/bin/python3" -c \
    "import site; print([p for p in site.getsitepackages() if 'site-packages' in p][0])"
)

if [ -d "$SCRIPT_DIR/vendor" ]; then
    log_info "安装打包好的 Python 依赖到 venv..."
    cp -r "$SCRIPT_DIR/vendor/"* "$VENV_SITE_PACKAGES/"
    log_info "依赖安装完成（离线模式）"
else
    log_warn "未找到打包好的依赖目录，尝试在线安装..."
    source venv/bin/activate
    pip install --upgrade pip -q
    pip install -r requirements.txt -q
    deactivate
fi

# 设置权限
chmod +x "$INSTALL_DIR/"*.sh 2>/dev/null || true

echo ""
log_info "=========================================="
log_info " 安装完成！"
log_info "=========================================="
echo ""
echo "使用方法:"
echo "  启动所有服务:  $INSTALL_DIR/start_all.sh [config_file]"
echo "  启动后端:      $INSTALL_DIR/start_backend.sh [config_file]"
echo "  停止所有服务:  $INSTALL_DIR/stop_all.sh [config_file]"
echo "  服务管理:      $INSTALL_DIR/manage_services.sh {start|stop|status|restart}"
echo ""
echo "默认配置文件: $INSTALL_DIR/examples/services.yaml"
echo "API 地址:     http://0.0.0.0:8080"
echo "API 文档:     http://0.0.0.0:8080/api/docs"
echo ""
INSTALL_EOF
chmod +x "$RELEASE_DIR/install.sh"

log_info "发布包内容:"
find "$RELEASE_DIR" -type f | sort | while read -r f; do
    echo "  $(realpath --relative-to="$RELEASE_DIR" "$f")"
done
echo ""

# ======================== 步骤 5: 打包为 tar.gz ========================
log_info "[步骤 5/5] 打包为安装包..."

cd "$BUILD_DIR"
TARBALL="${RELEASE_NAME}-linux-$(uname -m).tar.gz"
tar czf "$TARBALL" "$RELEASE_NAME"

TARBALL_PATH="$BUILD_DIR/$TARBALL"
TARBALL_SIZE=$(du -h "$TARBALL_PATH" | cut -f1)

echo ""
log_info "=========================================="
log_info " 打包完成！"
log_info "=========================================="
echo ""
echo "安装包: $TARBALL_PATH"
echo "大小:   $TARBALL_SIZE"
echo ""
echo "安装方式:"
echo "  tar xzf $TARBALL"
echo "  cd $RELEASE_NAME"
echo "  ./install.sh [安装目录]"
echo ""

# ======================== 清理临时文件 ========================
cleanup

# 清理 Cython 构建临时目录（保留最终的 tar.gz 和发布包目录）
rm -rf "$CYTHON_BUILD_DIR" 2>/dev/null || true

log_info "构建完成"
