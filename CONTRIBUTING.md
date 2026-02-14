# 贡献指南

感谢你对 **ServiceCompose** 的关注！我们欢迎任何形式的贡献，包括但不限于：

- 🐛 Bug 报告
- 💡 功能建议
- 📝 文档改进
- 🔧 代码提交

## 开始之前

1. 请先查看 [Issues](https://github.com/liuyuansharp/service-compose/issues)，确认你要解决的问题尚未被他人认领。
2. 对于较大的改动，建议先开一个 Issue 讨论方案。

## 开发流程

### 1. Fork & Clone

```bash
git clone https://github.com/liuyuansharp/service-compose.git
cd service-compose
```

### 2. 安装依赖

```bash
# 后端
pip install -r requirements.txt

# 前端
cd frontend && npm install && cd ..
```

### 3. 创建分支

请从 `main` 分支创建你的特性分支：

```bash
git checkout -b feature/your-feature
# 或
git checkout -b fix/your-bugfix
```

### 4. 开发 & 测试

```bash
# 启动后端
python3 -m backend.app --config examples/services.yaml --host 0.0.0.0 --port 8080

# 启动前端 (开发模式)
cd frontend && npm run dev
```

请确保你的改动：

- 不会破坏现有功能
- 后端代码兼容 Python 3.9+
- 前端代码通过 `npm run build` 构建无报错

### 5. 提交规范

我们推荐使用 [Conventional Commits](https://www.conventionalcommits.org/) 格式：

```
feat: 添加定时重启功能
fix: 修复日志轮转时的文件锁问题
docs: 更新 README 配置说明
refactor: 重构心跳检测模块
style: 统一代码缩进格式
chore: 更新依赖版本
```

### 6. 提交 Pull Request

```bash
git push origin feature/your-feature
```

然后在 GitHub 上创建 Pull Request，并：

- 描述你的改动内容和原因
- 关联相关 Issue（如有）
- 确保 CI 检查通过

## 代码风格

### Python (后端)

- 遵循 PEP 8 规范
- 使用 4 空格缩进
- 函数和类添加 docstring
- 类型注解尽量完整

### JavaScript / Vue (前端)

- 使用 Vue 3 Composition API (`<script setup>`)
- 组合式函数放在 `composables/` 目录
- 组件命名使用 PascalCase
- 使用 Tailwind CSS 进行样式开发

## 目录说明

| 目录 | 说明 |
|------|------|
| `backend/` | Python 后端源码 |
| `frontend/src/components/` | Vue 组件 |
| `frontend/src/composables/` | 组合式函数 |
| `examples/` | 示例配置和脚本 |

## 报告 Bug

请在 Issue 中包含以下信息：

1. **环境**：操作系统、Python 版本、Node.js 版本
2. **复现步骤**：尽量提供最小可复现的步骤
3. **期望行为**：你期望看到什么
4. **实际行为**：实际发生了什么
5. **日志 / 截图**：如有相关日志或截图请一并提供

## 许可证

提交贡献即表示你同意你的代码以 [MIT License](LICENSE) 许可发布。

---

再次感谢你的贡献！🎉
