# Service Manager Dashboard - Quick Reference

## 🚀 快速启动

```bash
# 一键启动所有服务
./dev-start.sh

# 仅启动后端
./dev-start.sh backend

# 仅启动前端
./dev-start.sh frontend

# 停止所有服务
./dev-start.sh stop
```

## 🌐 访问地址

| 服务 | URL | 说明 |
|------|-----|------|
| 仪表板 | http://localhost:5173 | Web UI 界面 |
| 后端 API | http://localhost:8080 | 后端服务 |
| Swagger 文档 | http://localhost:8080/api/docs | 交互式 API 文档 |
| ReDoc 文档 | http://localhost:8080/api/redoc | 静态 API 文档 |
| 健康检查 | http://localhost:8080/api/health | 服务健康状态 |

## 📋 API 速查表

### 获取状态
```bash
curl http://localhost:8080/api/status
```

### 启动/停止服务
```bash
# 启动平台
curl -X POST http://localhost:8080/api/control \
  -H "Content-Type: application/json" \
  -d '{"action": "start"}'

# 停止平台
curl -X POST http://localhost:8080/api/control \
  -H "Content-Type: application/json" \
  -d '{"action": "stop"}'

# 重启平台
curl -X POST http://localhost:8080/api/control \
  -H "Content-Type: application/json" \
  -d '{"action": "restart"}'
```

### 获取日志
```bash
# 获取最后 100 行日志
curl "http://localhost:8080/api/logs?service=platform&lines=100"

# 搜索日志
curl "http://localhost:8080/api/logs?service=platform&search=ERROR"

# 下载日志
curl "http://localhost:8080/api/logs/download?service=platform" > logs.txt
```

## 📁 文件结构速查

```
service/
├── dashboard_api.py          # 后端主文件（FastAPI）
├── manage_services.py        # 服务管理器
├── requirements.txt          # Python 依赖
├── dev-start.sh             # 开发启动脚本 ⭐
├── setup.sh                 # 环境初始化
├── frontend/
│   ├── src/
│   │   ├── App.vue         # 主 UI 组件
│   │   ├── main.js         # 入口文件
│   │   └── style.css       # 样式
│   ├── package.json        # npm 配置
│   └── vite.config.js      # Vite 配置
├── logs/                   # 日志目录（自动创建）
└── DASHBOARD_README.md     # 完整文档
```

## 🔧 常用命令

### 安装依赖
```bash
# 完整初始化
./setup.sh

# 或手动安装
pip install -r requirements.txt
cd frontend && npm install
```

### 后端开发

```bash
# 安装依赖
pip install -r requirements.txt

# 启动（自动重载）
python dashboard_api.py --reload

# 指定端口
python dashboard_api.py --port 9000

# 生产模式
python dashboard_api.py --host 0.0.0.0 --port 8080
```

### 前端开发

```bash
cd frontend

# 安装依赖
npm install

# 开发服务器
npm run dev

# 生产构建
npm run build

# 预览构建结果
npm run preview
```

## 🐛 常见问题

### 端口占用
```bash
# 查看占用的进程
lsof -i :8080    # 后端
lsof -i :5173    # 前端

# 终止进程
kill -9 <PID>
```

### 依赖安装失败
```bash
# 清除缓存重试
pip cache purge
pip install -r requirements.txt --no-cache-dir

# npm 清除缓存
npm cache clean --force
npm install --legacy-peer-deps
```

### 模块找不到
```bash
# 后端
pip install -r requirements.txt

# 前端
cd frontend
rm -rf node_modules package-lock.json
npm install
```

## 🎯 开发工作流

### 添加后端接口

1. 编辑 `dashboard_api.py`
```python
@app.get("/api/new-endpoint")
async def new_endpoint():
    return {"data": "value"}
```

2. 刷新浏览器即可调用

### 修改前端 UI

1. 编辑 `frontend/src/App.vue`
2. 热模块替换自动更新浏览器

### 修改样式

1. 编辑 `frontend/src/style.css` 或 `tailwind.config.js`
2. 自动应用到 UI

## 📊 监控和调试

### 查看实时日志
```bash
# 平台日志
tail -f logs/platform.log

# 服务日志
tail -f logs/service_a.log
```

### 检查服务状态
```bash
# 查看 PID
cat service/platform.pid
cat service/service_a.pid

# 查看进程
ps aux | grep python
ps aux | grep manage_services
```

### 浏览器调试
1. 打开 DevTools（F12）
2. 查看 Console 获取错误
3. Network 标签查看 API 调用
4. 连接 WebSocket 查看实时日志

## 🔐 生产部署建议

1. **不使用 --reload 标志**
   ```bash
   python dashboard_api.py --host 0.0.0.0 --port 8080
   ```

2. **构建前端**
   ```bash
   cd frontend && npm run build
   ```

3. **使用反向代理**（Nginx）
   ```nginx
   server {
       listen 80;
       server_name example.com;
       
       location / {
           proxy_pass http://localhost:8080;
       }
   }
   ```

4. **使用进程管理器**（PM2）
   ```bash
   npm install -g pm2
   pm2 start dashboard_api.py --name dashboard
   ```

## 📚 文档链接

- [FastAPI 文档](https://fastapi.tiangolo.com/)
- [Vue 3 文档](https://vuejs.org/)
- [Vite 文档](https://vitejs.dev/)
- [Tailwind CSS 文档](https://tailwindcss.com/)

## 💡 提示和技巧

1. **快速刷新状态** - 点击仪表板的 "🔄 Refresh" 按钮
2. **搜索日志** - 使用日志查看器中的搜索框
3. **暂停日志** - 点击 "⏸️ Pause" 停止实时更新
4. **下载日志** - 点击 "⬇️ Download" 导出日志文件
5. **查看 API 文档** - 访问 http://localhost:8080/api/docs

---

**需要帮助？** 查看 `DASHBOARD_README.md` 获取更多详细信息。
