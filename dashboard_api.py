from fastapi import Request
from fastapi.responses import StreamingResponse
import time
import asyncio
import json
import logging
import os
import subprocess
import tarfile
import shutil
import hashlib
import sys
import urllib.request
import urllib.error
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from collections import deque

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, Query, Depends, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
import uvicorn
import psutil
import uuid
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy import Column, DateTime, Integer, String, create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Get the service manager directory
SERVICE_DIR = Path(__file__).parent
# CONFIG_FILE = SERVICE_DIR / 'services_config.json' 
CONFIG_FILE = SERVICE_DIR / 'examples' / 'services_config_example.json'
LOGS_DIR = SERVICE_DIR / 'logs'

# Ensure logs directory exists
LOGS_DIR.mkdir(exist_ok=True)

# Authentication / Database setup
AUTH_DB_PATH = SERVICE_DIR / 'auth.db'
SECRET_KEY = os.getenv('AUTH_SECRET_KEY', 'change-this-secret')
ALGORITHM = 'HS256'
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv('ACCESS_TOKEN_EXPIRE_MINUTES', '480'))
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
security = HTTPBearer(auto_error=False)

AUTH_DB_URL = f"sqlite:///{AUTH_DB_PATH}"
engine = create_engine(AUTH_DB_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)
Base = declarative_base()


class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False)
    role = Column(String, default="admin", nullable=False)  # admin / operator / readonly
    visible_cards = Column(String, default="", nullable=False)  # JSON array string, empty = all
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)


# Metrics history storage (24h by default)
METRICS_INTERVAL_SECONDS = 10
METRICS_HISTORY_HOURS = 24
MAX_METRICS_POINTS = int(METRICS_HISTORY_HOURS * 3600 / METRICS_INTERVAL_SECONDS)
METRICS_HISTORY: Dict[str, deque] = {}
METRICS_LAST_IO_READ: Dict[str, int] = {}
METRICS_LAST_IO_WRITE: Dict[str, int] = {}
UPDATE_TASKS: Dict[str, Dict] = {}
MAX_LOG_LINES = 500
MAX_LOG_SEARCH_LINES = -1
MAX_METRICS_HISTORY_POINTS = 2000
MAX_LOG_BYTES = 10 * 1024 * 1024       # Single log file max size (10MB, matches RotatingFileHandler)
MAX_LOG_BACKUPS = 3                     # Max backup files per service (.log.1, .log.2, .log.3)
MAX_TOTAL_LOG_BYTES = 500 * 1024 * 1024 # Total log directory size limit (500MB)
LOG_INDEX_STRIDE = 1000
LOG_INDEX_CACHE: Dict[str, Dict] = {}

# Audit log file
AUDIT_LOG_FILE = SERVICE_DIR / 'logs' / 'audit.json'
AUDIT_LOG_MAX_ENTRIES = 5000

# System-level metrics persistent history (CPU% & memory%)
SYSTEM_METRICS_FILE = LOGS_DIR / 'system_metrics_history.json'
SYSTEM_METRICS_PERSIST_INTERVAL = 60  # seconds – append one point per minute
SYSTEM_METRICS_MAX_DAYS = 30
SYSTEM_METRICS_MAX_POINTS = SYSTEM_METRICS_MAX_DAYS * 24 * 60  # 43200 points @ 1min


# ==================== Authentication Helpers ====================

def init_auth_db():
    AUTH_DB_PATH.parent.mkdir(exist_ok=True)
    Base.metadata.create_all(bind=engine)
    # Auto-migrate: add role / visible_cards columns if missing
    import sqlite3
    conn = sqlite3.connect(str(AUTH_DB_PATH))
    cursor = conn.cursor()
    existing = {row[1] for row in cursor.execute("PRAGMA table_info(users)").fetchall()}
    if "role" not in existing:
        cursor.execute("ALTER TABLE users ADD COLUMN role TEXT NOT NULL DEFAULT 'admin'")
    if "visible_cards" not in existing:
        cursor.execute("ALTER TABLE users ADD COLUMN visible_cards TEXT NOT NULL DEFAULT ''")
    conn.commit()
    conn.close()
    session = SessionLocal()
    try:
        count = session.query(User).count()
        if count == 0:
            default_password = os.getenv('DEFAULT_ADMIN_PASSWORD', 'ly1234')
            session.add(User(username='liuyuan', password_hash=pwd_context.hash(default_password), role='admin'))
            session.commit()
            logger.info("Created default admin user 'liuyuan'")
    finally:
        session.close()


def get_user_by_username(username: str) -> Optional[Dict]:
    session = SessionLocal()
    try:
        user = session.query(User).filter(User.username == username).first()
        if not user:
            return None
        # parse visible_cards JSON
        vc = []
        if user.visible_cards:
            try:
                vc = json.loads(user.visible_cards)
            except Exception:
                vc = []
        return {
            "id": user.id,
            "username": user.username,
            "password_hash": user.password_hash,
            "role": user.role or "admin",
            "visible_cards": vc,
            "created_at": user.created_at.isoformat() if user.created_at else None
        }
    finally:
        session.close()


def verify_password(plain_password: str, password_hash: str) -> bool:
    try:
        return pwd_context.verify(plain_password, password_hash)
    except Exception:
        return False


def authenticate_user(username: str, password: str) -> Optional[Dict]:
    user = get_user_by_username(username)
    if not user:
        return None
    if not verify_password(password, user['password_hash']):
        return None
    return user


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def decode_token(token: str) -> Dict:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise HTTPException(status_code=401, detail="Invalid authentication token")
        user = get_user_by_username(username)
        if not user:
            raise HTTPException(status_code=401, detail="User not found")
        return user
    except JWTError as exc:
        logger.warning(f"JWT decode error: {exc}")
        raise HTTPException(status_code=401, detail="Invalid authentication token") from exc


async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    if not credentials:
        raise HTTPException(status_code=401, detail="Not authenticated")
    token = credentials.credentials
    return decode_token(token)


def get_user_from_request(request: Request, token_param: Optional[str] = None) -> Dict:
    token = token_param
    if not token:
        auth_header = request.headers.get('authorization')
        if auth_header and auth_header.lower().startswith('bearer '):
            token = auth_header.split(' ', 1)[1]
    if not token:
        raise HTTPException(status_code=401, detail="Missing authentication token")
    return decode_token(token)
from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app):
    # Startup
    init_auth_db()
    asyncio.create_task(_metrics_sampler())
    asyncio.create_task(_system_metrics_persist_loop())
    asyncio.create_task(_log_maintenance())
    asyncio.create_task(_scheduled_restart_loop())
    yield
    # Shutdown (cleanup if needed)

