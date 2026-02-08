# 📱 Service Manager Dashboard - 使用指南

## 🎯 快速开始

### 方式 1: 一键启动（推荐）

```bash
cd /home/liuyuan/workspace/work/fsys/service
./dev-start.sh
```

该脚本会：
- ✅ 检查 Python 环境
- ✅ 安装依赖
- ✅ 启动后端服务（FastAPI）
- ✅ 启动前端服务（Vite）
- ✅ 自动打开浏览器（http://localhost:5173）

### 方式 2: 手动启动

#### 启动后端
```bash
cd /home/liuyuan/workspace/work/fsys/service
python3 dashboard_api.py --host 0.0.0.0 --port 8080
```

#### 启动前端
```bash
cd /home/liuyuan/workspace/work/fsys/service/frontend
npm install  # 首次需要
npm run dev
```

---

## 🌐 访问地址

| 服务 | 地址 | 说明 |
|------|------|------|
| **仪表板** | http://localhost:5173 | 主要的 Web 界面 |
| **API** | http://localhost:8080 | 后端 REST API |
| **API 文档** | http://localhost:8080/api/docs | Swagger UI（交互式） |
| **API 文档** | http://localhost:8080/api/redoc | ReDoc（只读） |
| **健康检查** | http://localhost:8080/api/health | 服务健康状态 |

---

## 🎨 仪表板功能

### 1. 状态概览
- **整体状态**：显示平台和服务的总体状态
- **活跃服务数**：实时显示运行中的服务数量
- **最后更新**：显示状态最后更新时间

### 2. 平台监控
- 显示平台服务的 PID（进程 ID）
- 显示最新的日志片段
- 提供启动/停止/重启按钮

### 3. 微服务监控
- 网格视图显示所有微服务
- 每个服务卡片显示：
  - 服务名称
  - 运行状态（✓ 运行中 / ✗ 已停止）
  - 操作按钮（启动/停止/重启）

### 4. 日志查看器
- **查看日志**：实时查看每个服务的日志
- **搜索日志**：按关键词搜索日志内容
- **日志着色**：
  - 🔴 ERROR（红色）
  - 🟡 WARNING（黄色）
  - 🟢 INFO（绿色）
  - 🔵 DEBUG（蓝色）
- **日志下载**：下载完整日志文件
- **日志控制**：暂停/恢复/清空日志实时流

---

## 🔌 API 端点

### 健康检查
```bash
# 检查服务健康状态
curl http://localhost:8080/api/health
```

返回：
```json
{
  "status": "healthy",
  "timestamp": "2026-02-05T22:31:10.702884"
}
```

### 获取状态
```bash
# 获取所有服务的状态
curl http://localhost:8080/api/status
```

### 获取日志
```bash
# 获取平台日志
curl http://localhost:8080/api/logs?service=platform

# 获取特定服务日志
curl http://localhost:8080/api/logs?service=service_a

# 搜索日志
curl http://localhost:8080/api/logs?search=ERROR

# 限制行数
curl http://localhost:8080/api/logs?lines=50
```

### 下载日志
```bash
# 下载日志文件
curl http://localhost:8080/api/logs/download?service=platform -o platform.log
```

### 服务控制
```bash
# 启动服务
curl -X POST http://localhost:8080/api/control \
  -H "Content-Type: application/json" \
  -d '{"service": "service_a", "action": "start"}'

# 停止服务
curl -X POST http://localhost:8080/api/control \
  -H "Content-Type: application/json" \
  -d '{"service": "service_a", "action": "stop"}'

# 重启服务
curl -X POST http://localhost:8080/api/control \
  -H "Content-Type: application/json" \
  -d '{"service": "service_a", "action": "restart"}'
```

---

## 🧪 测试 API

### Bash 测试脚本
```bash
cd /home/liuyuan/workspace/work/fsys/service
./test-api.sh http://localhost:8080
```

### Python 测试脚本
```bash
cd /home/liuyuan/workspace/work/fsys/service
python3 test_api.py http://localhost:8080
```

### 使用 pytest 运行完整测试
```bash
pip install pytest
pytest -v
```

---

## 📝 配置说明

### 后端配置 (dashboard_api.py)

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `--host` | 0.0.0.0 | 监听地址 |
| `--port` | 8080 | 监听端口 |
| `--reload` | False | 开发模式（文件变更自动重载） |

### 前端配置 (vite.config.js)

```javascript
// API 代理配置
proxy: {
  '/api': {
    target: 'http://localhost:8080',
    changeOrigin: true
  }
}
```

### 环境变量

创建 `.env` 文件或 `.env.local` 文件：

```bash
# 后端
PYTHON_ENV=development
LOG_LEVEL=INFO
LOG_DIR=./logs

# 前端
VITE_API_URL=http://localhost:8080
```

---

## 🐛 故障排查

### 问题：端口已被占用

**症状**：启动时报错 "Address already in use"

**解决方案**：
```bash
# 查找占用端口的进程
lsof -i :8080
lsof -i :5173

# 强制杀死进程（谨慎使用）
pkill -f "python3 dashboard_api"
pkill -f "npm run dev"

# 或使用指定 PID 杀死
kill -9 <PID>
```

### 问题：依赖不完整

**症状**：启动时报错 "ModuleNotFoundError"

**解决方案**：
```bash
# Python 依赖
pip install -r requirements.txt

# Node.js 依赖
cd frontend
npm install --legacy-peer-deps
```

### 问题：Hot Module Reload (HMR) 不工作

**症状**：修改代码后页面不自动刷新

**解决方案**：
1. 检查浏览器控制台是否有错误
2. 重启 Vite 开发服务器：`npm run dev`
3. 清理浏览器缓存（Ctrl+Shift+Delete）

