# Service Manager Dashboard

一个现代化的 Web 仪表板，用于实时监控和控制多个服务的运行状态。包括一个 Python FastAPI 后端和 Vue3 前端。

## ✨ 特性

- 🔴 **实时状态监控** - 查看平台和所有服务的运行状态
- 🎮 **一键控制** - 启动、停止、重启服务
- 📊 **日志查看** - 实时查看和搜索日志
- 💾 **日志下载** - 下载完整日志文件
- 🎨 **现代化 UI** - 使用 Tailwind CSS 构建的响应式界面
- ⚡ **快速开发** - Vite 热模块替换，开发体验极佳
- 🔧 **简易部署** - 无需 Docker，直接运行

## 📋 项目结构

```
service/
├── dashboard_api.py           # FastAPI 后端应用
├── manage_services.py         # 服务管理器（原有）
├── services_config.json       # 服务配置文件
├── requirements.txt           # Python 依赖
├── dev-start.sh              # 开发启动脚本
├── frontend/                 # Vue3 前端
│   ├── src/
│   │   ├── App.vue          # 主应用组件
│   │   ├── main.js          # 入口文件
│   │   └── style.css        # 全局样式
│   ├── index.html           # HTML 模板
│   ├── vite.config.js       # Vite 配置
│   ├── tailwind.config.js   # Tailwind 配置
│   ├── postcss.config.js    # PostCSS 配置
│   ├── package.json         # npm 依赖
│   └── .gitignore
└── logs/                     # 日志目录（自动创建）
```

## 🚀 快速开始

### 方式 1：一键启动（推荐）

```bash
chmod +x dev-start.sh
./dev-start.sh
```

脚本会自动：
1. 检查 Python 和 Node.js
2. 安装依赖
3. 启动后端服务器（port 8080）
4. 启动前端开发服务器（port 5173）
5. 在浏览器中打开仪表板

### 方式 2：分别启动

**后端服务器：**
```bash
# 安装依赖
pip install -r requirements.txt

# 启动服务（支持自动重载）
python dashboard_api.py --host 0.0.0.0 --port 8080 --reload
```

**前端开发服务器：**
```bash
cd frontend

# 安装依赖
npm install

# 启动开发服务器
npm run dev
```

## 🌐 访问地址

启动成功后，可以通过以下地址访问：

| 服务 | 地址 | 说明 |
|------|------|------|
| 仪表板 | http://localhost:5173 | Vue3 前端 |
| 后端 API | http://localhost:8080 | FastAPI 后端 |
| API 文档 | http://localhost:8080/api/docs | Swagger UI 文档 |
| API 架构 | http://localhost:8080/api/redoc | ReDoc 文档 |

## 📱 使用指南

### 仪表板界面

#### 顶部状态卡片
- **Overall Status** - 平台总体运行状态
- **Active Services** - 当前运行的服务数
- **Last Updated** - 最后更新时间

#### 平台卡片
显示平台进程的详细信息：
- 运行状态指示灯
- 进程 ID (PID)
- 最近日志条目
- 启动/停止按钮
- 查看日志按钮

#### 服务列表
网格显示所有服务：
- 每个服务有独立卡片
- 显示状态、PID 和最近日志
- 支持单个服务控制

### 日志查看器

点击任何服务的 **Logs** 按钮打开日志窗口：

**功能：**
- **Pause/Resume** - 暂停或恢复实时更新
- **Search** - 搜索日志内容
- **Download** - 下载当前日志文件
- **Clear** - 清除显示的日志

**日志等级着色：**
- 🔴 ERROR - 红色
- 🟡 WARNING - 黄色
- 🟢 INFO - 绿色
- 🔵 DEBUG - 蓝色

## 🔌 API 端点

### REST API

#### 获取状态
```bash
GET /api/status

# 响应示例
{
  "status": "running",
  "platform": {
    "name": "platform",
    "running": true,
    "pid": 12345,
    "last_log": "2024-02-05 10:30:45 - INFO - Platform started"
  },
  "services": [...],
  "timestamp": "2024-02-05T10:30:45.123456"
}
```

#### 控制服务
```bash
POST /api/control
Content-Type: application/json

{
  "action": "start",  # 或 "stop", "restart"
  "service": "service_a"  # 可选，None 表示控制平台
}
```

#### 获取日志
```bash
GET /api/logs?service=platform&lines=100&search=ERROR

# 响应
{
  "service": "platform",
  "logs": [...],
  "total": 1500,
  "displayed": 50
}
```

#### 下载日志
```bash
GET /api/logs/download?service=platform
```

### WebSocket

#### 实时日志流
```javascript
ws = new WebSocket('ws://localhost:8080/api/ws/logs/platform');

// 接收日志
ws.onmessage = (event) => {
  const log = JSON.parse(event.data);
  console.log(log.raw);
};

// 发送控制命令
ws.send(JSON.stringify({ action: 'pause' }));    // 暂停
ws.send(JSON.stringify({ action: 'resume' }));   // 恢复
ws.send(JSON.stringify({ action: 'clear' }));    // 清除
```

## ⚙️ 配置

### 后端配置

编辑 `dashboard_api.py` 的配置部分：

```python
# 日志目录
LOGS_DIR = SERVICE_DIR / 'logs'

# 日志行数（API 默认返回）
lines: int = Query(100)
```

