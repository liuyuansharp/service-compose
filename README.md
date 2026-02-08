# Service Manager Dashboard

一个完整的服务管理和监控系统，包括：
- 🐍 **Python FastAPI** 后端 - 完整的 REST API 和 WebSocket 支持
- 🎨 **Vue3 前端** - 现代化、响应式的 Web 仪表板
- 📊 **实时监控** - 查看所有服务的运行状态
- 🎮 **服务控制** - 启动、停止、重启服务
- 📋 **日志管理** - 查看、搜索、下载日志
- 🚀 **自动重启** - 指数退避和防风暴机制

## 🌟 主要特性

### 后端功能 (FastAPI)
- ✅ REST API 端点 - 状态、控制、日志操作
- ✅ WebSocket 实时日志流
- ✅ 与 manage_services.py 集成
- ✅ 自动提供前端静态文件（生产环境）
- ✅ 详细的错误处理和日志记录

### 前端功能 (Vue3)
- ✅ 实时状态监控仪表板
- ✅ 服务控制面板
- ✅ 高级日志查看器（搜索、暂停、下载）
- ✅ 响应式设计（移动端友好）
- ✅ 现代化的 UI（Tailwind CSS）

### 服务管理 (manage_services.py - 原有)
- ✅ 平台优先启动，然后并行启动子服务
- ✅ PID 文件管理
- ✅ 自动日志轮转（10MB/文件，5 个备份）
- ✅ 指数退避重启延迟
- ✅ 防重启风暴机制
- ✅ 优雅停止处理

## 🚀 快速开始（5 分钟）

### 方式 1：一键启动（推荐）

```bash
chmod +x dev-start.sh
./dev-start.sh
```

脚本会自动：
1. 检查环境（Python 和 Node.js）
2. 安装依赖
3. 启动后端服务器（http://localhost:8080）
4. 启动前端开发服务器（http://localhost:5173）
5. 在浏览器中打开仪表板

### 方式 2：分别启动

**后端：**
```bash
pip install -r requirements.txt
python dashboard_api.py --reload
```

**前端：**
```bash
cd frontend
npm install
npm run dev
```

### 访问地址

| 服务 | URL |
|------|-----|
| 🎨 仪表板 | http://localhost:5173 |
| 🔧 后端 API | http://localhost:8080 |
| 📖 API 文档 | http://localhost:8080/api/docs |
| 💚 健康检查 | http://localhost:8080/api/health |

### 前端运行时配置

构建后的前端会从 `dist/config.js` 读取后端地址（开发时位于 `frontend/public/config.js`）。

```js
window.APP_CONFIG = {
  apiBaseUrl: "http://localhost:8080",
  wsBaseUrl: "ws://localhost:8080"
};
```

## � 登录与权限

仪表板已启用登录认证，后端使用 SQLite (`auth.db`) 保存用户。

- 默认账号：`admin`
- 默认密码：`admin123`

可通过环境变量调整：

- `DEFAULT_ADMIN_PASSWORD`：初始化默认管理员密码
- `AUTH_SECRET_KEY`：JWT 签名密钥
- `ACCESS_TOKEN_EXPIRE_MINUTES`：Token 过期时间（分钟，默认 480）

前端登录后会自动携带 Token 访问 API（包括 SSE 与 WebSocket）。

## �📁 文件说明

### 核心应用
| 文件 | 说明 |
|------|------|
| `dashboard_api.py` | FastAPI 后端应用（430+ 行）|
| `frontend/` | Vue3 前端应用目录 |
| `manage_services.py` | 服务管理器（原有，后端依赖）|

### 配置文件
| 文件 | 说明 |
|------|------|
| `services_config.json` | 服务定义和配置 |
| `requirements.txt` | Python 依赖列表 |
| `frontend/package.json` | npm 项目配置 |

