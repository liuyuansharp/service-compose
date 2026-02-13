"""Service status, heartbeat checking, process metrics."""

import os
import urllib.request
import urllib.error
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import psutil

from .config import (
    LOGS_DIR, RUN_DIR, logger,
    load_config, get_all_services,
    METRICS_HISTORY, METRICS_LAST_IO_READ, METRICS_LAST_IO_WRITE,
    MAX_METRICS_POINTS, METRICS_INTERVAL_SECONDS,
)
from .models import ServiceStatus, SystemMetrics, DiskPartitionInfo, ServiceInfo


# ---------- System Info (static hardware / OS details) ----------

_system_info_cache = None
_system_info_cache_time = 0


def get_system_info() -> dict:
    """Collect system hardware, OS and runtime info. Cached for 300s."""
    import platform
    import time as _time

    global _system_info_cache, _system_info_cache_time
    now = _time.time()
    if _system_info_cache and now - _system_info_cache_time < 300:
        return _system_info_cache

    info = {}

    # ── OS ──
    uname = platform.uname()
    info["hostname"] = uname.node
    info["os"] = f"{uname.system} {uname.release}"
    info["os_version"] = uname.version
    info["arch"] = uname.machine

    # Pretty name from /etc/os-release
    try:
        lines = Path("/etc/os-release").read_text().splitlines()
        kv = {}
        for line in lines:
            if "=" in line:
                k, v = line.split("=", 1)
                kv[k.strip()] = v.strip().strip('"')
        info["distro"] = kv.get("PRETTY_NAME", "")
    except Exception:
        info["distro"] = ""

    # glibc
    try:
        info["glibc"] = " ".join(platform.libc_ver())
    except Exception:
        info["glibc"] = ""

    # ── CPU ──
    info["cpu_model"] = ""
    try:
        with open("/proc/cpuinfo") as f:
            for line in f:
                if line.startswith("model name"):
                    info["cpu_model"] = line.split(":", 1)[1].strip()
                    break
    except Exception:
        pass
    info["cpu_cores_physical"] = psutil.cpu_count(logical=False) or 0
    info["cpu_cores_logical"] = psutil.cpu_count(logical=True) or 0

    # CPU frequency
    try:
        freq = psutil.cpu_freq()
        if freq:
            info["cpu_freq_mhz"] = round(freq.current, 0)
            info["cpu_freq_max_mhz"] = round(freq.max, 0) if freq.max else 0
        else:
            info["cpu_freq_mhz"] = 0
            info["cpu_freq_max_mhz"] = 0
    except Exception:
        info["cpu_freq_mhz"] = 0
        info["cpu_freq_max_mhz"] = 0

    # ── Memory ──
    mem = psutil.virtual_memory()
    info["memory_total_gb"] = round(mem.total / (1024 ** 3), 2)
    swap = psutil.swap_memory()
    info["swap_total_gb"] = round(swap.total / (1024 ** 3), 2)

    # ── Boot / Uptime ──
    try:
        boot = psutil.boot_time()
        info["boot_time"] = datetime.fromtimestamp(boot).isoformat()
        uptime_s = int(now - boot)
        days, rem = divmod(uptime_s, 86400)
        hours, rem = divmod(rem, 3600)
        minutes, _ = divmod(rem, 60)
        info["uptime"] = f"{days}d {hours}h {minutes}m"
    except Exception:
        info["boot_time"] = ""
        info["uptime"] = ""

    # ── Python ──
    info["python_version"] = platform.python_version()

    # ── Kernel ──
    info["kernel"] = uname.release

    # ── Load average ──
    try:
        la = os.getloadavg()
        info["load_avg"] = [round(v, 2) for v in la]
    except Exception:
        info["load_avg"] = []

    # ── Network interfaces (primary IPs only) ──
    try:
        addrs = psutil.net_if_addrs()
        nets = []
        import socket
        for iface, addr_list in addrs.items():
            if iface == "lo":
                continue
            for addr in addr_list:
                if addr.family == socket.AF_INET:
                    nets.append({"interface": iface, "ip": addr.address})
                    break
        info["network"] = nets
    except Exception:
        info["network"] = []

    _system_info_cache = info
    _system_info_cache_time = now
    return info


# ---------- PID ----------