# Initialize FastAPI app
app = FastAPI(
    title="Service Manager Dashboard API",
    description="Real-time monitoring and control API for platform and microservices",
    version="1.0.0",
    docs_url="/api/docs",
    openapi_url="/api/openapi.json",
    lifespan=lifespan,
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ==================== Pydantic Models ====================

class ServiceStatus(BaseModel):
    name: str
    running: bool
    health: str = "stopped"  # running / stopped / abnormal
    health_reason: Optional[str] = None
    pid: Optional[int] = None
    uptime: Optional[str] = None
    uptime_seconds: Optional[int] = None
    restart_count: int = 0
    last_log: Optional[str] = None
    scheduled_restart: Optional[Dict] = None  # {enabled, cron, last_restart, next_restart}


class PlatformStatus(BaseModel):
    status: str  # "running", "stopped", "error"
    platform: ServiceStatus
    services: List[ServiceStatus]
    timestamp: str


class LogEntry(BaseModel):
    timestamp: str
    level: str
    message: str
    service: str


class ServiceControl(BaseModel):
    action: str  # "start", "stop", "restart"
    service: Optional[str] = None  # None for all, or service name


class BatchServiceControl(BaseModel):
    action: str  # "start", "stop", "restart"
    services: List[str]  # list of service names


class SystemMetrics(BaseModel):
    cpu_percent: float  # CPU 使用率 (0-100)
    cpu_count: int  # CPU 核心数
    cpu_percents: List[float] = []  # 每核 CPU 使用率
    memory_percent: float  # 内存使用率 (0-100)
    memory_used: int  # 已用内存 (MB)
    memory_total: int  # 总内存 (MB)
    disk_percent: float  # 磁盘使用率 (0-100)
    disk_used: int  # 已用磁盘 (GB)
    disk_total: int  # 总磁盘 (GB)
    disk_free: int  # 可用磁盘 (GB)
    timestamp: str


class DiskPartitionInfo(BaseModel):
    device: str
    mountpoint: str
    fstype: str
    total_gb: int
    used_gb: int
    free_gb: int
    percent: float


class DashboardStatus(BaseModel):
    status: str
    platform: ServiceStatus
    services: List[ServiceStatus]
    metrics: SystemMetrics
    timestamp: str


class ServiceInfo(BaseModel):
    name: str
    version: str
    commit_hash: str
    build_date: str
    uptime: Optional[str] = None
    uptime_seconds: Optional[int] = None


class UpdateTaskResponse(BaseModel):
    task_id: str


class UpdateProgress(BaseModel):
    task_id: str
    status: str
    update_progress: int
    message: Optional[str] = None


class BackupInfo(BaseModel):
    name: str
    created_at: str


class LoginRequest(BaseModel):
    username: str
    password: str


class UserProfile(BaseModel):
    username: str
    role: str = "admin"
    visible_cards: List[str] = []
    created_at: Optional[str] = None


class LoginResponse(BaseModel):
    token: str
    user: UserProfile


# ==================== Utility Functions ====================

def load_config() -> dict:
    """Load services configuration."""
    try:
        with open(CONFIG_FILE, 'r') as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Failed to load config: {e}")
        return {}


def get_pid(pidfile: Path) -> Optional[int]:
    """Read PID from pidfile."""
    try:
        if pidfile.exists():
            with open(pidfile, 'r') as f:
                content = f.read().strip()
                if content.isdigit():
                    return int(content)
    except Exception as e:
        logger.debug(f"Failed to read PID from {pidfile}: {e}")
    return None


def _get_process_tree_metrics(pid: int) -> Dict:
    """Return aggregated metrics for a process and its children."""
    try:
        proc = psutil.Process(pid)
    except Exception:
        return {
            "cpu_percent": 0.0,
            "memory_mb": 0.0,
            "read_bytes": 0,
            "write_bytes": 0
        }

    processes = [proc]
    try:
        processes.extend(proc.children(recursive=True))
    except Exception:
        pass

    total_cpu = 0.0
    total_mem = 0
    total_read = 0
    total_write = 0
    for p in processes:
        try:
            total_cpu += p.cpu_percent(interval=None)
        except Exception:
            pass
        try:
            total_mem += p.memory_info().rss
        except Exception:
            pass
        try:
            io = p.io_counters()
            total_read += getattr(io, "read_bytes", 0)
            total_write += getattr(io, "write_bytes", 0)
        except Exception:
            pass

    return {
        "cpu_percent": round(total_cpu, 2),
        "memory_mb": round(total_mem / (1024 * 1024), 2),
        "read_bytes": total_read,
        "write_bytes": total_write
    }


def _init_metrics_history(config: dict):
    """Initialize history buffers for platform and services."""
    global METRICS_HISTORY
    METRICS_HISTORY["platform"] = deque(maxlen=MAX_METRICS_POINTS)
    for service_cfg in config.get("services", []):
        name = service_cfg.get("name")
        if name:
            METRICS_HISTORY[name] = deque(maxlen=MAX_METRICS_POINTS)


async def _metrics_sampler():
    """Background task: sample process tree metrics and store history."""
    while True:
        try:
            config = load_config()
            if not METRICS_HISTORY:
                _init_metrics_history(config)

            timestamp = datetime.now().isoformat()

            # Platform metrics
            platform_pid = get_pid(LOGS_DIR / "platform.pid")
            if platform_pid:
                metrics = _get_process_tree_metrics(platform_pid)
            else:
                metrics = {"cpu_percent": 0.0, "memory_mb": 0.0, "read_bytes": 0, "write_bytes": 0}

            last_read = METRICS_LAST_IO_READ.get("platform", metrics["read_bytes"])
            last_write = METRICS_LAST_IO_WRITE.get("platform", metrics["write_bytes"])
            delta_read = max(metrics["read_bytes"] - last_read, 0)
            delta_write = max(metrics["write_bytes"] - last_write, 0)
            METRICS_LAST_IO_READ["platform"] = metrics["read_bytes"]
            METRICS_LAST_IO_WRITE["platform"] = metrics["write_bytes"]
            METRICS_HISTORY["platform"].append({
                "timestamp": timestamp,
                "cpu_percent": metrics["cpu_percent"],
                "memory_mb": metrics["memory_mb"],
                "read_mb_s": round(delta_read / (1024 * 1024 * METRICS_INTERVAL_SECONDS), 3),
                "write_mb_s": round(delta_write / (1024 * 1024 * METRICS_INTERVAL_SECONDS), 3)
            })

            # Service metrics
            for service_cfg in config.get("services", []):
                name = service_cfg.get("name")
                if not name:
                    continue
                pid = get_pid(LOGS_DIR / f"{name}.pid")
                if pid:
                    svc_metrics = _get_process_tree_metrics(pid)
                else:
                    svc_metrics = {"cpu_percent": 0.0, "memory_mb": 0.0, "read_bytes": 0, "write_bytes": 0}

                last_read = METRICS_LAST_IO_READ.get(name, svc_metrics["read_bytes"])
                last_write = METRICS_LAST_IO_WRITE.get(name, svc_metrics["write_bytes"])
                delta_read = max(svc_metrics["read_bytes"] - last_read, 0)
                delta_write = max(svc_metrics["write_bytes"] - last_write, 0)
                METRICS_LAST_IO_READ[name] = svc_metrics["read_bytes"]
                METRICS_LAST_IO_WRITE[name] = svc_metrics["write_bytes"]
                METRICS_HISTORY.setdefault(name, deque(maxlen=MAX_METRICS_POINTS)).append({
                    "timestamp": timestamp,
                    "cpu_percent": svc_metrics["cpu_percent"],
                    "memory_mb": svc_metrics["memory_mb"],
                    "read_mb_s": round(delta_read / (1024 * 1024 * METRICS_INTERVAL_SECONDS), 3),
                    "write_mb_s": round(delta_write / (1024 * 1024 * METRICS_INTERVAL_SECONDS), 3)
                })
        except Exception as e:
            logger.warning(f"Metrics sampler error: {e}")

        await asyncio.sleep(METRICS_INTERVAL_SECONDS)


# ==================== System Metrics Persistent History ====================

def _load_system_metrics_history() -> List[Dict]:
    """Load system metrics history from disk."""
    if not SYSTEM_METRICS_FILE.exists():
        return []
    try:
        data = json.loads(SYSTEM_METRICS_FILE.read_text(encoding="utf-8"))
        return data if isinstance(data, list) else []
    except Exception:
        return []


def _save_system_metrics_history(entries: List[Dict]):
    """Save system metrics history to disk with size cap."""
    if len(entries) > SYSTEM_METRICS_MAX_POINTS:
        entries = entries[-SYSTEM_METRICS_MAX_POINTS:]
    SYSTEM_METRICS_FILE.write_text(json.dumps(entries, ensure_ascii=False), encoding="utf-8")


async def _system_metrics_persist_loop():
    """Background loop: every 60s append a system-level CPU/memory point to persistent file."""
    logger.info("System metrics persistent sampler started")
    while True:
        await asyncio.sleep(SYSTEM_METRICS_PERSIST_INTERVAL)
        try:
            cpu = psutil.cpu_percent(interval=0)
            mem = psutil.virtual_memory()
            point = {
                "t": datetime.now().isoformat(),
                "c": round(cpu, 1),
                "m": round(mem.percent, 1),
            }
            entries = _load_system_metrics_history()
            entries.append(point)
            _save_system_metrics_history(entries)
        except Exception as e:
            logger.warning(f"System metrics persist error: {e}")


async def _log_maintenance():
    while True:
        try:
            for log_file in LOGS_DIR.glob("*.log"):
                _rotate_log_if_needed(log_file)
            _enforce_total_log_size()
        except Exception as exc:
            logger.warning(f"Log maintenance error: {exc}")
        await asyncio.sleep(300)


def is_process_running(pid: int) -> bool:
    """Check if process is running."""
    try:
        # Check if process exists without sending signal
        os.kill(pid, 0)
        return True
    except (OSError, TypeError):
        return False


def _check_heartbeat(heartbeat_url: Optional[str]) -> Tuple[bool, Optional[str]]:
    if not heartbeat_url:
        return False, "missing"
    if heartbeat_url in {"mock", "simulate", "mock://ok", "simulate://ok"}:
        return True, None
    if heartbeat_url in {"mock://fail", "simulate://fail"}:
        return False, "mock_fail"
    try:
        req = urllib.request.Request(heartbeat_url, method="GET")
        with urllib.request.urlopen(req, timeout=1.5) as response:
            return response.status == 200, None if response.status == 200 else f"http_status_{response.status}"
    except urllib.error.HTTPError as exc:
        return False, f"http_status_{getattr(exc, 'code', 'unknown')}"
    except urllib.error.URLError as exc:
        reason = str(getattr(exc, "reason", "connection_error"))
        if "timed out" in reason.lower():
            return False, "timeout"
        return False, "connection_error"
    except ValueError:
        return False, "invalid_url"


def get_service_status(name: str, pidfile: Path, log_file: Path, heartbeat_url: Optional[str] = None, scheduled_restart_cfg: Optional[Dict] = None) -> ServiceStatus:
    """Get service status from PID file, log file, and heartbeat."""
    pid = get_pid(pidfile)
    running_pid = pid is not None and is_process_running(pid)
    heartbeat_ok, heartbeat_reason = _check_heartbeat(heartbeat_url) if running_pid else (False, "missing")
    health_reason = None
    if running_pid and heartbeat_ok:
        health = "running"
    elif running_pid and not heartbeat_ok:
        health = "abnormal"
        health_reason = heartbeat_reason or "heartbeat_failed"
    else:
        health = "stopped"
    running = running_pid
    uptime = None
    uptime_seconds = None
    if running and pid:
        try:
            proc = psutil.Process(pid)
            start_time = datetime.fromtimestamp(proc.create_time())
            delta = datetime.now() - start_time
            total_seconds = int(delta.total_seconds())
            uptime_seconds = total_seconds
            days, rem = divmod(total_seconds, 86400)
            hours, rem = divmod(rem, 3600)
            minutes, seconds = divmod(rem, 60)
            uptime = f"{days}d {hours}h {minutes}m {seconds}s"
        except Exception:
            uptime = None
    
    # Get last log line
    last_log = None
    try:
        if log_file.exists() and log_file.stat().st_size > 0:
            with open(log_file, 'rb') as f:
                # Read last 500 bytes to find last line
                f.seek(0, 2)
                file_size = f.tell()
                read_size = min(500, file_size)
                f.seek(-read_size, 2)
                content = f.read().decode('utf-8', errors='ignore')
                lines = content.split('\n')
                # Find last non-empty line
                for line in reversed(lines):
                    if line.strip():
                        last_log = line.strip()[:100]  # Max 100 chars
                        break
    except Exception as e:
        logger.debug(f"Failed to read log for {name}: {e}")
    
    # Build scheduled restart info for frontend
    sr_info = None
    if scheduled_restart_cfg:
        sr_info = {
            "enabled": scheduled_restart_cfg.get("enabled", False),
            "cron": scheduled_restart_cfg.get("cron", ""),
            "last_restart": scheduled_restart_cfg.get("last_restart"),
            "next_restart": _calc_next_restart(scheduled_restart_cfg) if scheduled_restart_cfg.get("enabled") else None,
        }

    return ServiceStatus(
        name=name,
        running=running,
        health=health,
        health_reason=health_reason,
        pid=pid if running else None,
        uptime=uptime,
        uptime_seconds=uptime_seconds,
        last_log=last_log,
        scheduled_restart=sr_info,
    )


def extract_log_level(log_line: str) -> str:
    """Extract log level from log line."""
    line = log_line.upper()
    if "ERROR" in line or "CRITICAL" in line:
        return "ERROR"
    elif "WARNING" in line:
        return "WARNING"
    elif "INFO" in line:
        return "INFO"
    elif "DEBUG" in line:
        return "DEBUG"
    return "INFO"


def get_system_metrics() -> SystemMetrics:
    """Get current system resource metrics."""
    try:
        # CPU 信息
        cpu_percents = psutil.cpu_percent(interval=0.1, percpu=True)
        cpu_count = len(cpu_percents) if cpu_percents else psutil.cpu_count()
        cpu_percent = round(sum(cpu_percents) / cpu_count, 2) if cpu_percents and cpu_count else 0.0
        
        # 内存信息
        memory = psutil.virtual_memory()
        memory_used_mb = memory.used // (1024 * 1024)
        memory_total_mb = memory.total // (1024 * 1024)
        memory_percent = memory.percent
        
        # 磁盘信息
        disk = psutil.disk_usage('/')
        disk_used_gb = disk.used // (1024 * 1024 * 1024)
        disk_total_gb = disk.total // (1024 * 1024 * 1024)
        disk_free_gb = disk.free // (1024 * 1024 * 1024)
        disk_percent = disk.percent
        
        return SystemMetrics(
            cpu_percent=round(cpu_percent, 2),
            cpu_count=cpu_count,
            cpu_percents=[round(v, 2) for v in cpu_percents] if cpu_percents else [],
            memory_percent=round(memory_percent, 2),
            memory_used=memory_used_mb,
            memory_total=memory_total_mb,
            disk_percent=round(disk_percent, 2),
            disk_used=disk_used_gb,
            disk_total=disk_total_gb,
            disk_free=disk_free_gb,
            timestamp=datetime.now().isoformat()
        )
    except Exception as e:
        logger.error(f"Failed to get system metrics: {e}")
        # Return default metrics on error
        return SystemMetrics(
            cpu_percent=0.0,
            cpu_count=0,
            cpu_percents=[],
            memory_percent=0.0,
            memory_used=0,
            memory_total=0,
            disk_percent=0.0,
            disk_used=0,
            disk_total=0,
            disk_free=0,
            timestamp=datetime.now().isoformat()
        )


def get_disk_partitions() -> List[DiskPartitionInfo]:
    partitions = []
    seen = set()
    network_fs = {
        'nfs', 'nfs4', 'cifs', 'smbfs', 'sshfs', 'fuse.sshfs', 'fuse.glusterfs',
        'glusterfs', 'ceph', 'fuse.ceph', 'fuse.rclone', 'afp', 'davfs', 'fuseblk'
    }
    virtual_fs = {
        'tmpfs', 'overlay', 'squashfs', 'proc', 'sysfs', 'devtmpfs', 'cgroup',
        'cgroup2', 'pstore', 'securityfs', 'debugfs', 'tracefs', 'configfs',
        'fusectl', 'mqueue', 'hugetlbfs', 'rpc_pipefs', 'autofs'
    }
    for part in psutil.disk_partitions(all=False):
        if not part.device or not part.device.startswith('/dev/'):
            continue
        fstype = (part.fstype or '').lower()
        if fstype in network_fs or fstype in virtual_fs:
            continue
        key = (part.device, part.mountpoint)
        if key in seen:
            continue
        seen.add(key)
        try:
            usage = psutil.disk_usage(part.mountpoint)
        except PermissionError:
            continue
        partitions.append(DiskPartitionInfo(
            device=part.device,
            mountpoint=part.mountpoint,
            fstype=part.fstype,
            total_gb=usage.total // (1024 * 1024 * 1024),
            used_gb=usage.used // (1024 * 1024 * 1024),
            free_gb=usage.free // (1024 * 1024 * 1024),
            percent=round(usage.percent, 2)
        ))
    partitions.sort(key=lambda item: item.total_gb, reverse=True)
    return partitions


def get_service_info(service_name: str) -> ServiceInfo:
    manifest = read_manifest(SERVICE_DIR / "deployments" / service_name)
    uptime = None
    uptime_seconds = None
    try:
        pidfile = LOGS_DIR / f"{service_name}.pid"
        if pidfile.exists():
            pid = int(pidfile.read_text().strip())
            proc = psutil.Process(pid)
            start_time = datetime.fromtimestamp(proc.create_time())
            delta = datetime.now() - start_time
            uptime_seconds = int(delta.total_seconds())
            days, rem = divmod(uptime_seconds, 86400)
            hours, rem = divmod(rem, 3600)
            minutes, seconds = divmod(rem, 60)
            uptime = f"{days}d {hours}h {minutes}m {seconds}s"
    except Exception:
        uptime = None
    return ServiceInfo(
        name=service_name,
        version=manifest.get("version", "unknown"),
        commit_hash=manifest.get("commit_hash", "unknown"),
        build_date=manifest.get("build_date", "unknown"),
        uptime=uptime,
        uptime_seconds=uptime_seconds
    )


def read_manifest(base_dir: Path) -> Dict:
    manifest_path = base_dir / "manifest.json"
    if not manifest_path.exists():
        return {}
    try:
        return json.loads(manifest_path.read_text(encoding="utf-8"))
    except Exception:
        return {}


def parse_version(value: str) -> Tuple:
    if not value:
        return tuple()
    parts = []
    for token in value.replace('-', '.').split('.'):
        if token.isdigit():
            parts.append(int(token))
        else:
            parts.append(token)
    return tuple(parts)


def is_newer_version(current: str, incoming: str) -> bool:
    if not current:
        return True
    return parse_version(incoming) > parse_version(current)


def compute_sha256(file_path: Path) -> str:
    digest = hashlib.sha256()
    with file_path.open('rb') as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b''):
            digest.update(chunk)
    return digest.hexdigest()