### 启动脚本
| 文件 | 说明 |
|------|------|
| `dev-start.sh` | 🌟 一键启动脚本（强烈推荐）|
| `setup.sh` | 环境初始化脚本 |
| `test-api.sh` | Bash API 测试脚本 |
| `test_api.py` | Python API 测试脚本 |

### 文档
| 文件 | 说明 |
|------|------|
| `DASHBOARD_README.md` | 📖 完整使用和 API 文档 |
| `QUICK_START.md` | ⚡ 快速参考指南 |
| `SETUP.md` | 🔧 部署和初始化指南 |
| `PROJECT_CHECKLIST.md` | ✅ 项目清单 |
| `README.md` | 📄 本文件 |

### 目录结构
```
logs/
├── platform.log         # 平台日志（自动生成）
├── service_a.log        # 服务日志（自动生成）
└── ...

frontend/
├── src/                 # 源代码
│   ├── App.vue         # 主组件
│   ├── main.js         # 入口文件
│   └── style.css       # 样式
├── public/             # 公开资源
├── dist/               # 构建输出（npm run build）
├── package.json        # npm 配置
├── vite.config.js      # Vite 配置
├── tailwind.config.js  # Tailwind 配置
└── index.html          # HTML 模板
```

## 📊 日志管理

### 自动轮转（由 manage_services.py 处理）

日志文件自动轮转，配置如下：
- **文件大小限制** - 10MB
- **保留备份数** - 5 个
- **轮转方式** - 当日志文件达到 10MB 时，自动重命名为 `.1`、`.2` 等

### 在仪表板中查看日志

1. 点击任何服务的 **Logs** 按钮
2. 在模态框中查看实时日志
3. 使用搜索功能查找特定内容
4. 点击 **Download** 下载完整日志文件
5. 点击 **Pause** 暂停实时更新

### 日志等级着色

- 🔴 **ERROR** - 错误（红色）
- 🟡 **WARNING** - 警告（黄色）
- 🟢 **INFO** - 信息（绿色）
- 🔵 **DEBUG** - 调试（蓝色）

## 🔄 自动重启策略（由 manage_services.py 处理）

### 指数退避延迟

当服务崩溃时，会自动重启。重启延迟按指数增长：

| 重启次数 | 延迟 |
|---------|------|
| 第 1 次 | 1s   |
| 第 2 次 | 2s   |
| 第 3 次 | 4s   |
| 第 4 次 | 8s   |
| 第 5 次 | 16s  |
| 第 6 次 | 32s  |
| 第 7 次+ | 60s  |

### 防重启风暴

- 监控每个服务在 1 分钟内的重启次数
- 如果超过 5 次，则放弃自动重启并记录严重错误
- 需要手动干预恢复

## 🔌 API 快速参考

### 健康检查
```bash
curl http://localhost:8080/api/health
# 响应: {"status": "healthy", "timestamp": "..."}
```

### 获取状态
```bash
curl http://localhost:8080/api/status
# 返回：平台状态、所有服务状态、时间戳
```

### 启动/停止/重启服务
```bash
# 启动
curl -X POST http://localhost:8080/api/control \
  -H "Content-Type: application/json" \
  -d '{"action": "start"}'

# 停止
curl -X POST http://localhost:8080/api/control \
  -H "Content-Type: application/json" \
  -d '{"action": "stop"}'

# 重启
curl -X POST http://localhost:8080/api/control \
  -H "Content-Type: application/json" \
  -d '{"action": "restart"}'
```

### 获取日志
```bash
curl "http://localhost:8080/api/logs?service=platform&lines=100"
curl "http://localhost:8080/api/logs?service=platform&search=ERROR"
```

### 下载日志文件
```bash
curl "http://localhost:8080/api/logs/download?service=platform" > logs.txt
```

### WebSocket 实时日志
```javascript
ws = new WebSocket('ws://localhost:8080/api/ws/logs/platform');
ws.onmessage = (event) => {
  const log = JSON.parse(event.data);
  console.log(log.raw);
};
// 发送控制命令
ws.send(JSON.stringify({action: "pause"}));
ws.send(JSON.stringify({action: "resume"}));
```