def get_pid(pidfile: Path) -> Optional[int]:
    try:
        if pidfile.exists():
            content = pidfile.read_text().strip()
            if content.isdigit():
                return int(content)
    except Exception:
        pass
    return None


def is_process_running(pid: int) -> bool:
    try:
        os.kill(pid, 0)
        return True
    except (OSError, TypeError):
        return False


# ---------- Heartbeat ----------

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


# ---------- Service Status ----------

def get_service_status(
    name: str, pidfile: Path, log_file: Path,
    heartbeat_url: Optional[str] = None,
    scheduled_restart_cfg: Optional[Dict] = None,
    depends_on: Optional[List[str]] = None,
) -> ServiceStatus:
    pid = get_pid(pidfile)
    running_pid = pid is not None and is_process_running(pid)
    heartbeat_ok, heartbeat_reason = _check_heartbeat(heartbeat_url) if running_pid else (False, "missing")

    if running_pid and heartbeat_ok:
        health = "running"
        health_reason = None
    elif running_pid and not heartbeat_ok:
        health = "abnormal"
        health_reason = heartbeat_reason or "heartbeat_failed"
    else:
        health = "stopped"
        health_reason = None

    uptime = None
    uptime_seconds = None
    if running_pid and pid:
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
            pass

    last_log = None
    try:
        if log_file.exists() and log_file.stat().st_size > 0:
            with open(log_file, 'rb') as f:
                f.seek(0, 2)
                file_size = f.tell()
                read_size = min(500, file_size)
                f.seek(-read_size, 2)
                content = f.read().decode('utf-8', errors='ignore')
                lines = content.split('\n')
                for line in reversed(lines):
                    if line.strip():
                        last_log = line.strip()[:100]
                        break
    except Exception:
        pass

    sr_info = None
    if scheduled_restart_cfg:
        from .scheduled import _calc_next_restart
        sr_info = {
            "enabled": scheduled_restart_cfg.get("enabled", False),
            "cron": scheduled_restart_cfg.get("cron", ""),
            "last_restart": scheduled_restart_cfg.get("last_restart"),
            "next_restart": _calc_next_restart(scheduled_restart_cfg) if scheduled_restart_cfg.get("enabled") else None,
        }

    return ServiceStatus(
        name=name,
        running=running_pid,
        health=health,
        health_reason=health_reason,
        pid=pid if running_pid else None,
        uptime=uptime,
        uptime_seconds=uptime_seconds,
        last_log=last_log,
        scheduled_restart=sr_info,
        depends_on=depends_on or [],
    )


def extract_log_level(log_line: str) -> str:
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


# ---------- System Metrics ----------

def get_system_metrics() -> SystemMetrics:
    try:
        cpu_percents = psutil.cpu_percent(interval=0.1, percpu=True)
        cpu_count = len(cpu_percents) if cpu_percents else psutil.cpu_count()
        cpu_percent = round(sum(cpu_percents) / cpu_count, 2) if cpu_percents and cpu_count else 0.0
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        return SystemMetrics(
            cpu_percent=round(cpu_percent, 2),
            cpu_count=cpu_count,
            cpu_percents=[round(v, 2) for v in cpu_percents] if cpu_percents else [],
            memory_percent=round(memory.percent, 2),
            memory_used=memory.used // (1024 * 1024),
            memory_total=memory.total // (1024 * 1024),
            disk_percent=round(disk.percent, 2),
            disk_used=disk.used // (1024 * 1024 * 1024),
            disk_total=disk.total // (1024 * 1024 * 1024),
            disk_free=disk.free // (1024 * 1024 * 1024),
            timestamp=datetime.now().isoformat()
        )
    except Exception as e:
        logger.error(f"Failed to get system metrics: {e}")
        return SystemMetrics(
            cpu_percent=0.0, cpu_count=0, cpu_percents=[],
            memory_percent=0.0, memory_used=0, memory_total=0,
            disk_percent=0.0, disk_used=0, disk_total=0, disk_free=0,
            timestamp=datetime.now().isoformat()
        )


