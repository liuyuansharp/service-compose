"""Background async tasks: metrics sampling, log maintenance, system metrics persistence."""

import asyncio
import json
from collections import deque
from datetime import datetime
from typing import Dict, List

import psutil

from .config import (
    LOGS_DIR, logger,
    load_config, get_all_services,
    METRICS_HISTORY, METRICS_LAST_IO_READ, METRICS_LAST_IO_WRITE,
    MAX_METRICS_POINTS, METRICS_INTERVAL_SECONDS,
    SYSTEM_METRICS_FILE, SYSTEM_METRICS_PERSIST_INTERVAL, SYSTEM_METRICS_MAX_POINTS,
)
from .services import get_pid, _get_process_tree_metrics
from .logs import rotate_log_if_needed, enforce_total_log_size


def _init_metrics_history(config: dict):
    global METRICS_HISTORY
    for svc in config.get("services", []):
        name = svc.get("name")
        if name:
            METRICS_HISTORY.setdefault(name, deque(maxlen=MAX_METRICS_POINTS))


async def metrics_sampler():
    while True:
        try:
            config = load_config()
            if not METRICS_HISTORY:
                _init_metrics_history(config)
            timestamp = datetime.now().isoformat()
            for svc in config.get("services", []):
                name = svc.get("name")
                if not name:
                    continue
                pid = get_pid(LOGS_DIR / f"{name}.pid")
                if pid:
                    m = _get_process_tree_metrics(pid)
                else:
                    m = {"cpu_percent": 0.0, "memory_mb": 0.0, "read_bytes": 0, "write_bytes": 0}
                last_read = METRICS_LAST_IO_READ.get(name, m["read_bytes"])
                last_write = METRICS_LAST_IO_WRITE.get(name, m["write_bytes"])
                delta_read = max(m["read_bytes"] - last_read, 0)
                delta_write = max(m["write_bytes"] - last_write, 0)
                METRICS_LAST_IO_READ[name] = m["read_bytes"]
                METRICS_LAST_IO_WRITE[name] = m["write_bytes"]
                METRICS_HISTORY.setdefault(name, deque(maxlen=MAX_METRICS_POINTS)).append({
                    "timestamp": timestamp,
                    "cpu_percent": m["cpu_percent"],
                    "memory_mb": m["memory_mb"],
                    "read_mb_s": round(delta_read / (1024 * 1024 * METRICS_INTERVAL_SECONDS), 3),
                    "write_mb_s": round(delta_write / (1024 * 1024 * METRICS_INTERVAL_SECONDS), 3)
                })
        except Exception as e:
            logger.warning(f"Metrics sampler error: {e}")
        await asyncio.sleep(METRICS_INTERVAL_SECONDS)


def _load_system_metrics_history() -> List[Dict]:
    if not SYSTEM_METRICS_FILE.exists():
        return []
    try:
        data = json.loads(SYSTEM_METRICS_FILE.read_text(encoding="utf-8"))
        return data if isinstance(data, list) else []
    except Exception:
        return []


def _save_system_metrics_history(entries: List[Dict]):
    if len(entries) > SYSTEM_METRICS_MAX_POINTS:
        entries = entries[-SYSTEM_METRICS_MAX_POINTS:]
    SYSTEM_METRICS_FILE.write_text(json.dumps(entries, ensure_ascii=False), encoding="utf-8")


async def system_metrics_persist_loop():
    logger.info("System metrics persistent sampler started")
    while True:
        await asyncio.sleep(SYSTEM_METRICS_PERSIST_INTERVAL)
        try:
            cpu = psutil.cpu_percent(interval=0)
            mem = psutil.virtual_memory()
            point = {"t": datetime.now().isoformat(), "c": round(cpu, 1), "m": round(mem.percent, 1)}
            entries = _load_system_metrics_history()
            entries.append(point)
            _save_system_metrics_history(entries)
        except Exception as e:
            logger.warning(f"System metrics persist error: {e}")


async def log_maintenance():
    while True:
        try:
            for log_file in LOGS_DIR.glob("*.log"):
                rotate_log_if_needed(log_file)
            enforce_total_log_size()
        except Exception as exc:
            logger.warning(f"Log maintenance error: {exc}")
        await asyncio.sleep(300)


# Re-export for routes
load_system_metrics_history = _load_system_metrics_history