### 问题：API 无响应

**症状**：前端显示 "Cannot GET /api/status"

**解决方案**：
```bash
# 检查后端是否运行
ps aux | grep python3

# 检查端口监听
lsof -i :8080

# 重启后端
pkill -f "python3 dashboard_api"
python3 dashboard_api.py --host 0.0.0.0 --port 8080
```

---

## 📊 日志管理

### 日志位置

```
/home/liuyuan/workspace/work/fsys/service/logs/
├── platform.log          # 平台日志
├── service_a.log         # 服务 A 日志
├── service_b.log         # 服务 B 日志
├── service_c.log         # 服务 C 日志
├── service_d.log         # 服务 D 日志
└── service_e.log         # 服务 E 日志
```

### 日志轮转策略

- 单个日志文件最大：10MB
- 备份文件数量：5 个
- 超出时自动轮转（按时间或大小）

### 查看日志

```bash
# 实时查看平台日志
tail -f logs/platform.log

# 查看错误日志
grep ERROR logs/*.log

# 统计日志条数
wc -l logs/*.log

# 清空某个日志（不推荐）
> logs/platform.log
```

---

## 🚀 生产部署

### 方式 1：使用 systemd

```bash
# 复制 systemd 服务文件
sudo cp systemd/app-manager.service /etc/systemd/system/

# 启用服务
sudo systemctl enable app-manager
sudo systemctl start app-manager

# 查看状态
sudo systemctl status app-manager

# 查看日志
sudo journalctl -u app-manager -f
```

### 方式 2：使用 PM2

```bash
# 全局安装 PM2
npm install -g pm2

# 启动应用
pm2 start dashboard_api.py --name "dashboard-api"
pm2 start "npm run build && npm run preview" --cwd frontend --name "dashboard-frontend"

# 设置开机自启
pm2 startup
pm2 save

# 查看进程
pm2 list
pm2 log dashboard-api
```

### 方式 3：使用 Nginx 反向代理

```nginx
upstream dashboard_api {
    server localhost:8080;
}

upstream dashboard_frontend {
    server localhost:5173;
}

server {
    listen 80;
    server_name yourdomain.com;

    # 前端
    location / {
        proxy_pass http://dashboard_frontend;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
    }

    # API
    location /api {
        proxy_pass http://dashboard_api;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

---

## 💡 最佳实践

### 开发

1. ✅ 使用 `npm run dev` 进行开发（启用 HMR）
2. ✅ 使用浏览器 DevTools 调试前端
3. ✅ 使用 `/api/docs` 测试 API
4. ✅ 定期查看后端日志

### 生产

1. ✅ 使用 `npm run build` 构建前端
2. ✅ 使用反向代理（如 Nginx）
3. ✅ 启用 HTTPS
4. ✅ 配置日志轮转
5. ✅ 设置自动重启机制
6. ✅ 监控应用性能

---

## 📚 更多文档

- [QUICK_START.md](./QUICK_START.md) - 快速开始指南
- [DASHBOARD_README.md](./DASHBOARD_README.md) - 完整的仪表板文档
- [SETUP.md](./SETUP.md) - 部署和配置指南
- [PROJECT_CHECKLIST.md](./PROJECT_CHECKLIST.md) - 项目清单
- [IMPLEMENTATION_COMPLETE.md](./IMPLEMENTATION_COMPLETE.md) - 实现总结

---

## 🆘 获取帮助

### 检查系统信息

```bash
# Python 版本
python3 --version

# Node.js 版本
node --version
npm --version

# 环境变量
env | grep -i python

# 已安装的 Python 包
pip list | grep -E "fastapi|uvicorn|pydantic"
```

### 查看后端日志

```bash
# 查看启动日志
tail -50 logs/platform.log

# 查看错误
grep ERROR logs/*.log

# 实时监控
tail -f logs/platform.log | grep ERROR
```

### 联系支持

遇到问题？请：

1. 查看上述故障排查部分
2. 检查日志文件
3. 运行测试脚本：`python3 test_api.py http://localhost:8080`
4. 查看文档文件夹中的相关文档

---

## 📞 常见问题 (FAQ)

**Q：如何更改监听端口？**
A：修改启动命令：`python3 dashboard_api.py --port 9000`

**Q：如何启用 HTTPS？**
A：使用 Nginx/Apache 反向代理，或使用 uvicorn 的 SSL 参数

**Q：如何集成真实的服务管理器？**
A：编辑 `dashboard_api.py`，修改 `/api/control` 端点的 `subprocess.run()` 调用

**Q：支持多用户并发访问吗？**
A：是的，FastAPI 原生支持异步并发处理

**Q：日志会永久保存吗？**
A：日志按轮转策略保存（最多 5 个备份文件）

---

## ✅ 检查清单

启动前检查：

- [ ] Python 3.9+ 已安装
- [ ] Node.js 14+ 已安装
- [ ] 依赖已安装（`pip install -r requirements.txt`）
- [ ] 前端依赖已安装（`npm install`）
- [ ] 端口 8080 和 5173 未被占用
- [ ] 日志目录可写（`logs/`）

启动后验证：

- [ ] 后端运行正常（进程出现在 `ps aux`）
- [ ] 前端运行正常（进程出现在 `ps aux`）
- [ ] 健康检查通过（`curl http://localhost:8080/api/health`）
- [ ] 仪表板可访问（http://localhost:5173）
- [ ] API 文档可访问（http://localhost:8080/api/docs）

---

## 🎉 完成！

现在你已准备好使用 Service Manager Dashboard 了！

享受实时监控和服务管理的便利！ 🚀

---

**最后更新**：2026-02-05  
**版本**：1.0.0  
**状态**：✅ 可投入生产
