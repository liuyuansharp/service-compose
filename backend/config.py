"""Shared constants, paths and configuration loaders."""

import json
import logging
import os
from pathlib import Path
from typing import Dict, List
from collections import deque

# ---------- Paths ----------
RUN_DIR = Path(__file__).resolve().parent.parent          # project root
CONFIG_FILE = RUN_DIR / 'services_config.json'
LOGS_DIR = RUN_DIR / 'logs'
AUTH_DB_PATH = RUN_DIR / 'auth.db'
AUDIT_LOG_FILE = LOGS_DIR / 'audit.json'
SYSTEM_METRICS_FILE = LOGS_DIR / 'system_metrics_history.json'

# ---------- Auth ----------
SECRET_KEY = os.getenv('AUTH_SECRET_KEY', 'liuyuan_wsd')
ALGORITHM = 'HS256'
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv('ACCESS_TOKEN_EXPIRE_MINUTES', '480'))

# ---------- Metrics ----------
METRICS_INTERVAL_SECONDS = 10
METRICS_HISTORY_HOURS = 24
MAX_METRICS_POINTS = int(METRICS_HISTORY_HOURS * 3600 / METRICS_INTERVAL_SECONDS)
METRICS_HISTORY: Dict[str, deque] = {}
METRICS_LAST_IO_READ: Dict[str, int] = {}
METRICS_LAST_IO_WRITE: Dict[str, int] = {}
MAX_METRICS_HISTORY_POINTS = 2000

# ---------- Logs ----------
MAX_LOG_LINES = 500
MAX_LOG_SEARCH_LINES = -1
MAX_LOG_BYTES = 10 * 1024 * 1024
MAX_LOG_BACKUPS = 3
MAX_TOTAL_LOG_BYTES = 500 * 1024 * 1024
LOG_INDEX_STRIDE = 1000
LOG_INDEX_CACHE: Dict[str, Dict] = {}

# ---------- Audit ----------
AUDIT_LOG_MAX_ENTRIES = 5000

# ---------- System Metrics ----------
SYSTEM_METRICS_PERSIST_INTERVAL = 60
SYSTEM_METRICS_MAX_DAYS = 30
SYSTEM_METRICS_MAX_POINTS = SYSTEM_METRICS_MAX_DAYS * 24 * 60

# ---------- Updates ----------
UPDATE_TASKS: Dict[str, Dict] = {}

# ---------- Logger ----------
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('backend')

# ---------- Config ----------
def update_run_dir(services_conifg_path):
    services_conifg = {}
    try:
        with open(services_conifg_path, 'r') as f:
            services_conifg = json.load(f)
    except Exception as e:
        logger.error(f"Failed to load config: {e}")

    if services_conifg:
        run_dir = services_conifg.get("run_dir",None)
        if run_dir:
            global RUN_DIR, CONFIG_FILE, LOGS_DIR, AUTH_DB_PATH, AUDIT_LOG_FILE, SYSTEM_METRICS_FILE
            RUN_DIR = Path(run_dir)
            CONFIG_FILE = Path(services_conifg_path)
            LOGS_DIR = RUN_DIR / 'logs'
            AUTH_DB_PATH = RUN_DIR / 'auth.db'
            AUDIT_LOG_FILE = LOGS_DIR / 'audit.json'
            SYSTEM_METRICS_FILE = LOGS_DIR / 'system_metrics_history.json'
            LOGS_DIR.mkdir(exist_ok=True)
            logger.info(f"Updated run directory to: {RUN_DIR}")

def load_config() -> dict:
    """Load services configuration (unified format — only 'services' key)."""
    try:
        with open(CONFIG_FILE, 'r') as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Failed to load config: {e}")
        return {}


def save_config(config: dict):
    """Write config back to CONFIG_FILE."""
    with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
        json.dump(config, f, indent=2, ensure_ascii=False)
        f.write('\n')


def get_all_services(config: dict = None) -> List[dict]:
    """Return the flat services list from config. No more platform/services split."""
    if config is None:
        config = load_config()
    return config.get('services', [])


def get_service_cfg(name: str, config: dict = None) -> dict:
    """Get config dict for a single service by name."""
    for svc in get_all_services(config):
        if svc.get('name') == name:
            return svc
    return {}


def build_dependency_graph(config: dict = None) -> Dict[str, List[str]]:
    """Build adjacency list: service → [services it depends on].
    
    Returns dict like {'service_A': ['platform'], 'platform': [], ...}
    """
    services = get_all_services(config)
    graph = {}
    for svc in services:
        name = svc.get('name', '')
        graph[name] = svc.get('depends_on', [])
    return graph


def topological_sort(config: dict = None) -> List[List[str]]:
    """Return a list of *levels* for parallel startup.
    
    Each level is a list of service names that can start in parallel.
    Level 0 has no dependencies, Level 1 depends only on Level 0 services, etc.
    
    Raises ValueError on cyclic dependencies.
    """
    graph = build_dependency_graph(config)
    all_names = set(graph.keys())
    in_degree = {name: 0 for name in all_names}
    # reverse adjacency (who depends on me)
    dependents: Dict[str, List[str]] = {name: [] for name in all_names}
    for name, deps in graph.items():
        for dep in deps:
            if dep in all_names:
                in_degree[name] += 1
                dependents[dep].append(name)

    levels: List[List[str]] = []
    ready = [n for n in all_names if in_degree[n] == 0]
    visited = 0

    while ready:
        levels.append(sorted(ready))  # sort for determinism
        next_ready = []
        for n in ready:
            visited += 1
            for dep in dependents[n]:
                in_degree[dep] -= 1
                if in_degree[dep] == 0:
                    next_ready.append(dep)
        ready = next_ready

    if visited != len(all_names):
        raise ValueError(f"Cyclic dependency detected among services: "
                         f"{[n for n in all_names if in_degree[n] > 0]}")
    return levels


def get_reverse_dependents(config: dict = None) -> Dict[str, List[str]]:
    """Return reverse map: service → list of services that depend on it."""
    graph = build_dependency_graph(config)
    rev: Dict[str, List[str]] = {name: [] for name in graph}
    for name, deps in graph.items():
        for dep in deps:
            if dep in rev:
                rev[dep].append(name)
    return rev