命令行参数：
```bash
python dashboard_api.py --host 0.0.0.0 --port 8080 --reload
```

### 前端配置

编辑 `frontend/vite.config.js`：

```javascript
server: {
  port: 5173,
  proxy: {
    '/api': {
      target: 'http://localhost:8080',  // 后端地址
      changeOrigin: true,
    }
  }
}
```

编辑 `frontend/tailwind.config.js` 修改主题色：

```javascript
colors: {
  primary: '#3b82f6',    // 主色
  secondary: '#8b5cf6',  // 副色
}
```

## 🛠️ 开发

### 添加新的 API 端点

在 `dashboard_api.py` 中：

```python
@app.get("/api/new-endpoint")
async def new_endpoint():
    return {"message": "Hello"}
```

### 修改前端组件

编辑 `frontend/src/App.vue`，支持热模块替换：

```vue
<template>
  <div><!-- 你的 HTML --></div>
</template>

<script setup>
// 你的 JavaScript
</script>

<style scoped>
/* 你的样式 */
</style>
```

### 构建生产版本

```bash
# 构建前端
cd frontend
npm run build

# 后端直接使用，会自动提供静态文件
# 访问 http://localhost:8080 即可
```

## 🧪 故障排查

### 后端无法启动

**问题：** `ModuleNotFoundError: No module named 'fastapi'`

**解决：**
```bash
pip install -r requirements.txt
```

### 前端无法连接到后端

**问题：** 控制台看到 CORS 错误

**解决：** 
- 确保后端正在运行：`http://localhost:8080/api/health`
- 检查 `frontend/vite.config.js` 中的代理配置

### 日志不显示

**问题：** 日志窗口为空

**解决：**
1. 检查 `logs/` 目录是否存在
2. 检查 `manage_services.py` 是否有写入日志
3. 确保用户有读取权限

### 端口已被占用

**问题：** `Address already in use`

**解决：**
```bash
# 查找占用端口的进程
lsof -i :8080    # 后端
lsof -i :5173    # 前端

# 强制关闭
kill -9 <PID>
```

或使用不同的端口：
```bash
python dashboard_api.py --port 9000
cd frontend && npm run dev -- --port 3000
```

## 📦 依赖项

### 后端
- **fastapi** - 现代 Web 框架
- **uvicorn** - ASGI 服务器
- **pydantic** - 数据验证
- **python-dotenv** - 环境变量管理

### 前端
- **vue** - 响应式 UI 框架
- **vite** - 构建工具
- **tailwindcss** - CSS 框架
- **postcss** - CSS 处理

## 🔄 自动刷新配置

### 状态刷新频率

`frontend/src/App.vue` 中修改：
```javascript
// 改为其他毫秒数（如 10000 = 10 秒）
statusInterval = setInterval(refreshStatus, 5000)
```

### 日志刷新频率
```javascript
// 改为其他毫秒数（如 5000 = 5 秒）
logsInterval = setInterval(() => {
  if (selectedService.value && !logPaused.value) {
    loadLogs(selectedService.value)
  }
}, 2000)
```

## 📝 日志格式

日志文件位置：`logs/platform.log` 和 `logs/service_*.log`

日志格式：
```
2024-02-05 10:30:45,123 - manage_services - INFO - Platform started successfully
```

## 🎯 常见任务

### 重启所有服务
点击仪表板中的 **Stop**，然后 **Start** 按钮

### 查看特定错误
在日志查看器中使用 Search 功能搜索 "ERROR"

### 导出日志分析
使用 **Download** 按钮下载日志文件，用文本编辑器或日志分析工具打开

## 💡 性能优化提示

1. **日志行数** - 减少返回的日志行数以加快加载速度
2. **刷新频率** - 降低自动刷新频率以减少 API 调用
3. **前端构建** - 运行 `npm run build` 创建优化的生产版本
4. **浏览器** - 使用现代浏览器（Chrome、Firefox、Safari）获得最佳体验

## 📚 进阶用法

### 与现有服务管理器集成

`dashboard_api.py` 与 `manage_services.py` 无缝集成：
- 读取 `services_config.json`
- 监控 `*.pid` 文件
- 读取 `logs/` 目录中的日志文件
- 通过 subprocess 调用管理器命令

### 自定义日志解析

修改 `dashboard_api.py` 中的 `extract_log_level()` 函数：

```python
def extract_log_level(log_line: str) -> str:
    """自定义日志等级提取逻辑"""
    if "custom_error" in log_line:
        return "ERROR"
    return "INFO"
```

## 🔐 安全建议

1. **生产环境** - 在反向代理（Nginx/Apache）后运行
2. **认证** - 可添加 JWT 认证（FastAPI-JWT 库）
3. **HTTPS** - 使用 SSL/TLS 加密
4. **访问控制** - 限制 API 访问范围

## 🤝 贡献

欢迎提交问题和拉取请求！

## 📄 许可证

MIT License

## 📞 支持

如有问题，请检查：
1. Python 版本：`python --version`（需要 3.9+）
2. Node 版本：`node --version`（需要 14+）
3. 日志文件：查看 `logs/` 目录
4. API 健康检查：`curl http://localhost:8080/api/health`

---

**最后更新：** 2024-02-05  
**作者：** Service Manager Team
