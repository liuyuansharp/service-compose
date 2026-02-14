[English](README.md) | [中文](README.zh-CN.md)

---

# ServiceCompose

<p align="center">
  <img src="frontend/public/favicon.svg" width="80" height="80" alt="ServiceCompose Logo">
</p>

<h1 align="center">ServiceCompose</h1>

<p align="center">
  <strong>Lightweight Service Orchestration Tool — Unified CLI + WebUI Management</strong>
</p>

<p align="center">
  <a href="#license"><img src="https://img.shields.io/badge/license-MIT-blue.svg" alt="License: MIT"></a>
  <img src="https://img.shields.io/badge/python-3.9%2B-brightgreen.svg" alt="Python 3.9+">
  <img src="https://img.shields.io/badge/vue-3.x-42b883.svg" alt="Vue 3">
  <img src="https://img.shields.io/badge/fastapi-0.104-009688.svg" alt="FastAPI">
  <img src="https://img.shields.io/badge/platform-linux-lightgrey.svg" alt="Platform: Linux">
</p>

<p align="center">
  <a href="#-quick-start">Quick Start</a> •
  <a href="#-features">Features</a> •
  <a href="#-tech-stack">Tech Stack</a> •
  <a href="#-examples">Examples</a> •
  <a href="#-contributing">Contributing</a>
</p>

---

# English version

<!-- 以下为英文内容，原中文内容请见 README.zh-CN.md -->

## 📖 Introduction

**ServiceCompose** is a lightweight tool for orchestrating and managing multiple services. It allows you to define, start, stop, and monitor multiple service processes with a single YAML configuration file. It provides both **CLI** and **WebUI** interfaces, making it suitable for development, testing, and lightweight production environments.

> *Manage your native processes declaratively, just like docker-compose.*

## 🖼️ Preview

<p align="center">
  <img src="doc/imgs/preview.gif" alt="ServiceCompose Dashboard Preview" width="960">
</p>

<details>
<summary>📸 View Static Screenshots</summary>

| # | Screenshot |
|---|------|
| 1 | ![](doc/imgs/1.png) |
| 2 | ![](doc/imgs/2.png) |
| 3 | ![](doc/imgs/3.png) |
| 4 | ![](doc/imgs/4.png) |
| 5 | ![](doc/imgs/5.png) |
| 6 | ![](doc/imgs/6.png) |
| 7 | ![](doc/imgs/7.png) |
| 8 | ![](doc/imgs/8.png) |
| 9 | ![](doc/imgs/9.png) |
| 10 | ![](doc/imgs/10.png) |
| 11 | ![](doc/imgs/11.png) |

</details>


## ✨ Features

### 🖥️ CLI

- **Declarative Configuration** — Define services, commands, arguments, and dependencies using YAML
- **Dependency Topology Sorting** — Automatically determine the start/stop order based on the dependency graph, with support for circular dependency detection
- **Process Daemon** — Automatically restart on crash, with built-in exponential backoff and restart storm protection
- **PID Management** — Automatically record and clean up PID files
- **Rolling Logs** — Independent log files for each service, with automatic rotation

### 🌐 WebUI

- **Real-time Monitoring** — Real-time metrics for CPU, memory, disk, and network IO, with detailed per-core usage
- **Service Control** — One-click start/stop/restart, with support for batch operations
- **Real-time Logs** — WebSocket-pushed log streams, with level filtering, keyword search, and historical replay
- **Dependency Workflows** — Visual service dependency topology (topology view + force-directed view)
- **Process Tree** — View the parent-child process relationships of services and the resource consumption of each process
- **System Metrics Trends** — Historical trend charts for CPU/memory usage, with up to 30 days of retention
- **Scheduled Restart** — Cron-style scheduled restart policies, with support for weekly configuration
- **Hot Update & Rollback** — Upload `.tar.gz` update packages for online upgrades, with one-click rollback to previous versions
- **User Permissions** — Multi-role permission system (admin/operator/read-only), with JWT authentication
- **Visible Cards** — Configure the visibility of dashboard service cards per user
- **Operation Audit** — Complete record of all user operation histories
- **Web Terminal** — Embedded xterm.js terminal, allowing direct server operations in the browser
- **Internationalization** — Chinese/English bilingual switch
- **Dark Mode** — Free switch between light and dark themes

## 🏗️ Tech Stack

| Layer       | Technology                                                        |
| ----------- | --------------------------------------------------------------- |
| **Backend** | Python 3.9+, FastAPI, Uvicorn, SQLAlchemy, psutil, PyYAML       |
| **Frontend**| Vue 3, Vite, Tailwind CSS, ECharts, xterm.js                   |
| **Authentication** | JWT (python-jose), bcrypt (passlib)                             |
| **Communication** | RESTful API + WebSocket                                         |
| **Build**   | Cython compilation (optional), Vite packaging, Shell script for one-click build               |

## 📁 Project Structure

