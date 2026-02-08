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
MAX_LOG_SEARCH_LINES = 5000
MAX_METRICS_HISTORY_POINTS = 2000
MAX_LOG_BYTES = 50 * 1024 * 1024
MAX_LOG_BACKUPS = 10
LOG_INDEX_STRIDE = 1000
LOG_INDEX_CACHE: Dict[str, Dict] = {}


# ==================== Authentication Helpers ====================

def init_auth_db():
    AUTH_DB_PATH.parent.mkdir(exist_ok=True)
    Base.metadata.create_all(bind=engine)
    session = SessionLocal()
    try:
        count = session.query(User).count()
        if count == 0:
            default_password = os.getenv('DEFAULT_ADMIN_PASSWORD', 'ly1234')
            session.add(User(username='liuyuan', password_hash=pwd_context.hash(default_password)))
            session.commit()
            logger.info("Created default liuyuan user 'liuyuan'")
    finally:
        session.close()


def get_user_by_username(username: str) -> Optional[Dict]:
    session = SessionLocal()
    try:
        user = session.query(User).filter(User.username == username).first()
        if not user:
            return None
        return {
            "id": user.id,
            "username": user.username,
            "password_hash": user.password_hash,
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

# Initialize FastAPI app
app = FastAPI(
    title="Service Manager Dashboard API",
    description="Real-time monitoring and control API for platform and microservices",
    version="1.0.0",
    docs_url="/api/docs",
    openapi_url="/api/openapi.json"
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


async def _log_maintenance():
    while True:
        try:
            for log_file in LOGS_DIR.glob("*.log"):
                _rotate_log_if_needed(log_file)
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


def get_service_status(name: str, pidfile: Path, log_file: Path, heartbeat_url: Optional[str] = None) -> ServiceStatus:
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
    
    return ServiceStatus(
        name=name,
        running=running,
        health=health,
        health_reason=health_reason,
        pid=pid if running else None,
        uptime=uptime,
        uptime_seconds=uptime_seconds,
        last_log=last_log
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
    try:
        if not log_file.exists():
            return
        if log_file.stat().st_size <= MAX_LOG_BYTES:
            return
        stamp = datetime.now().strftime('%Y%m%d%H%M%S')
        rotated = log_file.with_name(f"{log_file.stem}.{stamp}{log_file.suffix}")
        shutil.move(str(log_file), str(rotated))
        log_file.touch()
        backups = sorted(log_file.parent.glob(f"{log_file.stem}.*{log_file.suffix}"), key=lambda p: p.stat().st_mtime, reverse=True)
        for old in backups[MAX_LOG_BACKUPS:]:
            old.unlink(missing_ok=True)
        LOG_INDEX_CACHE.pop(str(log_file), None)
    except Exception as exc:
        logger.warning(f"Log rotate failed for {log_file}: {exc}")


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
        raise HTTPException(status_code=401, detail="Incorrect username or password")
    token = create_access_token({"sub": user["username"]})
    return {
        "token": token,
        "user": {
            "username": user["username"],
            "created_at": user.get("created_at")
        }
    }


@app.get("/api/me", response_model=UserProfile)
async def get_me(current_user: dict = Depends(get_current_user)):
    return {
        "username": current_user["username"],
        "created_at": current_user.get("created_at")
    }


@app.get("/api/disks", response_model=List[DiskPartitionInfo])
async def list_disks(current_user: dict = Depends(get_current_user)):
    return get_disk_partitions()


@app.get("/api/info", response_model=ServiceInfo)
async def get_info(service: str = Query("platform"), current_user: dict = Depends(get_current_user)):
    return get_service_info(service)


@app.post("/api/update/upload", response_model=UpdateTaskResponse)
async def upload_update_package(
    service: str = Query("platform"),
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_user)
):
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
    try:
        rollback_to_backup(service, backup)
        return {"status": "success", "message": "rollback completed"}
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc))

@app.on_event("startup")
async def _start_metrics_sampler():
    asyncio.create_task(_metrics_sampler())


@app.on_event("startup")
async def _start_log_maintenance():
    asyncio.create_task(_log_maintenance())


@app.on_event("startup")
async def _init_auth():
    init_auth_db()

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
        platform_heartbeat = (config.get('platform') or {}).get('heartbeat')
        platform_status = get_service_status('platform', platform_pidfile, platform_logfile, platform_heartbeat)
        
        # Services status
        services_status = []
        for service_cfg in config.get('services', []):
            service_name = service_cfg.get('name', 'unknown')
            pidfile = LOGS_DIR / f"{service_name}.pid"
            logfile = LOGS_DIR / f"{service_name}.log"
            heartbeat = service_cfg.get('heartbeat')
            services_status.append(get_service_status(service_name, pidfile, logfile, heartbeat))
        
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
        platform_heartbeat = (config.get('platform') or {}).get('heartbeat')
        platform_status = get_service_status('platform', platform_pidfile, platform_logfile, platform_heartbeat)

        services_status = []
        for service_cfg in config.get('services', []):
            service_name = service_cfg.get('name', 'unknown')
            pidfile = LOGS_DIR / f"{service_name}.pid"
            logfile = LOGS_DIR / f"{service_name}.log"
            heartbeat = service_cfg.get('heartbeat')
            services_status.append(get_service_status(service_name, pidfile, logfile, heartbeat))

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