def list_backups(service: str) -> List[BackupInfo]:
    backups = []
    prefix = f"{service}_backup_"
    for path in (SERVICE_DIR / "deployments").glob(f"{prefix}*"):
        if not path.is_dir():
            continue
        suffix = path.name[len(prefix):]
        created_at = "unknown"
        if suffix and suffix.isdigit():
            created_at = f"{suffix[0:4]}-{suffix[4:6]}-{suffix[6:8]} {suffix[8:10]}:{suffix[10:12]}:{suffix[12:14]}"
        backups.append(BackupInfo(name=path.name, created_at=created_at))
    backups.sort(key=lambda item: item.name, reverse=True)
    return backups


def prune_backups(service: str, keep: int = 20):
    backups = list_backups(service)
    if len(backups) <= keep:
        return
    deployments_dir = SERVICE_DIR / "deployments"
    for backup in backups[keep:]:
        path = deployments_dir / backup.name
        if path.exists():
            shutil.rmtree(path, ignore_errors=True)


def rollback_to_backup(service: str, backup_name: str):
    deployments_dir = SERVICE_DIR / "deployments"
    target_dir = deployments_dir / service
    backup_dir = deployments_dir / backup_name
    if not backup_dir.exists():
        raise RuntimeError("backup not found")

    rollback_stamp = datetime.now().strftime('%Y%m%d%H%M%S')
    if target_dir.exists():
        current_backup = deployments_dir / f"{service}_backup_{rollback_stamp}"
        shutil.move(str(target_dir), str(current_backup))
        prune_backups(service, keep=20)
    shutil.move(str(backup_dir), str(target_dir))
    _run_restart(service)


def _safe_extract_tar(tar: tarfile.TarFile, dest: Path):
    for member in tar.getmembers():
        member_path = (dest / member.name).resolve()
        if not str(member_path).startswith(str(dest.resolve())):
            raise ValueError("Invalid tar entry path")
    tar.extractall(dest)


def _parse_iso_timestamp(value: Optional[str]) -> Optional[datetime]:
    if not value:
        return None
    try:
        safe = value.replace('Z', '')
        return datetime.fromisoformat(safe)
    except Exception:
        return None


