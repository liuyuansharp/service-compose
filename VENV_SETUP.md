# 🐍 Python 虚拟环境设置指南

## 📋 概述

已为项目创建了 Python 虚拟环境，用于隔离项目依赖，避免与系统 Python 包的冲突。

---

## ✅ 虚拟环境状态

### 已创建

- **位置**：`/home/liuyuan/workspace/work/fsys/service/venv`
- **Python 版本**：3.12.7
- **已安装依赖**：6 个包

### 已安装的包

| 包名 | 版本 | 用途 |
|------|------|------|
| `fastapi` | 0.104.1 | Web 框架 |
| `uvicorn[standard]` | 0.24.0 | ASGI 服务器 |
| `pydantic` | 2.5.0 | 数据验证 |
| `pydantic-settings` | 2.1.0 | 配置管理 |
| `python-dotenv` | 1.0.0 | 环境变量加载 |
| `psutil` | 5.9.8 | 系统监控 |

---

## 🚀 激活虚拟环境

### 方法 1：直接激活（推荐）

```bash
# 进入项目目录
cd /home/liuyuan/workspace/work/fsys/service

# 激活虚拟环境
source venv/bin/activate

# 你会看到提示符变化
(venv) $ 
```

### 方法 2：使用激活脚本

```bash
# 在项目根目录运行
source .env-setup.sh

# 输出示例：
# ✅ 虚拟环境已激活: /home/liuyuan/workspace/work/fsys/service/venv
# Python 版本: Python 3.12.7
```

### 方法 3：一行命令激活并运行

```bash
# 直接在虚拟环境中运行 Python
source ./venv/bin/activate && python dashboard_api.py

# 或运行 pip 命令
source ./venv/bin/activate && pip list
```

---

## 📦 验证虚拟环境

### 检查 Python 版本

```bash
# 激活环境后
source venv/bin/activate

# 检查 Python
python --version
# 输出: Python 3.12.7

# 检查 pip
pip --version
# 输出: pip 24.3.1 from /path/to/venv/lib/python3.12/site-packages/pip
```

### 查看已安装的包

```bash
# 激活环境后
pip list

# 输出示例:
# Package            Version
# ------------------ -----------
# fastapi            0.104.1
# pydantic           2.5.0
# psutil             5.9.8
# python-dotenv      1.0.0
# pydantic-settings  2.1.0
# uvicorn            0.24.0
```

### 验证特定包

```bash
# 检查 fastapi
python -c "import fastapi; print(f'FastAPI {fastapi.__version__}')"

# 检查 psutil
python -c "import psutil; print(f'psutil {psutil.__version__}')"

# 检查所有依赖
python -c "import fastapi, pydantic, psutil, uvicorn; print('✅ 所有依赖都已正确安装')"
```

---

## 💾 在虚拟环境中安装新包

### 添加新依赖

```bash
# 确保虚拟环境已激活
source venv/bin/activate

# 安装新包
pip install <package-name>

# 例如：安装 requests
pip install requests
```

### 更新 requirements.txt

```bash
# 激活虚拟环境后，生成新的 requirements.txt
pip freeze > requirements.txt
```

### 从 requirements.txt 安装

```bash
# 激活虚拟环境后
pip install -r requirements.txt

# 安装特定版本
pip install -r requirements.txt --upgrade
```

---

## 🔄 停用虚拟环境

### 退出虚拟环境

```bash
# 当前处于虚拟环境中时（提示符显示 (venv)）
deactivate

# 提示符会恢复为正常状态
```

---

## 🐛 故障排查

### 问题 1：找不到虚拟环境

**症状**：
```
bash: ./venv/bin/activate: No such file or directory
```

**解决**：
```bash
# 重新创建虚拟环境
python3 -m venv venv

# 然后激活
source venv/bin/activate

# 安装依赖
pip install -r requirements.txt
```

### 问题 2：虚拟环境损坏

**症状**：
```
Error: [Errno 2] No such file or directory: 'venv/bin/python'
```

**解决**：
```bash
# 删除旧的虚拟环境
rm -rf venv

# 重新创建
python3 -m venv venv

# 激活并安装
source venv/bin/activate
pip install -r requirements.txt
```

