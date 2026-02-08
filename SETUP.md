# 项目初始化和部署指南

## 📖 目录

1. [环境要求](#环境要求)
2. [项目结构](#项目结构)
3. [初始化步骤](#初始化步骤)
4. [本地开发](#本地开发)
5. [生产部署](#生产部署)
6. [常见问题](#常见问题)
7. [维护和监控](#维护和监控)

## 环境要求

### 必需

- **Python 3.9 或更高版本**
  ```bash
  python --version  # 查看版本
  ```

- **Node.js 14+ 和 npm** (仅前端开发所需)
  ```bash
  node --version
  npm --version
  ```

### 推荐

- **Git** - 版本控制
- **curl 或 Postman** - API 测试
- **文本编辑器** - VS Code、PyCharm 等

## 项目结构

```
service/
├── 📄 dashboard_api.py              # FastAPI 后端应用（主文件）
├── 📄 manage_services.py            # 服务管理器脚本
├── 📄 services_config.json          # 服务配置
├── 📄 requirements.txt              # Python 依赖
├── 📄 setup.sh                      # 环境初始化脚本
├── 📄 dev-start.sh                  # 开发启动脚本 ⭐
├── 📄 test-api.sh                   # API 测试脚本
├── 📂 frontend/                     # Vue3 前端应用
│   ├── 📂 src/
│   │   ├── App.vue                  # 主组件
│   │   ├── main.js                  # 入口文件
│   │   └── style.css                # 全局样式
│   ├── 📄 index.html                # HTML 模板
│   ├── 📄 vite.config.js            # Vite 配置
│   ├── 📄 tailwind.config.js        # Tailwind 主题
│   ├── 📄 postcss.config.js         # PostCSS 配置
│   ├── 📄 package.json              # npm 依赖
│   └── 📄 .gitignore
├── 📂 logs/                         # 日志目录（自动创建）
├── 📄 DASHBOARD_README.md           # 完整使用文档
├── 📄 QUICK_START.md                # 快速参考
└── 📄 SETUP.md                      # 本文件
```

## 初始化步骤

### 第 1 步：克隆或进入项目

```bash
cd /home/liuyuan/workspace/work/fsys/service
```

### 第 2 步：自动初始化（推荐）

运行一键初始化脚本：

```bash
chmod +x setup.sh dev-start.sh test-api.sh
./setup.sh
```

脚本会自动：
1. 检查 Python 环境
2. 安装 Python 依赖
3. 创建虚拟环境（可选）
4. 创建日志目录
5. 安装 Node.js 依赖（如果安装了 Node）

### 第 3 步：手动初始化（可选）

如果脚本失败，可以手动执行：

```bash
# 创建虚拟环境（可选但推荐）
python3 -m venv venv
source venv/bin/activate  # Linux/Mac
# 或 venv\Scripts\activate  # Windows

# 安装 Python 依赖
pip install -r requirements.txt

# 创建日志目录
mkdir -p logs

# 安装前端依赖（如果有 Node.js）
cd frontend
npm install
cd ..
```

## 本地开发

### 快速启动

最简单的方式是运行启动脚本：

```bash
./dev-start.sh
```

这会自动：
- 启动 FastAPI 后端（http://localhost:8080）
- 启动 Vite 前端服务器（http://localhost:5173）
- 在浏览器中打开仪表板

### 分别启动（推荐用于调试）

**终端 1 - 后端：**
```bash
# 激活虚拟环境（如果创建了）
source venv/bin/activate

# 启动后端，支持自动重载
python dashboard_api.py --reload
```

**终端 2 - 前端：**
```bash
cd frontend
npm run dev
```

**终端 3 - 查看日志：**
```bash
tail -f logs/platform.log
tail -f logs/service_a.log
```

### 验证部署

运行测试脚本验证所有 API 端点：

```bash
chmod +x test-api.sh
./test-api.sh
```

预期输出：
```
Testing backend: http://localhost:8080
...
All tests passed! ✓
```

## 生产部署

### 部署前准备

1. **构建前端**
   ```bash
   cd frontend
   npm run build
   # 生成的文件在 dist/ 目录
   cd ..
   ```

2. **安装生产依赖**
   ```bash
   pip install -r requirements.txt
   ```

3. **创建日志目录**
   ```bash
   mkdir -p logs
   chmod 755 logs
   ```

4. **设置权限**
   ```bash
   chmod +x dashboard_api.py
   chmod +x manage_services.py
   ```

### 运行生产服务器

```bash
# 不使用 --reload 标志（热重载仅用于开发）
python dashboard_api.py --host 0.0.0.0 --port 8080
```

### 使用 Systemd 服务（Linux）

创建服务文件 `/etc/systemd/system/dashboard.service`：

```ini
[Unit]
Description=Service Manager Dashboard
After=network.target

[Service]
Type=simple
User=app
WorkingDirectory=/path/to/service
ExecStart=/usr/bin/python3 /path/to/service/dashboard_api.py --host 0.0.0.0 --port 8080
Restart=on-failure
RestartSec=10

[Install]
WantedBy=multi-user.target
```

启用和启动：
```bash
sudo systemctl enable dashboard
sudo systemctl start dashboard
sudo systemctl status dashboard
```

### 使用 PM2（推荐）

```bash
# 全局安装 PM2
npm install -g pm2

# 启动应用
pm2 start dashboard_api.py --name dashboard --interpreter python3

# 查看状态
pm2 status

# 设置开机自启
pm2 startup
pm2 save
```

### 使用反向代理（Nginx）

创建 Nginx 配置 `/etc/nginx/sites-available/dashboard`：

```nginx
server {
    listen 80;
    server_name your-domain.com;

    # 静态文件
    location / {
        proxy_pass http://localhost:8080;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # WebSocket
    location /api/ws {
        proxy_pass http://localhost:8080;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
    }
}
```

启用配置：
```bash
sudo ln -s /etc/nginx/sites-available/dashboard /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

### 使用 HTTPS（Let's Encrypt）

```bash
sudo apt install certbot python3-certbot-nginx
sudo certbot --nginx -d your-domain.com
```

## 常见问题

### Q: 后端启动失败 - "ModuleNotFoundError: No module named 'fastapi'"

**A:** 安装 Python 依赖
```bash
pip install -r requirements.txt
```

### Q: 前端连接不到后端 - CORS 错误

**A:** 
1. 确保后端正在运行：http://localhost:8080/api/health
2. 检查 `frontend/vite.config.js` 中的代理设置
3. 清除浏览器缓存：Ctrl+Shift+Delete

### Q: 端口 8080 或 5173 被占用

**A:** 
```bash
# 查找占用的进程
lsof -i :8080
lsof -i :5173

# 杀死进程
kill -9 <PID>

# 或使用不同端口
python dashboard_api.py --port 9000
cd frontend && npm run dev -- --port 3000
```

### Q: 日志文件不存在

**A:** 
1. 确保 `logs/` 目录存在：`mkdir -p logs`
2. 确保 `manage_services.py` 在运行
3. 检查目录权限：`chmod 755 logs`

### Q: "Permission denied" 错误

**A:** 
```bash
# 给脚本添加执行权限
chmod +x dev-start.sh setup.sh test-api.sh dashboard_api.py
```

### Q: 修改代码后前端没有更新

**A:** 
1. 确保运行 `npm run dev`（支持热模块替换）
2. 手动刷新浏览器：Ctrl+F5（硬刷新）
3. 清除浏览器缓存

## 维护和监控

### 查看日志

```bash
# 平台日志
tail -f logs/platform.log

# 特定服务日志
tail -f logs/service_a.log

# 搜索错误
grep ERROR logs/*.log

# 查看最后 50 行
tail -50 logs/platform.log
```

### 监控进程

```bash
# 查看 Python 进程
ps aux | grep python

# 查看特定进程详情
ps -ef | grep dashboard

# 查看内存使用
top -p $(pgrep -f dashboard_api)
```

### 性能优化

1. **减少日志刷新频率**
   ```bash
   # 编辑 frontend/src/App.vue
   # 修改 setInterval 的时间间隔
   ```

2. **限制日志行数**
   ```bash
   # 编辑 dashboard_api.py
   # 修改 lines: int = Query(100) 的默认值
   ```

3. **启用 Gzip 压缩**（在 Nginx 中）
   ```nginx
   gzip on;
   gzip_types text/plain application/json;
   ```

### 备份配置

```bash
# 备份服务配置
cp services_config.json services_config.json.backup

# 备份日志
tar -czf logs-backup-$(date +%Y%m%d).tar.gz logs/
```

### 日志清理

```bash
# 删除超过 30 天的日志
find logs/ -name "*.log" -mtime +30 -delete

# 或手动清理
rm logs/old-service.log
```

## 下一步

1. 阅读 [DASHBOARD_README.md](DASHBOARD_README.md) 了解详细使用方法
2. 查看 [QUICK_START.md](QUICK_START.md) 获取常用命令速查
3. 浏览 API 文档：http://localhost:8080/api/docs

## 故障排除清单

- [ ] Python 版本检查：`python --version` >= 3.9
- [ ] Node 版本检查：`node --version` >= 14
- [ ] 依赖安装：`pip install -r requirements.txt`
- [ ] 日志目录：`mkdir -p logs`
- [ ] 脚本权限：`chmod +x *.sh`
- [ ] 后端启动：`python dashboard_api.py --reload`
- [ ] 前端启动：`cd frontend && npm run dev`
- [ ] API 测试：`./test-api.sh`

## 获取帮助

如有问题，请检查：

1. **后端日志** - 查看 console 输出
2. **浏览器控制台** - 按 F12 打开开发者工具
3. **API 文档** - http://localhost:8080/api/docs
4. **日志文件** - `logs/` 目录下的日志

---

**最后更新：** 2024-02-05  
**版本：** 1.0.0
