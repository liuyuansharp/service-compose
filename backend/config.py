"""Shared constants, paths and configuration loaders."""

import json
import logging
import os
from pathlib import Path
from typing import Dict, List
from collections import deque

import yaml

# ---------- Paths ----------
RUN_DIR = Path(__file__).resolve().parent.parent          # project root
CONFIG_FILE = RUN_DIR / 'services.yaml'


def _detect_config_file(base_dir: Path) -> Path:
    """Auto-detect config file: prefer .yaml, fallback to .json."""
    yaml_path = base_dir / 'services.yaml'
    json_path = base_dir / 'services.json'
    if yaml_path.exists():
        return yaml_path
    if json_path.exists():
        return json_path
    return yaml_path  # default


def _load_file(path: Path) -> dict:
    """Load config from YAML or JSON based on file extension."""
    suffix = path.suffix.lower()
    with open(path, 'r', encoding='utf-8') as f:
        if suffix == '.json':
            return json.load(f) or {}
        else:
            return yaml.safe_load(f) or {}


def _save_file(path: Path, data: dict):
    """Save config to YAML or JSON based on file extension."""
    suffix = path.suffix.lower()
    with open(path, 'w', encoding='utf-8') as f:
        if suffix == '.json':
            json.dump(data, f, ensure_ascii=False, indent=2)
        else:
            yaml.dump(data, f, default_flow_style=False, allow_unicode=True, sort_keys=False)


LOGS_DIR = RUN_DIR / 'logs'
_auth_db_env = os.getenv('AUTH_DB_PATH', '')
AUTH_DB_PATH = Path(_auth_db_env) if _auth_db_env else RUN_DIR / 'auth.db'
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
def _resolve_path(path_str: str, base_dir: Path) -> str:
    """Resolve a path relative to base_dir if it's not absolute."""
    p = Path(path_str)
    if p.is_absolute():
        return str(p)
    return str((base_dir / p).resolve())


def update_run_dir(services_conifg_path):
    services_conifg = {}
    config_dir = Path(services_conifg_path).resolve().parent
    try:
        services_conifg = _load_file(Path(services_conifg_path))
    except Exception as e:
        logger.error(f"Failed to load config: {e}")

    if services_conifg:
        run_dir = services_conifg.get("run_dir", None)
        if run_dir:
            resolved_run_dir = _resolve_path(run_dir, config_dir)
            global RUN_DIR, CONFIG_FILE, LOGS_DIR, AUTH_DB_PATH, AUDIT_LOG_FILE, SYSTEM_METRICS_FILE
            RUN_DIR = Path(resolved_run_dir)
            CONFIG_FILE = Path(services_conifg_path)
            LOGS_DIR = RUN_DIR / 'logs'
            if not _auth_db_env:
                AUTH_DB_PATH = RUN_DIR / 'auth.db'
            AUDIT_LOG_FILE = LOGS_DIR / 'audit.json'
            SYSTEM_METRICS_FILE = LOGS_DIR / 'system_metrics_history.json'
            LOGS_DIR.mkdir(exist_ok=True)
            logger.info(f"Updated run directory to: {RUN_DIR}")

def load_config() -> dict:
    """Load services configuration (unified format — only 'services' key).
    
    Supports both YAML (.yaml/.yml) and JSON (.json) formats.
    Returns raw config without resolving relative paths,
    so that save_config can preserve original relative paths.
    """
    try:
        return _load_file(CONFIG_FILE)
    except Exception as e:
        logger.error(f"Failed to load config: {e}")
        return {}


def load_config_resolved() -> dict:
    """Load config with all relative paths resolved to absolute.
    
    Use this when you need actual executable paths (e.g., for running services).
    Do NOT pass the result to save_config — it would overwrite relative paths.
    """
    cfg = load_config()
    config_dir = CONFIG_FILE.resolve().parent
    for svc in cfg.get('services', []):
        if 'cmd' in svc:
            svc['cmd'] = _resolve_path(svc['cmd'], config_dir)
    if 'run_dir' in cfg and cfg['run_dir']:
        cfg['run_dir'] = _resolve_path(cfg['run_dir'], config_dir)
    return cfg


def save_config(config: dict):
    """Write config back to CONFIG_FILE (auto-detect YAML/JSON by extension)."""
    _save_file(CONFIG_FILE, config)


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