@app.post("/api/control")
async def control_service(control: ServiceControl, current_user: dict = Depends(get_current_user)):
    """Control service (start/stop/restart)."""
    try:
        logger.info(f"Control action: {control.action}")
        
        # Build command
        cmd = [
            sys.executable,
            str(SERVICE_DIR / 'manage_services.py'),
            control.action
        ]

        # 支持独立控制：平台服务 / 单个服务 / 全部
        if control.service:
            if control.service == 'platform':
                cmd.append('--platform')
                if control.action in ("start", "restart"):
                    cmd.append('--daemon')
            else:
                cmd.extend(['--service', control.service])
                if control.action in ("start", "restart"):
                    cmd.append('--daemon')
        
        # Execute command
        if "--daemon" in cmd:
            # Daemonized start/restart should not block API request
            subprocess.Popen(
                cmd,
                cwd=str(SERVICE_DIR),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            result = subprocess.CompletedProcess(cmd, 0, stdout="", stderr="")
        else:
            result = subprocess.run(
                cmd,
                cwd=str(SERVICE_DIR),
                capture_output=True,
                text=True,
                timeout=30
            )
        
        if result.returncode != 0:
            logger.error(f"Command failed: {result.stderr}")
            raise HTTPException(
                status_code=400,
                detail=f"Failed to {control.action} services: {result.stderr}"
            )
        
        logger.info(f"Successfully executed '{control.action}'")
        return {
            "status": "success",
            "action": control.action,
            "message": f"Successfully executed '{control.action}'",
            "command": " ".join(cmd),
            "output": result.stdout,
            "stderr": result.stderr,
            "daemon": "--daemon" in cmd
        }
    except subprocess.TimeoutExpired:
        logger.error("Command timeout")
        raise HTTPException(status_code=500, detail="Command timeout")
    except Exception as e:
        logger.error(f"Control error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/logs")
async def get_logs(
    service: str = Query("platform"),
    lines: str = Query("100"),
    offset: int = Query(0),
    search: Optional[str] = Query(None),
    current_user: dict = Depends(get_current_user)
) -> Dict:
    """Get log entries for a service."""
    try:
        log_file = LOGS_DIR / f"{service}.log"
        
        if not log_file.exists():
            return {
                "service": service,
                "logs": [],
                "total": 0,
                "displayed": 0
            }

        _rotate_log_if_needed(log_file)
        
        # Read log file (cap search window to avoid large memory usage)
        total_lines = 0
        if search:
            recent_logs = deque(maxlen=MAX_LOG_SEARCH_LINES)
            with open(log_file, 'r', encoding='utf-8', errors='ignore') as f:
                for idx, line in enumerate(f):
                    total_lines = idx + 1
                    recent_logs.append(line)
            base_index = max(total_lines - len(recent_logs), 0)
            all_logs = list(recent_logs)
            indexed_logs = [(idx + base_index, line) for idx, line in enumerate(all_logs)]
        else:
            try:
                n_lines = int(lines)
            except Exception:
                n_lines = 0 if str(lines).lower() in ("all", "0") else 100
            if n_lines <= 0:
                n_lines = MAX_LOG_LINES
            n_lines = min(n_lines, MAX_LOG_LINES)
            indexed_logs, total_lines = _read_log_lines(log_file, offset, n_lines)
            indexed_logs = [(idx, line) for idx, line in indexed_logs]
        
        # Filter by search term，保留原始行号信息
        # 我们构造一个列表，元素为 (line_index, line_content)，这样即使过滤后也能知道原始行号
        if search:
            lowered = search.lower()
            filtered_indexed_logs = [
                (idx, line) for idx, line in indexed_logs
                if lowered in line.lower()
            ]
        else:
            filtered_indexed_logs = indexed_logs
        
        # 分段加载：offset为起始行，lines为加载行数
        try:
            n_lines = int(lines)
        except Exception:
            n_lines = 0 if str(lines).lower() in ("all", "0") else 100
        if n_lines > 0:
            n_lines = min(n_lines, MAX_LOG_LINES)

        if search:
            filtered_total = len(filtered_indexed_logs)
            # offset<0 表示从末尾倒数
            if n_lines <= 0 or str(lines).lower() == "all":
                logs_to_return = filtered_indexed_logs
                real_offset = 0
            else:
                # offset为正：从offset开始，取n_lines行
                # offset为负：从末尾倒数offset行开始，取n_lines行
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
                level = extract_log_level(log_line)
                # 原始行号（1-based）
                line_number = idx + 1
                entries.append({
                    "raw": log_line.rstrip(),
                    "level": level,
                    "timestamp": log_line[:19] if len(log_line) > 19 else "",
                    "line": line_number,
                })
        
        return {
            "service": service,
            "logs": entries,
            # total：原始文件总行数
            "total": total_lines,
            # displayed：当前返回的有效日志条数
            "displayed": len(entries),
            # searched：参与本次搜索的行数（无搜索时等于 total）
            "searched": filtered_total if search else total_lines,
            # offset：在 filtered_indexed_logs 中的起始下标（0-based），用于分页
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
    """Download logs for a service."""
    try:
        log_file = LOGS_DIR / f"{service}.log"
        
        if not log_file.exists():
            raise HTTPException(status_code=404, detail=f"Log file for {service} not found")
        
        return FileResponse(
            path=log_file,
            filename=f"{service}-logs-{datetime.now().strftime('%Y%m%d-%H%M%S')}.log",
            media_type="text/plain"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Download error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


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
