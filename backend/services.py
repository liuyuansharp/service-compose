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

# ---------- Network IO speed tracking ----------
import time as _net_time

_net_io_prev: Dict = {}        # {iface: (bytes_sent, bytes_recv, timestamp)}
_net_io_speed: Dict = {}       # {iface: (upload_MB_s, download_MB_s)}


def _refresh_net_io_speed():
    """Sample net_io_counters to compute per-interface upload/download MB/s."""
    global _net_io_prev, _net_io_speed
    try:
        counters = psutil.net_io_counters(pernic=True)
    except Exception:
        return
    if not counters:
        return
    now = _net_time.time()
    for name, c in counters.items():
        prev = _net_io_prev.get(name)
        if prev:
            dt = now - prev[2]
            if dt > 0:
                up = (c.bytes_sent - prev[0]) / dt / (1024 * 1024)
                down = (c.bytes_recv - prev[1]) / dt / (1024 * 1024)
                _net_io_speed[name] = (max(round(up, 2), 0), max(round(down, 2), 0))
        _net_io_prev[name] = (c.bytes_sent, c.bytes_recv, now)


def _get_net_io_totals() -> Dict:
    """Get cumulative network IO totals in GB per interface."""
    totals: Dict = {}
    try:
        counters = psutil.net_io_counters(pernic=True)
        if counters:
            for name, c in counters.items():
                totals[name] = (
                    round(c.bytes_sent / (1024 ** 3), 2),
                    round(c.bytes_recv / (1024 ** 3), 2),
                )
    except Exception:
        pass
    return totals


def _is_physical_nic(iface: str) -> bool:
    """Check if a network interface is a physical NIC (not virtual)."""
    # lo is always virtual
    if iface == "lo":
        return False
    # Known virtual prefixes
    _virtual_prefixes = (
        'veth', 'docker', 'br-', 'virbr', 'vnet', 'tun', 'tap',
        'flannel', 'cni', 'calico', 'wg', 'tailscale', 'utun',
        'vmnet', 'vboxnet', 'lxc', 'lxd',
    )
    iface_lower = iface.lower()
    for prefix in _virtual_prefixes:
        if iface_lower.startswith(prefix):
            return False
    # On Linux, physical NICs have /sys/class/net/<iface>/device
    sys_path = Path(f"/sys/class/net/{iface}/device")
    if sys_path.exists():
        return True
    # Fallback: if /sys not available, accept common physical patterns
    # (eth*, en*, em*, wl*, ww*, ib*, bond*, br0-9 bridges)
    import re
    if re.match(r'^(eth|en|em|wl|ww|ib|bond|br\d)\w*', iface_lower):
        return True
    return False


def _build_network_info() -> list:
    """Build network interfaces list with IP and real-time speed."""
    _refresh_net_io_speed()
    io_totals = _get_net_io_totals()
    nets = []
    try:
        import socket
        addrs = psutil.net_if_addrs()
        for iface, addr_list in addrs.items():
            if not _is_physical_nic(iface):
                continue
            ip = ""
            for addr in addr_list:
                if addr.family == socket.AF_INET:
                    ip = addr.address
                    break
            if not ip:
                continue
            speed = _net_io_speed.get(iface, (0.0, 0.0))
            total = io_totals.get(iface, (0.0, 0.0))
            nets.append({
                "interface": iface,
                "ip": ip,
                "upload_speed": speed[0],    # MB/s
                "download_speed": speed[1],  # MB/s
                "upload_total": total[0],    # GB
                "download_total": total[1],  # GB
            })
    except Exception:
        pass
    return nets


def get_system_info() -> dict:
    """Collect system hardware, OS and runtime info. Cached for 300s."""
    import platform
    import time as _time

    global _system_info_cache, _system_info_cache_time
    now = _time.time()
    if _system_info_cache and now - _system_info_cache_time < 300:
        # Static info cached, but network speed always fresh
        result = dict(_system_info_cache)
        result["network"] = _build_network_info()
        return result

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

    _system_info_cache = info
    _system_info_cache_time = now

    # Network is always fresh (speed data), appended after cache
    result = dict(info)
    result["network"] = _build_network_info()
    return result


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


# ---------- Disk IO speed tracking ----------
import time as _disk_time

_disk_io_prev: Dict = {}        # {disk_name: (read_bytes, write_bytes, timestamp)}
_disk_io_speed: Dict = {}       # {disk_name: (read_MB_s, write_MB_s)}


def _refresh_disk_io_speed():
    """Sample disk_io_counters to compute per-device read/write MB/s."""
    global _disk_io_prev, _disk_io_speed
    try:
        counters = psutil.disk_io_counters(perdisk=True)
    except Exception:
        return
    if not counters:
        return
    now = _disk_time.time()
    for name, c in counters.items():
        prev = _disk_io_prev.get(name)
        if prev:
            dt = now - prev[2]
            if dt > 0:
                r_speed = (c.read_bytes - prev[0]) / dt / (1024 * 1024)
                w_speed = (c.write_bytes - prev[1]) / dt / (1024 * 1024)
                _disk_io_speed[name] = (max(round(r_speed, 2), 0), max(round(w_speed, 2), 0))
        _disk_io_prev[name] = (c.read_bytes, c.write_bytes, now)


def _get_disk_io_totals() -> Dict:
    """Get cumulative IO totals in GB per device."""
    totals: Dict = {}
    try:
        counters = psutil.disk_io_counters(perdisk=True)
        if counters:
            for name, c in counters.items():
                totals[name] = (
                    round(c.read_bytes / (1024 ** 3), 2),
                    round(c.write_bytes / (1024 ** 3), 2),
                )
    except Exception:
        pass
    return totals


def _device_to_disk_name(device: str) -> str:
    """Map /dev/sda1 -> sda1, /dev/nvme0n1p1 -> nvme0n1p1, etc."""
    return os.path.basename(device)


def _find_parent_disk(dev_name: str, io_keys) -> str:
    """Try to match partition dev_name to a parent whole-disk in io_keys.
    e.g. sda1 -> sda, nvme0n1p1 -> nvme0n1"""
    if dev_name in io_keys:
        return dev_name
    # strip trailing partition number: sda1 -> sda
    import re
    # NVMe: nvme0n1p1 -> nvme0n1
    m = re.match(r'^(nvme\d+n\d+)p\d+$', dev_name)
    if m and m.group(1) in io_keys:
        return m.group(1)
    # sd/hd/vd: sda1 -> sda
    m = re.match(r'^([a-z]+)(\d+)$', dev_name)
    if m and m.group(1) in io_keys:
        return m.group(1)
    return dev_name


def get_disk_partitions() -> List[DiskPartitionInfo]:
    _refresh_disk_io_speed()
    io_totals = _get_disk_io_totals()
    io_keys = set(_disk_io_speed.keys()) | set(io_totals.keys())

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

        dev_name = _device_to_disk_name(part.device)
        io_name = _find_parent_disk(dev_name, io_keys)
        speed = _disk_io_speed.get(io_name, (0.0, 0.0))
        total_io = io_totals.get(io_name, (0.0, 0.0))

        partitions.append(DiskPartitionInfo(
            device=part.device, mountpoint=part.mountpoint, fstype=part.fstype,
            total_gb=usage.total // (1024 * 1024 * 1024),
            used_gb=usage.used // (1024 * 1024 * 1024),
            free_gb=usage.free // (1024 * 1024 * 1024),
            percent=round(usage.percent, 2),
            io_read_speed=speed[0],
            io_write_speed=speed[1],
            io_read_total=total_io[0],
            io_write_total=total_io[1],
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