```
service-compose/
├── backend/                  # Backend Python source code
│   ├── app.py                # FastAPI main entry & API routes
│   ├── service_compose.py    # CLI core: process management & dependency orchestration
│   ├── services.py           # System metrics collection & heartbeat detection
│   ├── auth.py               # JWT authentication & user management
│   ├── config.py             # Global configuration & constants
│   ├── models.py             # Pydantic data models
│   ├── logs.py               # Log chain reading & rotation
│   ├── tasks.py              # Background scheduled tasks
│   ├── scheduled.py          # Scheduled restart parsing
│   ├── audit.py              # Operation audit logs
│   └── update.py             # Hot update & rollback
├── frontend/                 # Frontend Vue 3 source code
│   ├── src/
│   │   ├── components/       # Vue components
│   │   └── composables/      # Composable functions (hooks)
│   └── package.json
├── examples/
│   ├── services.yaml         # Example configuration file
│   └── dummy_service.sh      # Example service script
├── build.sh                  # One-click build and package script
├── start_all.sh              # One-click start (services + API)
├── stop_all.sh               # One-click stop
├── requirements.txt          # Python dependencies
└── README.md
```

## 🚀 Quick Start

### Environment Requirements

- Python 3.9+
- Node.js 16+ (only required for frontend development)
- Linux operating system

### 1. Install Dependencies

```bash
# Clone the repository
git clone https://github.com/liuyuansharp/service-compose.git
cd service-compose

# Install Python dependencies
pip install -r requirements.txt

# Install frontend dependencies (optional, only needed during development)
cd frontend && npm install && cd ..
```

### 2. Write Configuration File

Create `services.yaml`:

```yaml
services:
  - name: gateway
    cmd: ./start_gateway.sh
    args: []
    restart_on_exit: true
    heartbeat: http://localhost:8000/health
    depends_on: []

  - name: user-service
    cmd: python3
    args: ["-m", "user_service.main"]
    restart_on_exit: true
    heartbeat: http://localhost:8001/health
    depends_on:
      - gateway

  - name: order-service
    cmd: python3
    args: ["-m", "order_service.main"]
    restart_on_exit: true
    heartbeat: http://localhost:8002/health
    scheduled_restart:
      enabled: true
      cron: "03:00"
    depends_on:
      - gateway

run_dir: ./.services
```

### 3. Start Using CLI

```bash
# Start all services (in dependency order)
python3 -m backend.service_compose start --config services.yaml

# Start a single service
python3 -m backend.service_compose start --config services.yaml --service gateway

# Check status
python3 -m backend.service_compose status --config services.yaml

# Stop all services (in reverse dependency order)
python3 -m backend.service_compose stop --config services.yaml

# Restart a single service (in daemon mode)
python3 -m backend.service_compose restart --config services.yaml --service user-service --daemon
```

### 4. Use WebUI

```bash
# One-click start (service processes + API backend)
./start_all.sh services.yaml

# Or manually start the backend API
python3 -m backend.app --config services.yaml --host 0.0.0.0 --port 8080

# Start frontend in development mode
cd frontend && npm run dev
```

Visit `http://localhost:8080` to open the dashboard (default user: `admin` / `admin`).

## 📝 Examples

### Quick Experience (Example Service)

```bash
# Use the provided example configuration and script
./start_all.sh examples/services.yaml

# Browser access
# Dashboard: http://localhost:8080
# API Documentation: http://localhost:8080/api/docs

# Stop
./stop_all.sh examples/services.yaml
```

### Production Build

```bash
# Full build (Cython compilation + frontend packaging + tar.gz)
./build.sh --version 1.2.0

# Skip frontend compilation
./build.sh --skip-frontend

# Skip Cython compilation
./build.sh --skip-cython
```

### Configuration Explanation

| Field                | Type     | Description                                      |
| ------------------- | -------- | --------------------------------------------- |
| `name`              | string   | Service name (unique identifier)                |
| `cmd`               | string   | Start command (supports relative paths, relative to the configuration file directory)   |
| `args`              | string[] | List of start arguments                          |
| `restart_on_exit`   | bool     | Whether to automatically restart the process after exit (exponential backoff)             |
| `heartbeat`         | string   | Heartbeat detection URL or `mock`                |
| `depends_on`        | string[] | List of service names that this service depends on (determines start/stop order)               |
| `scheduled_restart` | object   | Scheduled restart configuration                  |
| `run_dir`           | string   | Runtime directory (where logs and PID files are stored)           |

### API Endpoints Overview

| Method     | Path                         | Description            |
| -------- | ---------------------------- | ------------- |
| `POST`   | `/api/login`                 | User login        |
| `GET`    | `/api/status`                | Dashboard status      |
| `POST`   | `/api/services/{name}/start` | Start service        |
| `POST`   | `/api/services/{name}/stop`  | Stop service        |
| `POST`   | `/api/services/{name}/restart` | Restart service      |
| `GET`    | `/api/logs/{name}`           | Get service logs    |
| `GET`    | `/api/metrics/{name}`        | Get monitoring metrics    |
| `WS`     | `/api/ws/logs/{name}`        | Real-time log stream      |
| `WS`     | `/api/ws/terminal`           | Web terminal        |
| `GET`    | `/api/docs`                  | Swagger API documentation |

For the complete API documentation, please start the service and visit `/api/docs`.


## 🤝 Contributing

Contributions are welcome! Please read [CONTRIBUTING.md](CONTRIBUTING.md) before submitting a PR.

1. Fork this repository
2. Create a feature branch (`git checkout -b feature/awesome-feature`)
3. Commit your changes (`git commit -m 'feat: add awesome feature'`)
4. Push to the branch (`git push origin feature/awesome-feature`)
5. Create a Pull Request

## 📄 License

This project is licensed under the [MIT License](LICENSE).

---

<p align="center">
  Made with ❤️ by <a href="https://github.com/liuyuansharp">ServiceCompose Contributors</a>
</p>