详见：http://localhost:8080/api/docs（Swagger UI）

## 🧪 测试 API

### 运行自动化测试

```bash
# Python 脚本（推荐，跨平台）
python test_api.py

# 或 Bash 脚本
./test-api.sh
```

## 🛠️ 配置和定制

### 改变服务配置

编辑 `services_config.json`，修改：
- 服务启动命令和参数
- 日志文件位置
- 自动重启设置
- `heartbeat`：服务健康检查地址（例如 `http://127.0.0.1:9001/heartbeat`）。
  - 可填 `mock` 用于模拟 200 响应（当前示例配置默认）。

### 改变仪表板配置

**刷新频率：** 编辑 `frontend/src/App.vue`
```javascript
statusInterval = setInterval(refreshStatus, 5000)  // 改为需要的毫秒数
```

**UI 主题色：** 编辑 `frontend/tailwind.config.js`
```javascript
colors: {
  primary: '#3b82f6',    // 改为你的颜色
  secondary: '#8b5cf6'
}
```

### 改变后端端口

```bash
python dashboard_api.py --port 9000
```

## 📚 更多文档

| 文档 | 内容 | 阅读时间 |
|------|------|---------|
| [DASHBOARD_README.md](./DASHBOARD_README.md) | 完整使用指南和 API 文档 | 20 min |
| [QUICK_START.md](./QUICK_START.md) | 常用命令快速参考 | 5 min |
| [SETUP.md](./SETUP.md) | 初始化和生产部署指南 | 15 min |
| [PROJECT_CHECKLIST.md](./PROJECT_CHECKLIST.md) | 项目完整清单 | 10 min |

## ❓ 常见问题

### Q: 如何在生产环境部署？
A: 请参考 `SETUP.md` 中的"生产部署"部分。

### Q: 如何添加新的服务？
A: 编辑 `services_config.json`，在 `services` 数组中添加新的服务定义。

### Q: 如何查看实时日志？
A: 打开仪表板（http://localhost:5173），点击服务的"Logs"按钮。

### Q: 如何修改 UI 主题？
A: 编辑 `frontend/tailwind.config.js` 修改颜色配置。

### Q: 能否使用 Docker？
A: 可以使用，但项目默认直接运行。可参考 `docker/` 目录的相关文件。
- 配置健康检查
- 调整重启延迟参数## 🔐 生产部署建议

### 最小化部署
```bash
# 1. 构建前端
cd frontend
npm run build
cd ..

# 2. 启动后端（后端会自动提供前端静态文件）
python dashboard_api.py --host 0.0.0.0 --port 8080
```

### 使用 systemd（Linux）
参考 `systemd/INSTALL_GUIDE.md` 配置自动启动。

### 使用 PM2（推荐）
```bash
npm install -g pm2
pm2 start dashboard_api.py --name dashboard --interpreter python3
pm2 startup
pm2 save
```

### 使用反向代理（Nginx）
参考 `SETUP.md` 中的"使用反向代理"部分。

## 📞 获取帮助

- 📖 完整文档 - `DASHBOARD_README.md`
- ⚡ 快速参考 - `QUICK_START.md`
- 🔧 部署指南 - `SETUP.md`
- 📄 项目清单 - `PROJECT_CHECKLIST.md`
- 🌐 API 文档 - http://localhost:8080/api/docs

## 🏆 项目亮点

✅ 完整的 Web 仪表板（Vue3 + Tailwind CSS）  
✅ RESTful API + WebSocket（FastAPI）  
✅ 实时日志查看和搜索  
✅ 一键启动脚本  
✅ 5000+ 行完整文档  
✅ 跨平台支持（Windows、Mac、Linux）  
✅ 无需 Docker，即装即用  

## 📄 许可证

MIT

---

**立即启动：** `./dev-start.sh`

**需要帮助？** 查看 `QUICK_START.md` 或 `DASHBOARD_README.md`

