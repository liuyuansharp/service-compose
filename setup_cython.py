#!/usr/bin/env python3
"""
Cython 编译配置脚本
将项目中的 Python 文件编译为 .so 动态库

用法:
    python3 setup_cython.py <build_dir>

所有中间文件（.c / .o）和输出 .so 均在 <build_dir> 中生成，
不会污染源码目录。
"""

import os
import sys
import shutil
from pathlib import Path
from setuptools import setup, Extension
from Cython.Build import cythonize
from Cython.Distutils import build_ext

# 项目根目录
ROOT_DIR = Path(__file__).resolve().parent

# 需要排除的文件（不编译为 .so 的文件）
EXCLUDE_FILES = {
    'setup_cython.py',
    'build.sh',
    'install.sh',
}

# __init__.py / app.py 保留为源码（不做 Cython 编译）
# - __init__.py: 包初始化文件，python -m 需要
# - app.py: FastAPI 路由使用 Depends() 依赖注入，Cython 编译后类型检查冲突
KEEP_AS_SOURCE = {
    '__init__.py',
    'app.py',
    'auth.py'
}


def collect_py_files():
    """收集所有需要编译的 Python 文件，返回 (相对路径, 模块名) 列表"""
    py_files = []

    # 收集 backend/ 下的 .py 文件
    backend_dir = ROOT_DIR / 'backend'
    for py_file in backend_dir.glob('*.py'):
        if py_file.name in EXCLUDE_FILES:
            continue
        if py_file.name in KEEP_AS_SOURCE:
            continue
        rel = py_file.relative_to(ROOT_DIR)
        module_name = str(rel.with_suffix('')).replace('/', '.')
        py_files.append((str(py_file), module_name))

    # # 收集根目录的 service_compose.py（已移入 backend/）
    # manage_file = ROOT_DIR / 'backend' / 'service_compose.py'
    # if manage_file.exists():
    #     py_files.append((str(manage_file), 'backend.service_compose'))

    return py_files


def main():
    # 解析构建目录参数
    if len(sys.argv) < 2:
        print("用法: python3 setup_cython.py <build_dir>")
        sys.exit(1)

    build_dir = Path(sys.argv[1]).resolve()
    build_dir.mkdir(parents=True, exist_ok=True)

    py_entries = collect_py_files()
    if not py_entries:
        print("没有找到需要编译的 Python 文件")
        sys.exit(1)

    print(f"将编译以下 {len(py_entries)} 个文件:")
    for src, mod in py_entries:
        print(f"  - {os.path.relpath(src, ROOT_DIR)}  ->  {mod}")
    print()

    # 1) 将源码拷贝到构建目录，保持目录结构
    src_staging = build_dir / '_src'
    if src_staging.exists():
        shutil.rmtree(src_staging)
    src_staging.mkdir(parents=True)

    staged_files = []
    for src_path, mod_name in py_entries:
        rel = Path(src_path).relative_to(ROOT_DIR)
        dst = src_staging / rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src_path, dst)
        staged_files.append((str(dst), mod_name))

    # 拷贝 __init__.py 到 staging（确保包结构被正确识别）
    for init_file in ROOT_DIR.rglob('__init__.py'):
        # 只拷贝项目内的 __init__.py（排除 venv 等）
        try:
            rel = init_file.relative_to(ROOT_DIR)
        except ValueError:
            continue
        if 'venv' in rel.parts or 'node_modules' in rel.parts or '.git' in rel.parts:
            continue
        dst = src_staging / rel
        if not dst.exists():
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(str(init_file), str(dst))

    # 2) 在 staging 目录中执行 Cython 编译
    temp_dir = build_dir / '_temp'
    temp_dir.mkdir(parents=True, exist_ok=True)

    output_dir = build_dir / 'output'
    if output_dir.exists():
        shutil.rmtree(output_dir)
    output_dir.mkdir(parents=True)

    # 切换到 staging 目录，确保相对路径正确
    original_cwd = os.getcwd()
    os.chdir(str(src_staging))

    # 生成相对路径列表供 cythonize 使用
    rel_sources = []
    for src_path, mod_name in staged_files:
        rel = Path(src_path).relative_to(src_staging)
        rel_sources.append(str(rel))

    # 不使用 build_dir，让 .c 文件就在 staging 的源文件旁边生成
    ext_modules = cythonize(
        rel_sources,
        compiler_directives={
            'language_level': '3',
            'boundscheck': False,
            'wraparound': False,
        },
        nthreads=os.cpu_count() or 4,
    )

    # 使用 --inplace，.so 按模块结构生成在 staging 目录
    sys.argv = [
        'setup_cython.py',
        'build_ext',
        '--inplace',
        '--build-temp', str(temp_dir),
    ]

    setup(
        name='services_flow',
        version='1.0.0',
        ext_modules=ext_modules,
        cmdclass={'build_ext': build_ext},
    )

    # 恢复工作目录
    os.chdir(original_cwd)

    # 3) 收集 staging 中的 .so 文件到 output，保持目录结构
    so_count = 0
    for root, dirs, files in os.walk(str(src_staging)):
        for fname in files:
            if fname.endswith('.so'):
                full = Path(root) / fname
                rel = full.relative_to(src_staging)
                dst = output_dir / rel
                dst.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(str(full), str(dst))
                so_count += 1

    print(f"\n编译完成，共生成 {so_count} 个 .so 文件，输出目录: {output_dir}")

    # 4) 清理 staging 和 temp
    shutil.rmtree(src_staging, ignore_errors=True)
    shutil.rmtree(temp_dir, ignore_errors=True)
    # 清理 setuptools 在当前目录可能生成的残留
    for d in ROOT_DIR.glob('*.egg-info'):
        shutil.rmtree(d, ignore_errors=True)
    build_residual = ROOT_DIR / 'build'
    if build_residual.exists():
        shutil.rmtree(build_residual, ignore_errors=True)


if __name__ == '__main__':
    main()