### 问题 3：pip 版本过旧

**症状**：
```
[notice] A new release of pip is available: 24.2 -> 26.0.1
```

**解决**：
```bash
# 激活虚拟环境后
pip install --upgrade pip

# 或使用模块运行升级
python -m pip install --upgrade pip
```

### 问题 4：权限错误

**症状**：
```
PermissionError: [Errno 13] Permission denied
```

**解决**：
```bash
# 检查权限
ls -la venv/bin/

# 修复权限
chmod -R +x venv/bin/

# 重新激活
source venv/bin/activate
```

---

## 📁 项目结构

```
service/
├── venv/                          # 虚拟环境目录
│   ├── bin/                       # 可执行文件
│   │   ├── activate               # 激活脚本
│   │   ├── deactivate             # 停用脚本
│   │   ├── python                 # Python 解释器
│   │   └── pip                    # 包管理器
│   ├── lib/                       # 库文件
│   │   └── python3.12/
│   │       └── site-packages/     # 已安装的包
│   ├── include/                   # 头文件
│   └── pyvenv.cfg                 # 配置文件
│
├── requirements.txt               # 依赖列表
├── .env-setup.sh                 # 激活脚本（便捷）
├── dashboard_api.py              # 后端应用
├── manage_services.py            # 服务管理器
└── ...
```

---

## 🎯 常用命令

### 快速启动

```bash
# 一键启动（激活环境 + 运行后端）
source venv/bin/activate && python dashboard_api.py --port 8080
```

### 开发工作流

```bash
# 1. 进入项目目录
cd /home/liuyuan/workspace/work/fsys/service

# 2. 激活虚拟环境
source venv/bin/activate

# 3. 运行应用
python dashboard_api.py

# 4. 或运行管理脚本
python manage_services.py

# 5. 完成后停用环境
deactivate
```

### 依赖管理

```bash
# 查看所有包
pip list

# 搜索包
pip search <package-name>

# 显示包信息
pip show <package-name>

# 升级包
pip install --upgrade <package-name>

# 卸载包
pip uninstall <package-name>

# 冻结依赖（生成新的 requirements.txt）
pip freeze > requirements.txt
```

---

## 🔐 安全建议

### ✅ 推荐做法

1. **始终使用虚拟环境**
   - 避免污染全局 Python
   - 便于项目隔离
   - 方便依赖管理

2. **版本锁定**
   - 所有包都有固定版本号（如 `fastapi==0.104.1`）
   - 确保环境一致性

3. **定期更新**
   ```bash
   # 检查可更新的包
   pip list --outdated
   
   # 谨慎升级（一次一个）
   pip install --upgrade <package-name>
   ```

4. **备份依赖**
   ```bash
   # 定期冻结依赖
   pip freeze > requirements-lock.txt
   ```

### ❌ 不推荐做法

- ❌ 直接在系统 Python 中安装包
- ❌ 手动编辑虚拟环境目录
- ❌ 跨项目共享虚拟环境
- ❌ 忽视依赖版本冲突

---

## 📊 虚拟环境信息

| 项目 | 值 |
|------|-----|
| **位置** | `/home/liuyuan/workspace/work/fsys/service/venv` |
| **Python 版本** | 3.12.7 |
| **已安装包数** | 6 个 |
| **总大小** | ~200 MB |
| **包管理器** | pip 24.3.1 |
| **状态** | ✅ 正常 |

---

## 📚 更多信息

### 官方文档

- [Python 虚拟环境文档](https://docs.python.org/3/library/venv.html)
- [pip 文档](https://pip.pypa.io/)
- [FastAPI 文档](https://fastapi.tiangolo.com/)

### 相关项目文件

- `requirements.txt` - 所有项目依赖
- `dashboard_api.py` - FastAPI 应用
- `SETUP.md` - 项目设置指南
- `README.md` - 项目概述

---

## ✨ 总结

✅ **虚拟环境已准备好！**

现在可以：
1. 激活虚拟环境：`source venv/bin/activate`
2. 运行后端：`python dashboard_api.py`
3. 开始开发：使用隔离的 Python 环境

**提示**：每次启动项目前，记得激活虚拟环境！

---

创建时间：2026-02-05  
状态：✅ 完成