def get_disk_partitions() -> List[DiskPartitionInfo]:
    partitions = []
    seen = set()
    network_fs = {'nfs', 'nfs4', 'cifs', 'smbfs', 'sshfs', 'fuse.sshfs', 'fuse.glusterfs',
                  'glusterfs', 'ceph', 'fuse.ceph', 'fuse.rclone', 'afp', 'davfs', 'fuseblk'}
    virtual_fs = {'tmpfs', 'overlay', 'squashfs', 'proc', 'sysfs', 'devtmpfs', 'cgroup',
                  'cgroup2', 'pstore', 'securityfs', 'debugfs', 'tracefs', 'configfs',
                  'fusectl', 'mqueue', 'hugetlbfs', 'rpc_pipefs', 'autofs'}
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
            device=part.device, mountpoint=part.mountpoint, fstype=part.fstype,
            total_gb=usage.total // (1024 * 1024 * 1024),
            used_gb=usage.used // (1024 * 1024 * 1024),
            free_gb=usage.free // (1024 * 1024 * 1024),
            percent=round(usage.percent, 2)
        ))
    partitions.sort(key=lambda item: item.total_gb, reverse=True)
    return partitions


# ---------- Process Tree Metrics ----------

def _get_process_tree_metrics(pid: int) -> Dict:
    try:
        proc = psutil.Process(pid)
    except Exception:
        return {"cpu_percent": 0.0, "memory_mb": 0.0, "read_bytes": 0, "write_bytes": 0}
    processes = [proc]
    try:
        processes.extend(proc.children(recursive=True))
    except Exception:
        pass
    total_cpu = total_mem = total_read = total_write = 0
    for p in processes:
        try: total_cpu += p.cpu_percent(interval=None)
        except Exception: pass
        try: total_mem += p.memory_info().rss
        except Exception: pass
        try:
            io = p.io_counters()
            total_read += getattr(io, "read_bytes", 0)
            total_write += getattr(io, "write_bytes", 0)
        except Exception: pass
    return {
        "cpu_percent": round(total_cpu, 2),
        "memory_mb": round(total_mem / (1024 * 1024), 2),
        "read_bytes": total_read,
        "write_bytes": total_write
    }


def get_service_info(service_name: str) -> ServiceInfo:
    from .update import read_manifest
    manifest = read_manifest(RUN_DIR / "deployments" / service_name)
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
        pass
    return ServiceInfo(
        name=service_name,
        version=manifest.get("version", "unknown"),
        commit_hash=manifest.get("commit_hash", "unknown"),
        build_date=manifest.get("build_date", "unknown"),
        uptime=uptime,
        uptime_seconds=uptime_seconds
    )


# ---------- Process tree detail ----------

def build_process_tree(pid: int) -> Optional[Dict]:
    try:
        proc = psutil.Process(pid)
    except (psutil.NoSuchProcess, psutil.AccessDenied):
        return None

    def _proc_info(p):
        info = {
            "pid": p.pid, "ppid": None, "name": "", "cmdline": "", "status": "",
            "cpu_percent": 0.0, "memory_mb": 0.0, "memory_percent": 0.0,
            "read_bytes": 0, "write_bytes": 0, "num_threads": 0, "create_time": None, "children": [],
        }
        try: info["ppid"] = p.ppid()
        except Exception: pass
        try: info["name"] = p.name()
        except Exception: pass
        try:
            cmdline = p.cmdline()
            info["cmdline"] = " ".join(cmdline) if cmdline else info["name"]
        except Exception: info["cmdline"] = info["name"]
        try: info["status"] = p.status()
        except Exception: pass
        try: info["cpu_percent"] = round(p.cpu_percent(interval=None), 2)
        except Exception: pass
        try: info["memory_mb"] = round(p.memory_info().rss / (1024 * 1024), 2)
        except Exception: pass
        try: info["memory_percent"] = round(p.memory_percent(), 2)
        except Exception: pass
        try:
            io = p.io_counters()
            info["read_bytes"] = getattr(io, "read_bytes", 0)
            info["write_bytes"] = getattr(io, "write_bytes", 0)
        except Exception: pass
        try: info["num_threads"] = p.num_threads()
        except Exception: pass
        try: info["create_time"] = datetime.fromtimestamp(p.create_time()).isoformat()
        except Exception: pass
        try:
            for child in p.children(recursive=False):
                ci = _proc_info(child)
                if ci:
                    info["children"].append(ci)
        except Exception: pass
        return info

    try:
        proc.cpu_percent(interval=None)
        for c in proc.children(recursive=True):
            try: c.cpu_percent(interval=None)
            except Exception: pass
    except Exception:
        pass

    import time
    time.sleep(0.1)
    return _proc_info(proc)