def _downsample_points(points: List[Dict], step_seconds: int) -> List[Dict]:
    if step_seconds <= 0:
        return points
    buckets: Dict[int, Dict] = {}
    for point in points:
        ts = _parse_iso_timestamp(point.get("timestamp"))
        if not ts:
            continue
        bucket = int(ts.timestamp() // step_seconds)
        buckets[bucket] = point
    return [buckets[key] for key in sorted(buckets.keys())]


def _rotate_log_if_needed(log_file: Path):
    """Enforce per-file rotation and backup limits.
    
    RotatingFileHandler in manage_services.py creates .log.1, .log.2, etc.
    This function enforces MAX_LOG_BACKUPS by deleting excess older backups,
    and enforces MAX_LOG_BYTES on the main .log file if manage_services isn't handling it.
    """
    try:
        if not log_file.exists():
            return

        # Enforce backup count: .log.1, .log.2, ... keep only MAX_LOG_BACKUPS
        base = log_file.name  # e.g. "service_A.log"
        backups = sorted(
            [f for f in log_file.parent.iterdir()
             if f.name.startswith(base + ".") and f.name[len(base)+1:].isdigit()],
            key=lambda p: int(p.name[len(base)+1:])
        )
        for old in backups[MAX_LOG_BACKUPS:]:
            old.unlink(missing_ok=True)
            logger.debug(f"Removed excess log backup: {old.name}")

        # If main log exceeds limit (fallback for non-RotatingFileHandler logs)
        if log_file.stat().st_size > MAX_LOG_BYTES:
            # Shift existing backups: .2 → .3, .1 → .2, etc.
            for i in range(MAX_LOG_BACKUPS, 0, -1):
                src = log_file.parent / f"{base}.{i}"
                dst = log_file.parent / f"{base}.{i + 1}"
                if src.exists():
                    if i >= MAX_LOG_BACKUPS:
                        src.unlink(missing_ok=True)
                    else:
                        shutil.move(str(src), str(dst))
            # Rotate current → .1
            shutil.move(str(log_file), str(log_file.parent / f"{base}.1"))
            log_file.touch()
            LOG_INDEX_CACHE.pop(str(log_file), None)
    except Exception as exc:
        logger.warning(f"Log rotate failed for {log_file}: {exc}")


def _enforce_total_log_size():
    """Enforce total log directory size limit by removing oldest backup files."""
    try:
        # Collect all log files (main + backups), sorted by mtime (oldest first)
        all_log_files = sorted(
            [f for f in LOGS_DIR.iterdir() if f.is_file() and '.log' in f.name and not f.name.endswith('.idx')],
            key=lambda p: p.stat().st_mtime
        )
        total = sum(f.stat().st_size for f in all_log_files)
        
        if total <= MAX_TOTAL_LOG_BYTES:
            return
        
        logger.info(f"Total log size {total // (1024*1024)}MB exceeds limit {MAX_TOTAL_LOG_BYTES // (1024*1024)}MB, cleaning up...")
        
        for f in all_log_files:
            if total <= MAX_TOTAL_LOG_BYTES:
                break
            # Only delete backup files (.log.N), never delete main .log files
            if f.suffix.lstrip('.').isdigit() or (f.name.count('.') >= 2 and f.name.split('.')[-1].isdigit()):
                fsize = f.stat().st_size
                f.unlink(missing_ok=True)
                # Also remove the index cache
                base_log = f.parent / f.name.rsplit('.', 1)[0]
                LOG_INDEX_CACHE.pop(str(base_log), None)
                total -= fsize
                logger.info(f"Removed old log backup: {f.name} ({fsize // 1024}KB)")
    except Exception as exc:
        logger.warning(f"Total log size enforcement error: {exc}")


def _load_log_index(log_file: Path) -> Dict:
    key = str(log_file)
    try:
        stat = log_file.stat()
    except Exception:
        return {"stride": LOG_INDEX_STRIDE, "offsets": [0], "total_lines": 0, "size": 0, "mtime": 0}

    cached = LOG_INDEX_CACHE.get(key)
    if cached and cached.get("mtime") == stat.st_mtime and cached.get("size") == stat.st_size:
        return cached

    idx_path = log_file.with_suffix(log_file.suffix + ".idx")
    if idx_path.exists():
        try:
            data = json.loads(idx_path.read_text(encoding="utf-8"))
            if data.get("mtime") == stat.st_mtime and data.get("size") == stat.st_size and data.get("stride") == LOG_INDEX_STRIDE:
                LOG_INDEX_CACHE[key] = data
                return data
        except Exception:
            pass

    offsets = [0]
    total_lines = 0
    with open(log_file, "rb") as f:
        while True:
            line = f.readline()
            if not line:
                break
            total_lines += 1
            if total_lines % LOG_INDEX_STRIDE == 0:
                offsets.append(f.tell())

    data = {
        "stride": LOG_INDEX_STRIDE,
        "offsets": offsets,
        "total_lines": total_lines,
        "size": stat.st_size,
        "mtime": stat.st_mtime,
    }
    try:
        idx_path.write_text(json.dumps(data), encoding="utf-8")
    except Exception:
        pass
    LOG_INDEX_CACHE[key] = data
    return data


def _get_log_chain(service: str) -> List[Path]:
    """Get ordered list of log files for a service: oldest backup → ... → current.
    
    e.g. [service_A.log.3, service_A.log.2, service_A.log.1, service_A.log]
    """
    base = LOGS_DIR / f"{service}.log"
    chain = []
    
    # Collect backup files (.log.N) sorted by N descending (oldest first)
    backups = []
    for f in LOGS_DIR.iterdir():
        name = f.name
        prefix = f"{service}.log."
        if name.startswith(prefix) and not name.endswith('.idx'):
            suffix = name[len(prefix):]
            if suffix.isdigit():
                backups.append((int(suffix), f))
    backups.sort(key=lambda x: x[0], reverse=True)  # highest number = oldest
    
    for _, f in backups:
        if f.exists():
            chain.append(f)
    
    if base.exists():
        chain.append(base)
    
    return chain


def _get_chained_total_lines(chain: List[Path]) -> Tuple[int, List[Tuple[Path, int]]]:
    """Get total lines across all chained log files.
    
    Returns (total_lines, [(file, file_total_lines), ...])
    """
    total = 0
    file_lines = []
    for f in chain:
        idx = _load_log_index(f)
        n = idx.get("total_lines", 0)
        file_lines.append((f, n))
        total += n
    return total, file_lines


def _read_chained_log_lines(chain: List[Path], start_line: int, max_lines: int) -> Tuple[List[Tuple[int, str]], int]:
    """Read lines across chained log files with virtual line numbers.
    
    The oldest backup is at the beginning; current .log is at the end.
    Virtual line 0 is the first line of the oldest backup.
    """
    total_lines, file_lines = _get_chained_total_lines(chain)
    if total_lines <= 0:
        return [], 0
    
    if start_line < 0:
        start_line = max(total_lines + start_line, 0)
    start_line = min(start_line, total_lines)
    
    results: List[Tuple[int, str]] = []
    cumulative = 0
    
    for fpath, flines in file_lines:
        if len(results) >= max_lines:
            break
        
        file_end = cumulative + flines
        
        if file_end <= start_line:
            # This file is entirely before start_line, skip it
            cumulative = file_end
            continue
        
        # Calculate where to start reading in this file
        local_start = max(start_line - cumulative, 0)
        remaining = max_lines - len(results)
        
        file_results, _ = _read_log_lines(fpath, local_start, remaining)
        for local_idx, line in file_results:
            results.append((cumulative + local_idx, line))
        
        cumulative = file_end
    
    return results[:max_lines], total_lines


def _read_log_lines(log_file: Path, start_line: int, max_lines: int) -> Tuple[List[Tuple[int, str]], int]:
    index = _load_log_index(log_file)
    total_lines = index.get("total_lines", 0)
    if total_lines <= 0:
        return [], 0
    if start_line < 0:
        start_line = max(total_lines + start_line, 0)
    start_line = min(start_line, total_lines)
    stride = index.get("stride", LOG_INDEX_STRIDE)
    offsets = index.get("offsets", [0])
    bucket = start_line // stride
    byte_offset = offsets[bucket] if bucket < len(offsets) else 0
    current_line = bucket * stride
    results: List[Tuple[int, str]] = []
    with open(log_file, "rb") as f:
        f.seek(byte_offset)
        while current_line < start_line:
            line = f.readline()
            if not line:
                break
            current_line += 1
        while len(results) < max_lines:
            line = f.readline()
            if not line:
                break
            results.append((current_line, line.decode("utf-8", errors="ignore")))
            current_line += 1
    return results, total_lines


def _run_restart(service: str):
    cmd = [
        sys.executable,
        str(SERVICE_DIR / 'manage_services.py'),
        'restart'
    ]
    if service == 'platform':
        cmd.extend(['--platform', '--daemon'])
    else:
        cmd.extend(['--service', service, '--daemon'])
    result = subprocess.run(cmd, cwd=str(SERVICE_DIR), capture_output=True, text=True, timeout=60)
    if result.returncode != 0:
        raise RuntimeError(result.stderr or result.stdout or 'Restart failed')


def _perform_update(task_id: str, service: str, file_path: Path):
    task = UPDATE_TASKS.get(task_id)
    if not task:
        return
    task["status"] = "extracting"
    task["update_progress"] = 5
    task["message"] = "Extracting package"

    package_hash = compute_sha256(file_path)
    task["package_hash"] = package_hash

    extract_root = SERVICE_DIR / "updates" / f"{service}-{task_id}"
    if extract_root.exists():
        shutil.rmtree(extract_root, ignore_errors=True)
    extract_root.mkdir(parents=True, exist_ok=True)

    with tarfile.open(file_path, "r:gz") as tar:
        _safe_extract_tar(tar, extract_root)

    entries = [p for p in extract_root.iterdir() if p.name not in ('__MACOSX',)]
    if len(entries) == 1 and entries[0].is_dir():
        source_dir = entries[0]
    else:
        source_dir = extract_root

    manifest = read_manifest(source_dir)
    if not manifest:
        raise RuntimeError("manifest.json missing in package")

    incoming_version = manifest.get("version")
    incoming_hash = manifest.get("package_hash")
    if incoming_hash and incoming_hash != package_hash:
        raise RuntimeError("package hash mismatch")

    current_manifest = read_manifest(SERVICE_DIR / "deployments" / service)
    current_version = current_manifest.get("version") if current_manifest else None
    if incoming_version and current_version and not is_newer_version(current_version, incoming_version):
        raise RuntimeError("incoming version is not newer")

    task["update_progress"] = 35
    task["status"] = "validating"
    task["message"] = "Validation complete"

    target_dir = SERVICE_DIR / "deployments" / service
    target_dir.parent.mkdir(parents=True, exist_ok=True)
    backup_dir = None
    if target_dir.exists():
        backup_dir = SERVICE_DIR / "deployments" / f"{service}_backup_{datetime.now().strftime('%Y%m%d%H%M%S')}"
        shutil.move(str(target_dir), str(backup_dir))
        prune_backups(service, keep=20)

    try:
        task["update_progress"] = 60
        task["status"] = "replacing"
        task["message"] = "Replacing files"
        shutil.copytree(source_dir, target_dir)

        task["update_progress"] = 85
        task["status"] = "restarting"
        task["message"] = "Restarting service"
        _run_restart(service)

        task["update_progress"] = 100
        task["status"] = "completed"
        task["message"] = "Update completed"
    except Exception:
        if backup_dir and backup_dir.exists():
            if target_dir.exists():
                shutil.rmtree(target_dir, ignore_errors=True)
            shutil.move(str(backup_dir), str(target_dir))
            try:
                _run_restart(service)
            except Exception:
                pass
        raise


async def run_update_task(task_id: str, service: str, file_path: Path):
    try:
        await asyncio.to_thread(_perform_update, task_id, service, file_path)
    except Exception as exc:
        task = UPDATE_TASKS.get(task_id)
        if task:
            task["status"] = "failed"
            task["message"] = str(exc)


# ==================== API Endpoints ====================


@app.post("/api/login", response_model=LoginResponse)
async def login(login_data: LoginRequest):
    user = authenticate_user(login_data.username, login_data.password)
    if not user:
        append_audit_log(user=login_data.username, role="unknown", action="login", result="failed", detail="invalid credentials")
        raise HTTPException(status_code=401, detail="Incorrect username or password")
    token = create_access_token({"sub": user["username"]})
    append_audit_log(user=user["username"], role=user.get("role", "admin"), action="login")
    return {
        "token": token,
        "user": {
            "username": user["username"],
            "role": user.get("role", "admin"),
            "visible_cards": user.get("visible_cards", []),
            "created_at": user.get("created_at")
        }
    }


@app.get("/api/me", response_model=UserProfile)
async def get_me(current_user: dict = Depends(get_current_user)):
    return {
        "username": current_user["username"],
        "role": current_user.get("role", "admin"),
        "visible_cards": current_user.get("visible_cards", []),
        "created_at": current_user.get("created_at")
    }


# ==================== Role-based Access Helpers ====================

VALID_ROLES = {"admin", "operator", "readonly"}

def require_role(current_user: dict, *allowed_roles: str):
    """Raise 403 if the user's role is not in allowed_roles."""
    role = current_user.get("role", "admin")
    if role not in allowed_roles:
        raise HTTPException(status_code=403, detail="Permission denied")

def require_admin(current_user: dict):
    require_role(current_user, "admin")

def require_operator(current_user: dict):
    """Admin and operator can perform write operations."""
    require_role(current_user, "admin", "operator")


# ==================== Scheduled Restart ====================

def _parse_cron(cron_str: str) -> Optional[Dict]:
    """Parse simple cron string 'HH:MM' or 'HH:MM@weekdays'.
    weekdays = comma-separated 0-6 (0=Mon, 6=Sun). Empty = every day.
    Examples: '03:00', '03:30@0,1,2,3,4', '02:00@0,2,4'
    """
    if not cron_str:
        return None
    try:
        parts = cron_str.split('@')
        time_part = parts[0].strip()
        h, m = int(time_part.split(':')[0]), int(time_part.split(':')[1])
        if not (0 <= h <= 23 and 0 <= m <= 59):
            return None
        weekdays = None  # None means every day
        if len(parts) > 1 and parts[1].strip():
            weekdays = [int(d) for d in parts[1].strip().split(',') if d.strip().isdigit()]
            weekdays = [d for d in weekdays if 0 <= d <= 6]
            if not weekdays:
                weekdays = None
        return {"hour": h, "minute": m, "weekdays": weekdays}
    except Exception:
        return None


def _calc_next_restart(sr_cfg: Dict) -> Optional[str]:
    """Calculate next restart ISO timestamp from scheduled_restart config."""
    if not sr_cfg.get("enabled") or not sr_cfg.get("cron"):
        return None
    parsed = _parse_cron(sr_cfg["cron"])
    if not parsed:
        return None
    now = datetime.now()
    target_today = now.replace(hour=parsed["hour"], minute=parsed["minute"], second=0, microsecond=0)
    weekdays = parsed.get("weekdays")

    # Search for next matching datetime within the next 8 days
    for day_offset in range(8):
        candidate = target_today + timedelta(days=day_offset)
        if day_offset == 0 and candidate <= now:
            continue  # already passed today
        if weekdays is not None and candidate.weekday() not in weekdays:
            continue
        return candidate.isoformat()
    return None


def _save_config(config: dict):
    """Write config back to CONFIG_FILE."""
    with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
        json.dump(config, f, indent=2, ensure_ascii=False)
        f.write('\n')


async def _scheduled_restart_loop():
    """Background loop: every 30s check if any service needs scheduled restart."""
    logger.info("Scheduled restart checker started")
    while True:
        await asyncio.sleep(30)
        try:
            config = load_config()
            now = datetime.now()
            changed = False

            # Check platform
            platform_cfg = config.get("platform", {})
            sr = platform_cfg.get("scheduled_restart")
            if sr and sr.get("enabled") and sr.get("cron"):
                if _should_restart_now(sr, now):
                    logger.info("Scheduled restart triggered for platform")
                    _do_scheduled_restart("platform")
                    sr["last_restart"] = now.isoformat()
                    changed = True

            # Check services
            for svc in config.get("services", []):
                sr = svc.get("scheduled_restart")
                if sr and sr.get("enabled") and sr.get("cron"):
                    if _should_restart_now(sr, now):
                        svc_name = svc.get("name", "unknown")
                        logger.info(f"Scheduled restart triggered for {svc_name}")
                        _do_scheduled_restart(svc_name)
                        sr["last_restart"] = now.isoformat()
                        changed = True

            if changed:
                _save_config(config)
        except Exception as e:
            logger.error(f"Scheduled restart check error: {e}")


def _should_restart_now(sr: Dict, now: datetime) -> bool:
    """Check if 'now' falls within the scheduled cron window."""
    parsed = _parse_cron(sr.get("cron", ""))
    if not parsed:
        return False
    # Must match hour and minute (within a 60s window to avoid double-trigger)
    if now.hour != parsed["hour"] or now.minute != parsed["minute"]:
        return False
    weekdays = parsed.get("weekdays")
    if weekdays is not None and now.weekday() not in weekdays:
        return False
    # Prevent double-trigger: check last_restart
    last = sr.get("last_restart")
    if last:
        try:
            last_dt = datetime.fromisoformat(last)
            if (now - last_dt).total_seconds() < 120:
                return False  # restarted less than 2 min ago
        except Exception:
            pass
    return True


def _do_scheduled_restart(service_name: str):
    """Execute a restart via manage_services.py for the given service."""
    cmd = [sys.executable, str(SERVICE_DIR / 'manage_services.py'), 'restart']
    if service_name == 'platform':
        cmd.append('--platform')
    else:
        cmd.extend(['--service', service_name])
    cmd.append('--daemon')
    try:
        subprocess.Popen(cmd, cwd=str(SERVICE_DIR), stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        append_audit_log(user="system", role="system", action="restart", target=service_name, detail="scheduled restart")
    except Exception as e:
        logger.error(f"Scheduled restart failed for {service_name}: {e}")
        append_audit_log(user="system", role="system", action="restart", target=service_name, detail=f"scheduled restart failed: {e}", result="failed")


# ==================== Audit Log ====================

import threading
_audit_lock = threading.Lock()

# ==================== Per-service control locks ====================
# Prevents concurrent conflicting operations on the same service (multi-user safety)
_service_locks: Dict[str, asyncio.Lock] = {}
_service_locks_meta_lock = asyncio.Lock()

async def _get_service_lock(service_name: str) -> asyncio.Lock:
    """Get or create an asyncio.Lock for a specific service."""
    async with _service_locks_meta_lock:
        if service_name not in _service_locks:
            _service_locks[service_name] = asyncio.Lock()
        return _service_locks[service_name]


def append_audit_log(user: str, role: str, action: str, target: str = "", detail: str = "", result: str = "success"):
    """Append an entry to the audit log JSON file."""
    entry = {
        "timestamp": datetime.now().isoformat(),
        "user": user,
        "role": role,
        "action": action,
        "target": target,
        "detail": detail,
        "result": result,
    }
    try:
        with _audit_lock:
            entries = []
            if AUDIT_LOG_FILE.exists():
                try:
                    entries = json.loads(AUDIT_LOG_FILE.read_text(encoding="utf-8"))
                except Exception:
                    entries = []
            entries.append(entry)
            # Keep only the latest N entries
            if len(entries) > AUDIT_LOG_MAX_ENTRIES:
                entries = entries[-AUDIT_LOG_MAX_ENTRIES:]
            AUDIT_LOG_FILE.write_text(json.dumps(entries, ensure_ascii=False, indent=None), encoding="utf-8")
    except Exception as exc:
        logger.warning(f"Failed to write audit log: {exc}")


def read_audit_logs(limit: int = 200, offset: int = 0, username: Optional[str] = None) -> Tuple[List[Dict], int]:
    """Read audit log entries with optional filtering by username."""
    if not AUDIT_LOG_FILE.exists():
        return [], 0
    try:
        entries = json.loads(AUDIT_LOG_FILE.read_text(encoding="utf-8"))
    except Exception:
        return [], 0
    if username:
        entries = [e for e in entries if e.get("user") == username]
    total = len(entries)
    # Return newest first
    entries = list(reversed(entries))
    entries = entries[offset:offset + limit]
    return entries, total


@app.get("/api/audit-logs")
async def get_audit_logs(
    limit: int = Query(200, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    current_user: dict = Depends(get_current_user),
):
    """Get audit logs. Admin sees all; others see only their own."""
    role = current_user.get("role", "admin")
    username_filter = None if role == "admin" else current_user["username"]
    entries, total = read_audit_logs(limit=limit, offset=offset, username=username_filter)
    return {"logs": entries, "total": total, "offset": offset, "limit": limit}


# ==================== User Management APIs (admin only) ====================

class UserCreateRequest(BaseModel):
    username: str
    password: str
    role: str = "readonly"
    visible_cards: List[str] = []

class UserUpdateRequest(BaseModel):
    password: Optional[str] = None
    role: Optional[str] = None
    visible_cards: Optional[List[str]] = None

class UserListItem(BaseModel):
    id: int
    username: str
    role: str
    visible_cards: List[str]
    created_at: Optional[str] = None


@app.get("/api/users")
async def list_users(current_user: dict = Depends(get_current_user)):
    """List all users (admin only)."""
    require_admin(current_user)
    session = SessionLocal()
    try:
        users = session.query(User).order_by(User.id).all()
        result = []
        for u in users:
            vc = []
            if u.visible_cards:
                try:
                    vc = json.loads(u.visible_cards)
                except Exception:
                    vc = []
            result.append({
                "id": u.id,
                "username": u.username,
                "role": u.role or "admin",
                "visible_cards": vc,
                "created_at": u.created_at.isoformat() if u.created_at else None
            })
        return result
    finally:
        session.close()


@app.post("/api/users")
async def create_user(req: UserCreateRequest, current_user: dict = Depends(get_current_user)):
    """Create a new user (admin only)."""
    require_admin(current_user)
    if req.role not in VALID_ROLES:
        raise HTTPException(status_code=400, detail=f"Invalid role. Must be one of: {', '.join(VALID_ROLES)}")
    session = SessionLocal()
    try:
        existing = session.query(User).filter(User.username == req.username).first()
        if existing:
            raise HTTPException(status_code=409, detail="Username already exists")
        user = User(
            username=req.username,
            password_hash=pwd_context.hash(req.password),
            role=req.role,
            visible_cards=json.dumps(req.visible_cards) if req.visible_cards else ""
        )
        session.add(user)
        session.commit()
        session.refresh(user)
        append_audit_log(user=current_user["username"], role=current_user.get("role", "admin"), action="create_user", target=req.username, detail=f"role={req.role}")
        return {"status": "success", "id": user.id, "username": user.username}
    finally:
        session.close()


@app.put("/api/users/{user_id}")
async def update_user(user_id: int, req: UserUpdateRequest, current_user: dict = Depends(get_current_user)):
    """Update a user (admin only)."""
    require_admin(current_user)
    session = SessionLocal()
    try:
        user = session.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        if req.role is not None:
            if req.role not in VALID_ROLES:
                raise HTTPException(status_code=400, detail=f"Invalid role. Must be one of: {', '.join(VALID_ROLES)}")
            # Prevent removing the last admin
            if user.role == "admin" and req.role != "admin":
                admin_count = session.query(User).filter(User.role == "admin").count()
                if admin_count <= 1:
                    raise HTTPException(status_code=400, detail="Cannot remove the last admin user")
            user.role = req.role
        if req.password is not None and req.password.strip():
            user.password_hash = pwd_context.hash(req.password)
        if req.visible_cards is not None:
            user.visible_cards = json.dumps(req.visible_cards) if req.visible_cards else ""
        changes = []
        if req.role is not None:
            changes.append(f"role={req.role}")
        if req.password is not None and req.password.strip():
            changes.append("password=***")
        if req.visible_cards is not None:
            changes.append(f"visible_cards={len(req.visible_cards)} items")
        session.commit()
        append_audit_log(user=current_user["username"], role=current_user.get("role", "admin"), action="update_user", target=user.username, detail=", ".join(changes))
        return {"status": "success"}
    finally:
        session.close()


@app.delete("/api/users/{user_id}")
async def delete_user(user_id: int, current_user: dict = Depends(get_current_user)):
    """Delete a user (admin only). Cannot delete yourself."""
    require_admin(current_user)
    session = SessionLocal()
    try:
        user = session.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        if user.username == current_user["username"]:
            raise HTTPException(status_code=400, detail="Cannot delete yourself")
        if user.role == "admin":
            admin_count = session.query(User).filter(User.role == "admin").count()
            if admin_count <= 1:
                raise HTTPException(status_code=400, detail="Cannot delete the last admin user")
        session.delete(user)
        session.commit()
        append_audit_log(user=current_user["username"], role=current_user.get("role", "admin"), action="delete_user", target=user.username)
        return {"status": "success"}
    finally:
        session.close()


# ==================== Service Order (config file) ====================

@app.put("/api/preferences/service-order")
async def put_service_order(request: Request, current_user: dict = Depends(get_current_user)):
    """按拖拽顺序重排配置文件中 services 列表"""
    require_operator(current_user)
    body = await request.json()
    order = body.get("order", [])
    if not isinstance(order, list) or not all(isinstance(n, str) for n in order):
        raise HTTPException(status_code=400, detail="order must be a list of service name strings")
    try:
        with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
            config = json.load(f)
        services = config.get("services", [])
        svc_map = {s["name"]: s for s in services}
        # 按传入顺序排列，未在 order 中的追加到末尾
        reordered = []
        for name in order:
            if name in svc_map:
                reordered.append(svc_map.pop(name))
        for s in svc_map.values():
            reordered.append(s)
        config["services"] = reordered
        with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2, ensure_ascii=False)
            f.write('\n')
        return {"ok": True, "order": [s["name"] for s in reordered]}
    except Exception as e:
        logger.error(f"Failed to save service order: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== Scheduled Restart API ====================

class ScheduledRestartRequest(BaseModel):
    service: str  # 'platform' or service name
    enabled: bool = False
    cron: str = ""  # 'HH:MM' or 'HH:MM@0,1,2,3,4'

@app.put("/api/scheduled-restart")
async def set_scheduled_restart(req: ScheduledRestartRequest, current_user: dict = Depends(get_current_user)):
    """Set or update scheduled restart config for a service. Admin/operator only."""
    require_operator(current_user)
    # Validate cron format
    if req.enabled and req.cron:
        parsed = _parse_cron(req.cron)
        if not parsed:
            raise HTTPException(status_code=400, detail="Invalid cron format. Use 'HH:MM' or 'HH:MM@0,1,2,3,4'")
    try:
        config = load_config()
        sr_data = {"enabled": req.enabled, "cron": req.cron}
        if req.service == 'platform':
            if 'platform' not in config:
                config['platform'] = {}
            # Preserve existing last_restart
            old_sr = config['platform'].get('scheduled_restart', {})
            sr_data["last_restart"] = old_sr.get("last_restart")
            config['platform']['scheduled_restart'] = sr_data
        else:
            found = False
            for svc in config.get('services', []):
                if svc.get('name') == req.service:
                    old_sr = svc.get('scheduled_restart', {})
                    sr_data["last_restart"] = old_sr.get("last_restart")
                    svc['scheduled_restart'] = sr_data
                    found = True
                    break
            if not found:
                raise HTTPException(status_code=404, detail=f"Service '{req.service}' not found")
        _save_config(config)
        append_audit_log(
            user=current_user["username"],
            role=current_user.get("role", "admin"),
            action="update_schedule",
            target=req.service,
            detail=f"enabled={req.enabled}, cron={req.cron}" if req.enabled else "disabled"
        )
        next_restart = _calc_next_restart(sr_data) if req.enabled else None
        return {"ok": True, "next_restart": next_restart}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to set scheduled restart: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/disks", response_model=List[DiskPartitionInfo])
async def list_disks(current_user: dict = Depends(get_current_user)):
    return get_disk_partitions()


# ==================== Process Tree API ====================

def _build_process_tree(pid: int) -> Optional[Dict]:
    """Build a process tree dict for a PID including all children recursively."""
    try:
        proc = psutil.Process(pid)
    except (psutil.NoSuchProcess, psutil.AccessDenied):
        return None

    def _proc_info(p: psutil.Process) -> Dict:
        info = {
            "pid": p.pid,
            "ppid": None,
            "name": "",
            "cmdline": "",
            "status": "",
            "cpu_percent": 0.0,
            "memory_mb": 0.0,
            "memory_percent": 0.0,
            "read_bytes": 0,
            "write_bytes": 0,
            "num_threads": 0,
            "create_time": None,
            "children": [],
        }
        try:
            info["ppid"] = p.ppid()
        except Exception:
            pass
        try:
            info["name"] = p.name()
        except Exception:
            pass
        try:
            cmdline = p.cmdline()
            info["cmdline"] = " ".join(cmdline) if cmdline else info["name"]
        except Exception:
            info["cmdline"] = info["name"]
        try:
            info["status"] = p.status()
        except Exception:
            pass
        try:
            info["cpu_percent"] = round(p.cpu_percent(interval=None), 2)
        except Exception:
            pass
        try:
            mem = p.memory_info()
            info["memory_mb"] = round(mem.rss / (1024 * 1024), 2)
        except Exception:
            pass
        try:
            info["memory_percent"] = round(p.memory_percent(), 2)
        except Exception:
            pass
        try:
            io = p.io_counters()
            info["read_bytes"] = getattr(io, "read_bytes", 0)
            info["write_bytes"] = getattr(io, "write_bytes", 0)
        except Exception:
            pass
        try:
            info["num_threads"] = p.num_threads()
        except Exception:
            pass
        try:
            info["create_time"] = datetime.fromtimestamp(p.create_time()).isoformat()
        except Exception:
            pass

        # Recurse into children
        try:
            for child in p.children(recursive=False):
                child_info = _proc_info(child)
                if child_info:
                    info["children"].append(child_info)
        except Exception:
            pass
        return info

    # First call cpu_percent to prime it, then gather info
    try:
        proc.cpu_percent(interval=None)
        for c in proc.children(recursive=True):
            try:
                c.cpu_percent(interval=None)
            except Exception:
                pass
    except Exception:
        pass

    import time
    time.sleep(0.1)  # brief pause for cpu_percent accuracy

    return _proc_info(proc)


@app.get("/api/process-tree")
async def get_process_tree(
    service: str = Query(..., description="Service name or 'platform'"),
    current_user: dict = Depends(get_current_user),
):
    """Get process tree for a service or platform, including all children with resource usage."""
    if service == "platform":
        pid = get_pid(LOGS_DIR / "platform.pid")
    else:
        pid = get_pid(LOGS_DIR / f"{service}.pid")

    if not pid:
        return {"service": service, "pid": None, "tree": None, "flat": []}

    tree = _build_process_tree(pid)
    if not tree:
        return {"service": service, "pid": pid, "tree": None, "flat": []}

    # Also provide a flat list for easy rendering
    flat = []
    def _flatten(node, depth=0):
        flat.append({
            "pid": node["pid"],
            "ppid": node["ppid"],
            "depth": depth,
            "name": node["name"],
            "cmdline": node["cmdline"],
            "status": node["status"],
            "cpu_percent": node["cpu_percent"],
            "memory_mb": node["memory_mb"],
            "memory_percent": node["memory_percent"],
            "read_bytes": node["read_bytes"],
            "write_bytes": node["write_bytes"],
            "num_threads": node["num_threads"],
            "create_time": node["create_time"],
        })
        for child in node.get("children", []):
            _flatten(child, depth + 1)
    _flatten(tree)

    return {"service": service, "pid": pid, "tree": tree, "flat": flat}


@app.post("/api/process-tree/kill")
async def kill_process(
    pid: int = Query(..., description="PID to kill"),
    service: str = Query(..., description="Service name for audit log"),
    kill_children: bool = Query(False, description="Also kill all children"),
    current_user: dict = Depends(get_current_user),
):
    """Kill a specific process or a process and all its children."""
    require_operator(current_user)
    killed = []
    failed = []
    try:
        proc = psutil.Process(pid)
        targets = [proc]
        if kill_children:
            try:
                targets = proc.children(recursive=True) + [proc]
            except Exception:
                pass

        for p in targets:
            try:
                p_pid = p.pid
                p.terminate()
                killed.append(p_pid)
            except Exception as e:
                failed.append({"pid": p.pid, "error": str(e)})

        # Give processes time to terminate, then force kill remaining
        import time
        time.sleep(0.5)
        for p in targets:
            try:
                if p.is_running():
                    p.kill()
            except Exception:
                pass

    except psutil.NoSuchProcess:
        raise HTTPException(status_code=404, detail=f"Process {pid} not found")
    except psutil.AccessDenied:
        raise HTTPException(status_code=403, detail=f"Access denied for PID {pid}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    detail = f"killed={killed}"
    if failed:
        detail += f", failed={failed}"
    append_audit_log(
        user=current_user["username"],
        role=current_user.get("role", "admin"),
        action="kill_pid",
        target=service,
        detail=detail,
    )
    return {"status": "success", "killed": killed, "failed": failed}


@app.get("/api/info", response_model=ServiceInfo)
async def get_info(service: str = Query("platform"), current_user: dict = Depends(get_current_user)):
    return get_service_info(service)


@app.post("/api/update/upload", response_model=UpdateTaskResponse)
async def upload_update_package(
    service: str = Query("platform"),
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_user)
):
    require_operator(current_user)
    if not file.filename or not file.filename.endswith(".tar.gz"):
        raise HTTPException(status_code=400, detail="Only .tar.gz packages are supported")
    upload_dir = SERVICE_DIR / "uploads"
    upload_dir.mkdir(exist_ok=True)
    task_id = uuid.uuid4().hex
    file_path = upload_dir / f"{service}-{task_id}.tar.gz"
    content = await file.read()
    file_path.write_bytes(content)

    UPDATE_TASKS[task_id] = {
        "service": service,
        "status": "queued",
        "update_progress": 0,
        "message": "Upload completed"
    }
    append_audit_log(
        user=current_user["username"],
        role=current_user.get("role", "admin"),
        action="upload",
        target=service,
        detail=f"file={file.filename}",
    )
    asyncio.create_task(run_update_task(task_id, service, file_path))
    return {"task_id": task_id}


@app.get("/api/update/progress", response_model=UpdateProgress)
async def get_update_progress(
    task_id: str = Query(...),
    current_user: dict = Depends(get_current_user)
):
    task = UPDATE_TASKS.get(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Update task not found")
    return UpdateProgress(
        task_id=task_id,
        status=task["status"],
        update_progress=task["update_progress"],
        message=task.get("message")
    )


@app.get("/api/update/backups", response_model=List[BackupInfo])
async def get_update_backups(
    service: str = Query("platform"),
    current_user: dict = Depends(get_current_user)
):
    return list_backups(service)


@app.post("/api/update/rollback")
async def rollback_update(
    service: str = Query("platform"),
    backup: str = Query(...),
    current_user: dict = Depends(get_current_user)
):
    require_operator(current_user)
    try:
        rollback_to_backup(service, backup)
        append_audit_log(
            user=current_user["username"],
            role=current_user.get("role", "admin"),
            action="rollback",
            target=service,
            detail=f"backup={backup}",
        )
        return {"status": "success", "message": "rollback completed"}
    except Exception as exc:
        append_audit_log(user=current_user["username"], role=current_user.get("role", "admin"), action="rollback", target=service, detail=f"backup={backup}", result="failed")
        raise HTTPException(status_code=400, detail=str(exc))

@app.get("/api/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat()
    }


@app.get("/api/status", response_model=PlatformStatus)
async def get_status(current_user: dict = Depends(get_current_user)) -> PlatformStatus:
    """Get current status of platform and all services."""
    try:
        config = load_config()
        
        # Platform status
        platform_pidfile = LOGS_DIR / 'platform.pid'
        platform_logfile = LOGS_DIR / 'platform.log'
        platform_cfg = config.get('platform') or {}
        platform_heartbeat = platform_cfg.get('heartbeat')
        platform_status = get_service_status('platform', platform_pidfile, platform_logfile, platform_heartbeat,
                                             scheduled_restart_cfg=platform_cfg.get('scheduled_restart'))
        
        # Services status
        services_status = []
        for service_cfg in config.get('services', []):
            service_name = service_cfg.get('name', 'unknown')
            pidfile = LOGS_DIR / f"{service_name}.pid"
            logfile = LOGS_DIR / f"{service_name}.log"
            heartbeat = service_cfg.get('heartbeat')
            services_status.append(get_service_status(service_name, pidfile, logfile, heartbeat,
                                                      scheduled_restart_cfg=service_cfg.get('scheduled_restart')))
        
        if platform_status.health == "running":
            overall_status = "running"
        elif platform_status.health == "abnormal":
            overall_status = "abnormal"
        else:
            overall_status = "stopped"
        
        return PlatformStatus(
            status=overall_status,
            platform=platform_status,
            services=services_status,
            timestamp=datetime.now().isoformat()
        )
    except Exception as e:
        logger.error(f"Error getting status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


async def build_dashboard_status() -> DashboardStatus:
    try:
        config = load_config()
        platform_pidfile = LOGS_DIR / 'platform.pid'
        platform_logfile = LOGS_DIR / 'platform.log'
        platform_cfg = config.get('platform') or {}
        platform_heartbeat = platform_cfg.get('heartbeat')
        platform_status = get_service_status('platform', platform_pidfile, platform_logfile, platform_heartbeat,
                                             scheduled_restart_cfg=platform_cfg.get('scheduled_restart'))

        services_status = []
        for service_cfg in config.get('services', []):
            service_name = service_cfg.get('name', 'unknown')
            pidfile = LOGS_DIR / f"{service_name}.pid"
            logfile = LOGS_DIR / f"{service_name}.log"
            heartbeat = service_cfg.get('heartbeat')
            services_status.append(get_service_status(service_name, pidfile, logfile, heartbeat,
                                                      scheduled_restart_cfg=service_cfg.get('scheduled_restart')))

        metrics = get_system_metrics()
        if platform_status.health == "running":
            overall_status = "running"
        elif platform_status.health == "abnormal":
            overall_status = "abnormal"
        else:
            overall_status = "stopped"

        return DashboardStatus(
            status=overall_status,
            platform=platform_status,
            services=services_status,
            metrics=metrics,
            timestamp=datetime.now().isoformat()
        )
    except Exception as e:
        logger.error(f"Error getting dashboard status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/dashboard", response_model=DashboardStatus)
async def get_dashboard_status(current_user: dict = Depends(get_current_user)) -> DashboardStatus:
    """Get complete dashboard status including system metrics."""
    return await build_dashboard_status()

# ==================== SSE Dashboard Endpoint ====================

@app.get("/api/dashboard/sse")
async def dashboard_sse(request: Request, token: Optional[str] = Query(None)):
    """SSE: 持续推送 DashboardStatus 实时数据"""
    get_user_from_request(request, token)

    async def event_generator():
        while True:
            if await request.is_disconnected():
                break
            try:
                status = await build_dashboard_status()
                data = status.model_dump_json()
                yield f"data: {data}\n\n"
            except Exception as e:
                logger.error(f"SSE dashboard error: {e}")
                break
            await asyncio.sleep(2)
    return StreamingResponse(event_generator(), media_type="text/event-stream")

async def _run_service_command(action: str, service: Optional[str], timeout: float = 30) -> dict:
    """Execute a single service control command asynchronously. Non-blocking for the event loop."""
    cmd = [
        sys.executable,
        str(SERVICE_DIR / 'manage_services.py'),
        action
    ]

    # 支持独立控制：平台服务 / 单个服务 / 全部
    if service:
        if service == 'platform':
            cmd.append('--platform')
            if action in ("start", "restart"):
                cmd.append('--daemon')
        else:
            cmd.extend(['--service', service])
            if action in ("start", "restart"):
                cmd.append('--daemon')
    else:
        if action in ("start", "restart"):
            cmd.append('--daemon')

    is_daemon = "--daemon" in cmd

    if is_daemon:
        # Daemonized: fire-and-forget, no blocking
        proc = await asyncio.create_subprocess_exec(
            *cmd,
            cwd=str(SERVICE_DIR),
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        # Don't await completion for daemon — just let it go
        return {
            "status": "success",
            "action": action,
            "service": service or "all",
            "message": f"Successfully executed '{action}'",
            "command": " ".join(cmd),
            "output": "",
            "stderr": "",
            "daemon": True,
        }
    else:
        # Non-daemon (stop): run with timeout, non-blocking via asyncio subprocess
        proc = await asyncio.create_subprocess_exec(
            *cmd,
            cwd=str(SERVICE_DIR),
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        try:
            stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=timeout)
        except asyncio.TimeoutError:
            proc.kill()
            await proc.wait()
            raise HTTPException(status_code=500, detail=f"Command timeout after {timeout}s for {service or 'all'}")

        stdout_str = stdout.decode(errors='replace') if stdout else ""
        stderr_str = stderr.decode(errors='replace') if stderr else ""

        if proc.returncode != 0:
            raise HTTPException(
                status_code=400,
                detail=f"Failed to {action} {service or 'services'}: {stderr_str}"
            )

        return {
            "status": "success",
            "action": action,
            "service": service or "all",
            "message": f"Successfully executed '{action}'",
            "command": " ".join(cmd),
            "output": stdout_str,
            "stderr": stderr_str,
            "daemon": False,
        }


@app.post("/api/control")
async def control_service(control: ServiceControl, current_user: dict = Depends(get_current_user)):
    """Control service (start/stop/restart). Requires operator or admin role.
       Uses per-service async lock to prevent concurrent conflicting operations."""
    require_operator(current_user)
    service_key = control.service or "__all__"
    lock = await _get_service_lock(service_key)

    # Try to acquire lock; if already locked, return 409 Conflict immediately
    if lock.locked():
        raise HTTPException(
            status_code=409,
            detail=f"Service '{control.service or 'all'}' is already being operated on by another user. Please wait."
        )

    async with lock:
        try:
            logger.info(f"Control action: {control.action} service={control.service} user={current_user['username']}")
            result = await _run_service_command(control.action, control.service)
            logger.info(f"Successfully executed '{control.action}' for {control.service or 'all'}")
            append_audit_log(
                user=current_user["username"],
                role=current_user.get("role", "admin"),
                action=control.action,
                target=control.service or "all",
            )
            return result
        except HTTPException:
            append_audit_log(user=current_user["username"], role=current_user.get("role", "admin"), action=control.action, target=control.service or "all", result="failed", detail="error")
            raise
        except Exception as e:
            logger.error(f"Control error: {e}")
            append_audit_log(user=current_user["username"], role=current_user.get("role", "admin"), action=control.action, target=control.service or "all", result="failed", detail=str(e))
            raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/batch-control")
async def batch_control_services(batch: BatchServiceControl, current_user: dict = Depends(get_current_user)):
    """Batch control multiple services concurrently. Each service runs in parallel with its own lock.
       Returns per-service results. Does not block the event loop."""
    require_operator(current_user)

    if not batch.services:
        raise HTTPException(status_code=400, detail="No services specified")

    if len(batch.services) > 50:
        raise HTTPException(status_code=400, detail="Too many services (max 50)")

    logger.info(f"Batch {batch.action}: {batch.services} by user={current_user['username']}")

    async def _control_one(service_name: str) -> dict:
        """Control a single service with its lock. Returns result dict."""
        lock = await _get_service_lock(service_name)
        if lock.locked():
            return {
                "service": service_name,
                "status": "skipped",
                "message": f"Service '{service_name}' is being operated by another user",
            }
        async with lock:
            try:
                result = await _run_service_command(batch.action, service_name)
                append_audit_log(
                    user=current_user["username"],
                    role=current_user.get("role", "admin"),
                    action=batch.action,
                    target=service_name,
                )
                return result
            except HTTPException as he:
                return {"service": service_name, "status": "failed", "message": he.detail}
            except Exception as e:
                return {"service": service_name, "status": "failed", "message": str(e)}

    # Run all service controls concurrently
    results = await asyncio.gather(*[_control_one(s) for s in batch.services])

    succeeded = sum(1 for r in results if r.get("status") == "success")
    skipped = sum(1 for r in results if r.get("status") == "skipped")
    failed = sum(1 for r in results if r.get("status") == "failed")

    append_audit_log(
        user=current_user["username"],
        role=current_user.get("role", "admin"),
        action=f"batch_{batch.action}",
        target=",".join(batch.services),
        detail=f"ok={succeeded} skipped={skipped} failed={failed}",
    )

    return {
        "status": "success" if failed == 0 else ("partial" if succeeded > 0 else "failed"),
        "action": batch.action,
        "total": len(batch.services),
        "succeeded": succeeded,
        "skipped": skipped,
        "failed": failed,
        "results": results,
    }


@app.get("/api/logs")
async def get_logs(
    service: str = Query("platform"),
    lines: str = Query("100"),
    offset: int = Query(0),
    search: Optional[str] = Query(None),
    level: Optional[str] = Query(None),
    range: Optional[str] = Query(None, alias="range"),
    current_user: dict = Depends(get_current_user)
) -> Dict:
    """Get log entries for a service. Reads across rotated log files (.log.N → .log).
    
    range: optional time range filter — '1h','6h','24h','7d','30d','all' or None.
    When set (and not 'all'), only log lines whose timestamp falls within the
    last N seconds are included.
    """
    # Precompute time-range cutoff (if any)
    _range_seconds = {"1h": 3600, "6h": 6*3600, "24h": 24*3600, "7d": 7*24*3600, "30d": 30*24*3600}
    time_cutoff = None
    if range and range != "all" and range in _range_seconds:
        time_cutoff = datetime.now() - timedelta(seconds=_range_seconds[range])
    try:
        log_file = LOGS_DIR / f"{service}.log"
        chain = _get_log_chain(service)
        
        if not chain:
            return {
                "service": service,
                "logs": [],
                "total": 0,
                "displayed": 0
            }

        _rotate_log_if_needed(log_file)
        
        # Read log files (chained: all backups + current)
        total_lines = 0
        # 读取所有日志（全量/搜索/分级/时间范围过滤时需全量扫描）
        if search or level or time_cutoff:
            # For search or level, read from ALL chained files (capped to MAX_LOG_SEARCH_LINES if >0)
            if MAX_LOG_SEARCH_LINES is not None and MAX_LOG_SEARCH_LINES > 0:
                recent_logs = deque(maxlen=MAX_LOG_SEARCH_LINES)
            else:
                recent_logs = []
            global_idx = 0
            for fpath in chain:
                try:
                    with open(fpath, 'r', encoding='utf-8', errors='ignore') as f:
                        for line in f:
                            if MAX_LOG_SEARCH_LINES is not None and MAX_LOG_SEARCH_LINES > 0:
                                recent_logs.append((global_idx, line))
                            else:
                                recent_logs.append((global_idx, line))
                            global_idx += 1
                except Exception:
                    pass
            total_lines = global_idx
            if MAX_LOG_SEARCH_LINES is not None and MAX_LOG_SEARCH_LINES > 0:
                base_index = max(total_lines - len(recent_logs), 0)
                indexed_logs = [(idx, line) for idx, line in recent_logs]
            else:
                indexed_logs = recent_logs
        else:
            try:
                n_lines = int(lines)
            except Exception:
                n_lines = 0 if str(lines).lower() in ("all", "0") else 100
            if n_lines <= 0:
                n_lines = MAX_LOG_LINES
            n_lines = min(n_lines, MAX_LOG_LINES)
            indexed_logs, total_lines = _read_chained_log_lines(chain, offset, n_lines)
            indexed_logs = [(idx, line) for idx, line in indexed_logs]

        # 先按分级过滤
        if level:
            level_upper = level.upper()
            indexed_logs = [
                (idx, line) for idx, line in indexed_logs
                if extract_log_level(line) == level_upper
            ]

        # 按时间范围过滤（如有）
        if time_cutoff:
            def _line_in_range(line: str) -> bool:
                ts_str = line[:19]  # e.g. "2026-02-12 10:23:45"
                try:
                    ts = datetime.strptime(ts_str, "%Y-%m-%d %H:%M:%S")
                    return ts >= time_cutoff
                except Exception:
                    return True  # 无法解析时间戳的行保留
            indexed_logs = [(idx, line) for idx, line in indexed_logs if _line_in_range(line)]

        # 再按搜索过滤
        if search:
            lowered = search.lower()
            filtered_indexed_logs = [
                (idx, line) for idx, line in indexed_logs
                if lowered in line.lower()
            ]
        else:
            filtered_indexed_logs = indexed_logs
        
        # Pagination
        try:
            n_lines = int(lines)
        except Exception:
            n_lines = 0 if str(lines).lower() in ("all", "0") else 100
        if n_lines > 0:
            n_lines = min(n_lines, MAX_LOG_LINES)

        if search:
            filtered_total = len(filtered_indexed_logs)
            if n_lines <= 0 or str(lines).lower() == "all":
                logs_to_return = filtered_indexed_logs
                real_offset = 0
            else:
                if offset < 0:
                    start = max(filtered_total + offset, 0)
                else:
                    start = offset
                end = min(start + n_lines, filtered_total)
                logs_to_return = filtered_indexed_logs[start:end]
                real_offset = start
        else:
            filtered_total = total_lines
            logs_to_return = filtered_indexed_logs
            if offset < 0:
                real_offset = max(filtered_total + offset, 0)
            else:
                real_offset = offset
        
        # Parse log entries
        entries = []
        for idx, log_line in logs_to_return:
            if log_line.strip():
                entry_level = extract_log_level(log_line)
                line_number = idx + 1
                entries.append({
                    "raw": log_line.rstrip(),
                    "level": entry_level,
                    "timestamp": log_line[:19] if len(log_line) > 19 else "",
                    "line": line_number,
                })
        
        return {
            "service": service,
            "logs": entries,
            "total": total_lines,
            "displayed": len(entries),
            "searched": filtered_total if search else total_lines,
            "offset": real_offset,
            "has_more_prev": real_offset > 0,
            "has_more_next": real_offset + len(entries) < filtered_total
        }
    except Exception as e:
        logger.error(f"Failed to get logs: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/metrics/history")
async def get_metrics_history(
    service: str = Query("platform"),
    limit: int = Query(MAX_METRICS_HISTORY_POINTS, ge=1, le=MAX_METRICS_POINTS),
    start: Optional[str] = Query(None),
    end: Optional[str] = Query(None),
    step_seconds: int = Query(0, ge=0),
    current_user: dict = Depends(get_current_user)
) -> Dict:
    """Return 24h history of process tree metrics for platform or a service."""
    try:
        history = list(METRICS_HISTORY.get(service, []))
        start_dt = _parse_iso_timestamp(start)
        end_dt = _parse_iso_timestamp(end)
        if start_dt or end_dt:
            filtered = []
            for point in history:
                ts = _parse_iso_timestamp(point.get("timestamp"))
                if not ts:
                    continue
                if start_dt and ts < start_dt:
                    continue
                if end_dt and ts > end_dt:
                    continue
                filtered.append(point)
            history = filtered
        if step_seconds and step_seconds > METRICS_INTERVAL_SECONDS:
            history = _downsample_points(history, step_seconds)
        if limit and len(history) > limit:
            history = history[-limit:]
        return {
            "service": service,
            "interval_seconds": METRICS_INTERVAL_SECONDS,
            "points": history,
            "count": len(history)
        }
    except Exception as e:
        logger.error(f"Failed to get metrics history: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Time range presets for system metrics history
_RANGE_SECONDS = {
    "1h": 3600,
    "6h": 6 * 3600,
    "24h": 24 * 3600,
    "7d": 7 * 24 * 3600,
    "30d": 30 * 24 * 3600,
}

@app.get("/api/system-metrics/history")
async def get_system_metrics_history(
    range: str = Query("1h"),
    current_user: dict = Depends(get_current_user),
) -> Dict:
    """Return system-level CPU/memory history for a given time range.
    range: 1h | 6h | 24h | 7d | 30d | all
    """
    try:
        entries = _load_system_metrics_history()
        now = datetime.now()

        # Filter by time range
        if range != "all" and range in _RANGE_SECONDS:
            cutoff = now - timedelta(seconds=_RANGE_SECONDS[range])
            entries = [e for e in entries if _parse_iso_timestamp(e.get("t")) and _parse_iso_timestamp(e.get("t")) >= cutoff]

        # Downsample for large ranges to keep response small (~500 points max)
        max_points = 500
        if len(entries) > max_points:
            step = len(entries) // max_points
            entries = entries[::step]

        return {
            "range": range,
            "points": entries,
            "count": len(entries),
        }
    except Exception as e:
        logger.error(f"Failed to get system metrics history: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/metrics/sse")
async def metrics_sse(request: Request, service: str = Query("platform"), token: Optional[str] = Query(None)):
    """SSE: stream latest metrics point for a service."""
    get_user_from_request(request, token)
    async def event_generator():
        while True:
            if await request.is_disconnected():
                break
            try:
                latest = METRICS_HISTORY.get(service, [])
                point = latest[-1] if latest else None
                if point:
                    yield f"data: {json.dumps(point)}\n\n"
            except Exception as e:
                logger.error(f"SSE metrics error: {e}")
                break
            await asyncio.sleep(METRICS_INTERVAL_SECONDS)

    return StreamingResponse(event_generator(), media_type="text/event-stream")


@app.get("/api/logs/download")
async def download_logs(service: str = Query("platform"), current_user: dict = Depends(get_current_user)):
    """Download all logs for a service (including rotated backups, merged chronologically)."""
    try:
        chain = _get_log_chain(service)
        if not chain:
            raise HTTPException(status_code=404, detail=f"Log file for {service} not found")
        
        if len(chain) == 1:
            # Single file — just download directly
            return FileResponse(
                path=chain[0],
                filename=f"{service}-logs-{datetime.now().strftime('%Y%m%d-%H%M%S')}.log",
                media_type="text/plain"
            )
        
        # Multiple files — stream merged content
        async def merged_stream():
            for fpath in chain:
                try:
                    with open(fpath, 'rb') as f:
                        while True:
                            chunk = f.read(65536)
                            if not chunk:
                                break
                            yield chunk
                except Exception:
                    pass
        
        return StreamingResponse(
            merged_stream(),
            media_type="text/plain",
            headers={
                "Content-Disposition": f'attachment; filename="{service}-logs-{datetime.now().strftime("%Y%m%d-%H%M%S")}.log"'
            }
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Download error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# 新增：统计所有日志文件分级数量
@app.get("/api/logs/level-counts")
async def get_log_level_counts(
    service: str = Query("platform"),
    range: Optional[str] = Query(None, alias="range"),
    current_user: dict = Depends(get_current_user)
) -> Dict:
    """Return log level counts for all chained log files of a service.
    
    range: optional time range filter — '1h','6h','24h','7d','30d','all' or None.
    """
    _range_seconds = {"1h": 3600, "6h": 6*3600, "24h": 24*3600, "7d": 7*24*3600, "30d": 30*24*3600}
    time_cutoff = None
    if range and range != "all" and range in _range_seconds:
        time_cutoff = datetime.now() - timedelta(seconds=_range_seconds[range])

    chain = _get_log_chain(service)
    counts = {"ERROR": 0, "WARNING": 0, "INFO": 0, "DEBUG": 0}
    for fpath in chain:
        try:
            with open(fpath, 'r', encoding='utf-8', errors='ignore') as f:
                for line in f:
                    # 时间范围过滤
                    if time_cutoff:
                        ts_str = line[:19]
                        try:
                            ts = datetime.strptime(ts_str, "%Y-%m-%d %H:%M:%S")
                            if ts < time_cutoff:
                                continue
                        except Exception:
                            pass
                    lvl = extract_log_level(line)
                    if lvl in counts:
                        counts[lvl] += 1
        except Exception:
            pass
    return {"service": service, "counts": counts}

# WebSocket connection manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, List[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, service: str):
        await websocket.accept()
        if service not in self.active_connections:
            self.active_connections[service] = []
        self.active_connections[service].append(websocket)
        logger.info(f"WebSocket connected for service: {service}")

    def disconnect(self, websocket: WebSocket, service: str):
        if service in self.active_connections:
            # 安全移除：连接可能已被移除/重复触发断开
            if websocket in self.active_connections[service]:
                self.active_connections[service].remove(websocket)
            if not self.active_connections[service]:
                del self.active_connections[service]
        logger.info(f"WebSocket disconnected for service: {service}")

    async def broadcast(self, service: str, message: dict):
        if service in self.active_connections:
            for connection in self.active_connections[service]:
                try:
                    await connection.send_json(message)
                except Exception as e:
                    logger.warning(f"Failed to send message: {e}")


manager = ConnectionManager()


@app.websocket("/api/ws/logs/{service}")
async def websocket_logs(websocket: WebSocket, service: str):
    """WebSocket endpoint for real-time log streaming."""
    token = websocket.query_params.get("token")
    if not token:
        await websocket.close(code=1008)
        return
    try:
        decode_token(token)
    except HTTPException:
        await websocket.close(code=1008)
        return

    await manager.connect(websocket, service)
    
    log_file = LOGS_DIR / f"{service}.log"
    
    try:
        # Start position at end of file
        file_position = 0
        if log_file.exists():
            file_position = log_file.stat().st_size
        
        pause = False
        
        while True:
            # Receive control messages
            try:
                data = await asyncio.wait_for(websocket.receive_json(), timeout=1.0)
                if data.get("action") == "pause":
                    pause = True
                    logger.debug(f"Paused logs for {service}")
                elif data.get("action") == "resume":
                    pause = False
                    logger.debug(f"Resumed logs for {service}")
                elif data.get("action") == "clear":
                    file_position = log_file.stat().st_size if log_file.exists() else 0
                    logger.debug(f"Cleared log position for {service}")
            except asyncio.TimeoutError:
                pass
            except Exception as e:
                logger.debug(f"WebSocket receive error: {e}")
                break
            
            # Check for new logs
            if not pause and log_file.exists():
                try:
                    current_size = log_file.stat().st_size
                    
                    if current_size < file_position:
                        file_position = 0

                    if current_size > file_position:
                        with open(log_file, 'r', encoding='utf-8', errors='ignore') as f:
                            f.seek(file_position)
                            new_logs = f.readlines()
                            file_position = current_size
                            
                            for log_line in new_logs:
                                if log_line.strip():
                                    level = extract_log_level(log_line)
                                    await websocket.send_json({
                                        "type": "log",
                                        "service": service,
                                        "raw": log_line.rstrip(),
                                        "level": level,
                                        "timestamp": log_line[:19] if len(log_line) > 19 else "",
                                    })
                except Exception as e:
                    logger.warning(f"Error reading logs: {e}")
            
            # Sleep to avoid busy waiting
            await asyncio.sleep(0.5)
    
    except WebSocketDisconnect:
        # 客户端（浏览器）断开 / 关闭页面时会走到这里
        logger.info(f"WebSocket client disconnected for service: {service}")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
    finally:
        # 无论何种原因退出，都要清理连接，防止 active_connections 泄漏
        manager.disconnect(websocket, service)
        try:
            await websocket.close(code=1000)
        except Exception:
            pass


# ==================== WebShell Terminal ====================

import pty
import struct
import fcntl
import termios
import signal

@app.websocket("/api/ws/terminal")
async def websocket_terminal(websocket: WebSocket):
    """WebSocket endpoint for interactive terminal (PTY). Admin only."""
    token = websocket.query_params.get("token")
    if not token:
        await websocket.close(code=1008)
        return
    try:
        user = decode_token(token)
        if user.get("role", "admin") != "admin":
            await websocket.close(code=1008, reason="Admin only")
            return
    except HTTPException:
        await websocket.close(code=1008)
        return

    await websocket.accept()

    # 创建 PTY 对
    master_fd, slave_fd = pty.openpty()
    shell = os.environ.get("SHELL", "/bin/bash")

    # 用 subprocess 启动 shell，stdin/stdout/stderr 绑定到 slave 端
    proc = subprocess.Popen(
        [shell, "--login"],
        stdin=slave_fd,
        stdout=slave_fd,
        stderr=slave_fd,
        cwd=str(SERVICE_DIR),
        preexec_fn=os.setsid,
        close_fds=True,
    )
    os.close(slave_fd)  # 父进程不需要 slave 端
    logger.info(f"Terminal session started, shell PID: {proc.pid}")

    loop = asyncio.get_event_loop()

    async def read_pty():
        """用 loop.add_reader 事件驱动地从 PTY 读取输出"""
        try:
            while True:
                # 等待 master_fd 可读
                readable = asyncio.Event()
                loop.add_reader(master_fd, readable.set)
                try:
                    await readable.wait()
                finally:
                    loop.remove_reader(master_fd)
                try:
                    data = os.read(master_fd, 16384)
                    if not data:
                        break
                    await websocket.send_text(data.decode("utf-8", errors="replace"))
                except OSError:
                    break
        except asyncio.CancelledError:
            pass

    async def write_pty():
        """接收 WebSocket 消息并写入 PTY"""
        try:
            while True:
                msg = await websocket.receive()
                if msg.get("type") == "websocket.disconnect":
                    break
                text = msg.get("text")
                if text is None:
                    continue
                # 检查是否是 resize 消息
                try:
                    payload = json.loads(text)
                    if payload.get("type") == "resize":
                        cols = payload.get("cols", 80)
                        rows = payload.get("rows", 24)
                        winsize = struct.pack("HHHH", rows, cols, 0, 0)
                        fcntl.ioctl(master_fd, termios.TIOCSWINSZ, winsize)
                        continue
                except (json.JSONDecodeError, TypeError):
                    pass
                # 普通输入
                try:
                    os.write(master_fd, text.encode("utf-8"))
                except OSError:
                    break
        except asyncio.CancelledError:
            pass

    try:
        read_task = asyncio.ensure_future(read_pty())
        write_task = asyncio.ensure_future(write_pty())

        done, pending = await asyncio.wait(
            [read_task, write_task],
            return_when=asyncio.FIRST_COMPLETED,
        )
        for task in pending:
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass

    except WebSocketDisconnect:
        logger.info(f"Terminal WebSocket disconnected, shell PID: {proc.pid}")
    except Exception as e:
        logger.error(f"Terminal error: {e}")
    finally:
        # 清理 reader（以防残留）
        try:
            loop.remove_reader(master_fd)
        except Exception:
            pass
        os.close(master_fd)
        # 终止 shell 进程
        try:
            os.killpg(os.getpgid(proc.pid), signal.SIGTERM)
        except Exception:
            pass
        try:
            proc.wait(timeout=2)
        except Exception:
            proc.kill()
        try:
            await websocket.close(code=1000)
        except Exception:
            pass
        logger.info(f"Terminal session ended, shell PID: {proc.pid}")


# ==================== Main ====================

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Service Manager Dashboard API")
    parser.add_argument("--host", default="0.0.0.0", help="Host to bind to")
    parser.add_argument("--port", type=int, default=8080, help="Port to bind to")
    parser.add_argument("--reload", action="store_true", help="Enable auto-reload")
    
    args = parser.parse_args()
    
    logger.info(f"Starting Service Manager Dashboard API on {args.host}:{args.port}")
    logger.info(f"API documentation: http://{args.host}:{args.port}/api/docs")
    
    # Mount frontend static files if they exist (for production)
    frontend_dist = SERVICE_DIR / 'frontend' / 'dist'
    if frontend_dist.exists():
        logger.info(f"Mounting frontend static files from {frontend_dist}")
        app.mount("/", StaticFiles(directory=frontend_dist, html=True), name="frontend")
    
    # Run the app directly using this module instead of "main:app" to avoid import conflicts
    uvicorn.run(
        app,
        host=args.host,
        port=args.port,
        reload=args.reload,
        log_level="info"
    )
