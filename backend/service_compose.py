#!/usr/bin/env python3

import argparse
import json
import logging
import logging.handlers
import os
import signal
import subprocess
import sys
import threading
import time
from pathlib import Path
from datetime import datetime
from typing import Dict, List

import yaml

try:
    import psutil
    _HAS_PSUTIL = True
except ImportError:
    _HAS_PSUTIL = False

ROOT = Path(__file__).resolve().parent.parent          # backend/ -> project root
CONFIG_FILE = ROOT / 'services.yaml'


def _load_file(path: Path) -> dict:
    """Load config from YAML or JSON based on file extension."""
    suffix = path.suffix.lower()
    with open(path, 'r', encoding='utf-8') as f:
        if suffix == '.json':
            return json.load(f) or {}
        else:
            return yaml.safe_load(f) or {}
LOGS_DIR = ROOT / 'logs'

def setup_logger(name, log_file, max_bytes=10*1024*1024, backup_count=3):
    """Setup rotating file handler for each service.
    
    Args:
        name: logger name
        log_file: path to log file
        max_bytes: max file size before rotation (default 10MB)
        backup_count: number of backup files to keep (default 5)
    """
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)
    
    # Avoid adding duplicate handlers if logger already exists
    if logger.handlers:
        return logger
    
    # Create logs directory
    LOGS_DIR.mkdir(exist_ok=True)
    
    # Rotating file handler
    handler = logging.handlers.RotatingFileHandler(
        log_file, maxBytes=max_bytes, backupCount=backup_count
    )
    handler.setLevel(logging.DEBUG)
    
    # Format: timestamp | level | message
    formatter = logging.Formatter(
        '%(asctime)s | %(levelname)-8s | %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    
    return logger


def build_dependency_graph(services: List[dict] = []) -> Dict[str, List[str]]:
    """Build adjacency list: service → [services it depends on].
    
    Returns dict like {'service_A': ['platform'], 'platform': [], ...}
    """
    graph = {}
    for svc in services:
        name = svc.get('name', '')
        graph[name] = svc.get('depends_on', [])
    return graph


def topological_sort(services: List[dict] = []) -> List[List[str]]:
    """Return a list of *levels* for parallel startup.
    
    Each level is a list of service names that can start in parallel.
    Level 0 has no dependencies, Level 1 depends only on Level 0 services, etc.
    
    Raises ValueError on cyclic dependencies.
    """
    graph = build_dependency_graph(services)
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


def _resolve_path(path_str: str, base_dir: Path) -> str:
    """Resolve a path relative to base_dir if it's not absolute."""
    p = Path(path_str)
    if p.is_absolute():
        return str(p)
    return str((base_dir / p).resolve())


class ServiceProcess:
    """Manages a single service process with auto-restart, logging, and pid tracking."""
    
    # Exponential backoff: 1s, 2s, 4s, 8s, 16s, 32s, then cap at 60s
    RESTART_DELAYS = [1, 2, 4, 8, 16, 32, 60]
    MAX_RESTART_ATTEMPTS_PER_MINUTE = 5  # Prevent restart storms
    
    def __init__(self, name, cmd, args, restart_on_exit=True):
        self.name = name
        self.cmd = cmd
        self.args = args or []
        self.log_file = LOGS_DIR / f'{name}.log'
        self.pidfile = LOGS_DIR / f'{name}.pid'
        self.stopflag = LOGS_DIR / f'{name}.stop'   # cross-process stop signal
        self.restart_on_exit = restart_on_exit
        self.process = None
        self._stop_requested = threading.Event()
        self._lock = threading.Lock()
        
        # Restart tracking
        self.restart_count = 0
        self.last_restart_time = None
        self.restart_times_this_minute = []  # timestamps of restarts in last minute
        
        # Setup logger
        self.logger = setup_logger(name, str(self.log_file))
        self.logger.info(f"Service '{name}' initialized")

    def _get_restart_delay(self):
        """Calculate restart delay based on consecutive failures.
        
        Returns exponential backoff delay, capped at MAX_RESTART_DELAYS[-1].
        """
        idx = min(self.restart_count, len(self.RESTART_DELAYS) - 1)
        return self.RESTART_DELAYS[idx]

    def _check_restart_storm(self):
        """Check if we're in a restart storm (too many restarts in short time).
        
        Returns True if we should skip restart to prevent storm.
        """
        now = time.time()
        # Remove timestamps older than 1 minute
        self.restart_times_this_minute = [
            t for t in self.restart_times_this_minute 
            if now - t < 60
        ]
        
        if len(self.restart_times_this_minute) >= self.MAX_RESTART_ATTEMPTS_PER_MINUTE:
            self.logger.error(
                f"Restart storm detected ({len(self.restart_times_this_minute)} "
                f"restarts in 1 minute). Giving up on auto-restart."
            )
            return True
        return False

    def _write_pid(self, pid):
        """Write process pid to pidfile."""
        try:
            self.pidfile.parent.mkdir(parents=True, exist_ok=True)
            with open(self.pidfile, 'w') as f:
                f.write(str(pid))
            self.logger.debug(f"Wrote PID {pid} to {self.pidfile}")
        except Exception as e:
            self.logger.error(f"Failed to write pidfile: {e}")

    def _remove_pidfile(self):
        """Remove pidfile."""
        try:
            if self.pidfile.exists():
                self.pidfile.unlink()
                self.logger.debug(f"Removed pidfile {self.pidfile}")
        except Exception as e:
            self.logger.error(f"Failed to remove pidfile: {e}")

    def _write_stop_flag(self):
        """Write stop flag file to signal watcher threads (including in other
        daemon processes) that this service should NOT be auto-restarted."""
        try:
            self.stopflag.parent.mkdir(parents=True, exist_ok=True)
            self.stopflag.write_text(str(time.time()))
            self.logger.debug(f"Wrote stop flag {self.stopflag}")
        except Exception as e:
            self.logger.error(f"Failed to write stop flag: {e}")

    def _remove_stop_flag(self):
        """Remove stop flag file (called before start)."""
        try:
            if self.stopflag.exists():
                self.stopflag.unlink()
                self.logger.debug(f"Removed stop flag {self.stopflag}")
        except Exception as e:
            self.logger.error(f"Failed to remove stop flag: {e}")

    def _is_stop_flagged(self):
        """Check if stop flag exists (another process requested stop)."""
        return self.stopflag.exists()

    def _read_pid_from_file(self):
        """Read PID from pidfile. Returns int or None."""
        try:
            if self.pidfile.exists():
                pid_str = self.pidfile.read_text().strip()
                if pid_str.isdigit():
                    return int(pid_str)
        except Exception as e:
            self.logger.debug(f"Failed to read pidfile: {e}")
        return None

    def _kill_pid(self, pid, timeout=10):
        """Kill a process and ALL its descendants (entire process tree), best-effort.

        Uses psutil to walk the full child tree so that grandchild processes
        (e.g. uvicorn workers spawned by a shell wrapper) are also terminated.
        Falls back to process-group kill when psutil is unavailable.

        Returns True if the process tree was successfully terminated.
        """
        try:
            os.kill(pid, 0)
        except ProcessLookupError:
            self.logger.debug(f"PID {pid} does not exist")
            return True
        except PermissionError:
            self.logger.warning(f"No permission to signal PID {pid}")
            return False

        self.logger.info(f"Killing process tree rooted at PID {pid}")

        # ---- Collect the full process tree via psutil ----
        all_pids = set()
        if _HAS_PSUTIL:
            try:
                parent = psutil.Process(pid)
                # children(recursive=True) returns all descendants
                descendants = parent.children(recursive=True)
                all_pids = {p.pid for p in descendants}
                all_pids.add(pid)
                self.logger.debug(
                    f"Process tree for PID {pid}: {sorted(all_pids)} "
                    f"({len(all_pids)} processes)"
                )
            except (psutil.NoSuchProcess, psutil.AccessDenied) as e:
                self.logger.debug(f"psutil tree walk failed: {e}, falling back to pgid")
                all_pids = {pid}
        else:
            all_pids = {pid}

        # ---- Phase 1: SIGTERM to process group + every known PID ----
        # Kill the process group (covers children that stayed in the group)
        try:
            pgid = os.getpgid(pid)
            my_pgid = os.getpgid(os.getpid())
            if pgid != my_pgid:
                os.killpg(pgid, signal.SIGTERM)
                self.logger.debug(f"Sent SIGTERM to process group {pgid}")
            else:
                self.logger.debug(f"PID {pid} shares our pgid, skipping killpg")
        except Exception as e:
            self.logger.debug(f"killpg SIGTERM failed: {e}")

        # Also SIGTERM each descendant individually (covers processes that
        # may have changed their own process group)
        for cpid in all_pids:
            try:
                os.kill(cpid, signal.SIGTERM)
            except (ProcessLookupError, PermissionError):
                pass

        # ---- Phase 2: wait for all to exit ----
        start_t = time.time()
        while time.time() - start_t < timeout:
            alive = set()
            for cpid in all_pids:
                try:
                    os.kill(cpid, 0)
                    alive.add(cpid)
                except (ProcessLookupError, PermissionError):
                    pass
            if not alive:
                self.logger.info(
                    f"Process tree (root {pid}, {len(all_pids)} procs) "
                    f"terminated gracefully"
                )
                return True
            time.sleep(0.3)

        # ---- Phase 3: SIGKILL survivors ----
        # Re-collect tree in case new children were spawned during grace period
        if _HAS_PSUTIL:
            try:
                parent = psutil.Process(pid)
                for ch in parent.children(recursive=True):
                    all_pids.add(ch.pid)
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass

        alive_pids = set()
        for cpid in all_pids:
            try:
                os.kill(cpid, 0)
                alive_pids.add(cpid)
            except (ProcessLookupError, PermissionError):
                pass

        if alive_pids:
            self.logger.warning(
                f"PIDs still alive after {timeout}s: {sorted(alive_pids)}, "
                f"sending SIGKILL"
            )
            # killpg SIGKILL
            try:
                pgid = os.getpgid(pid)
                my_pgid = os.getpgid(os.getpid())
                if pgid != my_pgid:
                    os.killpg(pgid, signal.SIGKILL)
            except Exception:
                pass
            # Also SIGKILL each individually
            for cpid in alive_pids:
                try:
                    os.kill(cpid, signal.SIGKILL)
                except (ProcessLookupError, PermissionError):
                    pass

        # ---- Final check ----
        time.sleep(0.5)
        still_alive = []
        for cpid in all_pids:
            try:
                os.kill(cpid, 0)
                still_alive.append(cpid)
            except (ProcessLookupError, PermissionError):
                pass

        if still_alive:
            self.logger.error(
                f"PIDs still alive after SIGKILL: {still_alive}"
            )
            return False

        self.logger.info(f"Process tree (root {pid}) fully killed")
        return True

    def start(self, _from_watcher=False):
        """Start the service process.

        Args:
            _from_watcher: Internal flag. When True (called by _watch for
                auto-restart), do NOT clear the stop flag file so that a
                concurrent stop command is respected.
        """
        with self._lock:
            if self.process and self.process.poll() is None:
                self.logger.info(f"Already running (pid={self.process.pid})")
                return

            if not _from_watcher:
                # External / explicit start — clear stop flag
                self._remove_stop_flag()
            else:
                # Auto-restart from watcher — recheck flag under lock
                if self._is_stop_flagged():
                    self.logger.info(
                        "Stop flag detected inside start() (from watcher), aborting"
                    )
                    return

            # Check for residual process from pidfile (e.g. from a previous manager instance)
            old_pid = self._read_pid_from_file()
            if old_pid:
                try:
                    os.kill(old_pid, 0)
                    # Process exists — kill it before starting a new one
                    self.logger.warning(
                        f"Found residual process PID {old_pid} from pidfile, killing before start"
                    )
                    self._kill_pid(old_pid)
                except ProcessLookupError:
                    self.logger.debug(f"Stale pidfile (PID {old_pid} not running), cleaning up")
                except PermissionError:
                    self.logger.warning(f"Residual PID {old_pid} exists but no permission to check/kill")
                self._remove_pidfile()

            LOGS_DIR.mkdir(exist_ok=True)
            cmd = [self.cmd] + self.args
            self.logger.info(f"Starting: {' '.join(cmd)}")
            
            try:
                # Start process in its own process group (for better signal handling)
                self.process = subprocess.Popen(
                    cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    preexec_fn=os.setsid,
                    text=True,
                    bufsize=1  # line buffered
                )
                self._write_pid(self.process.pid)
                self.restart_count = 0  # Reset counter on successful start
                
                # Start a watcher thread
                t = threading.Thread(target=self._watch, daemon=True)
                t.start()
                self.logger.info(f"Started with PID {self.process.pid}")
            except Exception as e:
                self.logger.error(f"Failed to start: {e}")

    def stop(self, timeout=10):
        """Stop the service process gracefully."""
        with self._lock:
            self._stop_requested.set()

            # Write stop flag FIRST — this signals any daemon watcher thread
            # (including those in other processes) to NOT auto-restart
            self._write_stop_flag()
            
            if not self.process:
                # No in-memory process handle — try to recover PID from pidfile
                old_pid = self._read_pid_from_file()
                if old_pid:
                    self.logger.info(
                        f"No in-memory process handle, but found PID {old_pid} in pidfile. "
                        f"Attempting to kill residual process."
                    )
                    self._kill_pid(old_pid, timeout=timeout)
                    self._remove_pidfile()
                    self.logger.info("Residual process stopped via pidfile")
                else:
                    self._remove_pidfile()
                    self.logger.info("Not running, nothing to stop")
                return
            
            if self.process.poll() is not None:
                self._remove_pidfile()
                self.logger.info("Already stopped")
                return
            
            self.logger.info(f"Stopping (pid={self.process.pid}), timeout={timeout}s")
            
            try:
                # Kill the entire process tree (shell script + all children)
                self._kill_pid(self.process.pid, timeout=timeout)
                
                # Ensure the Popen object is reaped to avoid zombies
                try:
                    self.process.wait(timeout=2)
                except Exception:
                    pass
                
                self.logger.info("Process tree stopped")
            except Exception as e:
                self.logger.error(f"Error stopping: {e}")
            finally:
                self._remove_pidfile()

    def _watch(self):
        """Watch the process and handle restart logic."""
        while not self._stop_requested.is_set():
            if not self.process:
                break
            
            # Read output line by line and log it
            try:
                for line in self.process.stdout:
                    if line:
                        self.logger.info(f"[OUTPUT] {line.rstrip()}")
            except Exception:
                pass
            
            ret = self.process.poll()
            
            if ret is None:
                time.sleep(0.5)
                continue
            
            # Process exited
            self.logger.warning(f"Process exited with code {ret}")
            self._remove_pidfile()
            
            # Check cross-process stop flag BEFORE deciding to restart.
            # Another process (e.g. a stop command from the Web UI) may have
            # written this flag to tell us not to restart.
            if self._is_stop_flagged():
                self.logger.info(
                    "Stop flag detected — service was stopped intentionally, "
                    "skipping auto-restart"
                )
                break
            
            if self.restart_on_exit and not self._stop_requested.is_set():
                # Check for restart storm
                if self._check_restart_storm():
                    self.logger.critical("Giving up on auto-restart due to storm")
                    break
                
                self.restart_count += 1
                self.restart_times_this_minute.append(time.time())
                delay = self._get_restart_delay()
                
                self.logger.warning(
                    f"Will restart in {delay}s (attempt {self.restart_count}, "
                    f"exponential backoff)"
                )
                time.sleep(delay)
                
                # Re-check stop flag after delay (stop may have arrived during wait)
                if self._is_stop_flagged() or self._stop_requested.is_set():
                    self.logger.info(
                        "Stop flag/request detected after delay, aborting restart"
                    )
                    break
                
                try:
                    self.logger.info("Attempting to restart...")
                    self.start(_from_watcher=True)
                except Exception as e:
                    self.logger.error(f"Failed to restart: {e}")
            break

    def is_running(self):
        """Check if process is running."""
        return self.process and self.process.poll() is None


class Manager:
    """Manages services (unified, no platform distinction)."""
    
    def __init__(self, config_path=CONFIG_FILE):
        self.config_path = Path(config_path)
        self.run_dir = None
        self.logger = None
        self._load_config()
        self.services = []
        self.services_map = {}

    def _load_config(self):
        """Load configuration from YAML or JSON file."""
        try:
            global CONFIG_FILE
            CONFIG_FILE = self.config_path
            config_dir = self.config_path.resolve().parent
            cfg = _load_file(self.config_path)
            self.services_cfg = cfg.get('services', [])
            run_dir_raw = cfg.get('run_dir', None)
            # resolve relative run_dir
            if run_dir_raw:
                self.run_dir = _resolve_path(run_dir_raw, config_dir)
            if self.run_dir:
                global LOGS_DIR
                LOGS_DIR = Path(self.run_dir) / "logs"
            # resolve relative cmd paths in services
            for svc in self.services_cfg:
                if 'cmd' in svc:
                    svc['cmd'] = _resolve_path(svc['cmd'], config_dir)
            self.logger = setup_logger('Manager', str(LOGS_DIR / 'manager.log'))
            self.logger.info(f"Loaded config from {self.config_path}")
        except Exception as e:
            if self.logger:
                self.logger.error(f"Failed to load config: {e}")
            raise

    def setup(self):
        """Initialize service objects."""
        self.services = []
        self.services_map = {}
        for s in self.services_cfg:
            sp = ServiceProcess(
                s.get('name'),
                s['cmd'],
                s.get('args', []),
                s.get('restart_on_exit', True)
            )
            self.services.append(sp)
            self.services_map[sp.name] = sp
        self.logger.info(f"Initialized {len(self.services)} services")

    def _get_start_levels(self):
        """Return ordered start levels based on dependency graph."""
        try:
            return topological_sort(self.services_cfg)
        except Exception as e:
            self.logger.error(f"Dependency graph error: {e}")
            # Fallback: all services in one level
            return [[s.get('name') for s in self.services_cfg]]

    def start_all(self):
        """Start all services in dependency order (topological levels)."""
        self.logger.info("=" * 60)
        self.logger.info("Starting all services")
        self.logger.info("=" * 60)
        levels = self._get_start_levels()
        for idx, level in enumerate(levels):
            self.logger.info(f"Starting level {idx + 1}/{len(levels)}: {', '.join(level)}")
            for name in level:
                svc = self.services_map.get(name)
                if svc:
                    svc.start()
            # Small delay between levels to allow dependencies to come up
            time.sleep(1)

        self.logger.info("All services started")

    def stop_all(self):
        """Stop all services in reverse dependency order."""
        self.logger.info("=" * 60)
        self.logger.info("Stopping all services")
        self.logger.info("=" * 60)

        # First, stop all per-service daemon managers to prevent auto-restart
        # while we are killing service processes
        for svc in self.services:
            daemon_pidfile = LOGS_DIR / f'manager-{svc.name}.pid'
            if daemon_pidfile.exists():
                self.logger.info(f"Stopping daemon manager for {svc.name}")
                _stop_manager_daemon(daemon_pidfile, self.logger)

        levels = self._get_start_levels()
        # Stop in reverse dependency order
        for idx, level in enumerate(reversed(levels)):
            self.logger.info(f"Stopping level {len(levels) - idx}/{len(levels)}: {', '.join(level)}")
            for name in level:
                svc = self.services_map.get(name)
                if svc:
                    svc.stop()

        self.logger.info("All stopped")

    def _get_service(self, name: str):
        return self.services_map.get(name)

    def start_service(self, name: str):
        """Start only a single service by name."""
        svc = self._get_service(name)
        if not svc:
            raise ValueError(f"Unknown service: {name}")
        self.logger.info("=" * 60)
        self.logger.info(f"Starting service: {name}")
        self.logger.info("=" * 60)
        svc.start()

    def stop_service(self, name: str):
        """Stop only a single service by name."""
        svc = self._get_service(name)
        if not svc:
            raise ValueError(f"Unknown service: {name}")
        self.logger.info("=" * 60)
        self.logger.info(f"Stopping service: {name}")
        self.logger.info("=" * 60)
        svc.stop()

    def restart_service(self, name: str):
        """Restart only a single service."""
        self.stop_service(name)
        time.sleep(1)
        self.start_service(name)

    def status(self):
        """Print status of all services."""
        self.logger.info("Checking status...")
        print("\n" + "=" * 60)
        print("Service Status")
        print("=" * 60)
        
        for s in self.services:
            status = 'RUNNING' if s.is_running() else 'STOPPED'
            print(f"{s.name:12s}: {status:10s} (restarts: {s.restart_count})")
        
        print("=" * 60 + "\n")

    def restart_all(self):
        """Restart all services."""
        self.logger.info("Restarting all...")
        self.stop_all()
        time.sleep(1)
        self.start_all()


def _write_manager_pid(pidfile: Path):
    try:
        pidfile.parent.mkdir(parents=True, exist_ok=True)
        with open(pidfile, 'w') as f:
            f.write(str(os.getpid()))
    except Exception:
        pass


def _remove_manager_pid(pidfile: Path):
    try:
        if pidfile.exists():
            pidfile.unlink()
    except Exception:
        pass


def _stop_manager_daemon(pidfile: Path, logger: logging.Logger, timeout: int = 5):
    """Stop a daemonized manager process recorded in pidfile (best-effort).

    Sends SIGTERM to the manager's process group so its watcher threads
    cannot auto-restart services after the manager exits.
    """
    try:
        if not pidfile.exists():
            return
        pid_str = pidfile.read_text().strip()
        if not pid_str.isdigit():
            _remove_manager_pid(pidfile)
            return
        pid = int(pid_str)

        # Avoid killing ourselves
        if pid == os.getpid():
            return

        # Check if process still exists
        try:
            os.kill(pid, 0)
        except ProcessLookupError:
            logger.info("Manager daemon already exited")
            _remove_manager_pid(pidfile)
            return

        logger.info(f"Stopping manager daemon pid={pid} (pidfile={pidfile})")

        # Try to SIGTERM the entire process group first,
        # but ONLY if it's not our own process group (safety check)
        try:
            pgid = os.getpgid(pid)
            my_pgid = os.getpgid(os.getpid())
            if pgid != my_pgid:
                os.killpg(pgid, signal.SIGTERM)
                logger.debug(f"Sent SIGTERM to manager daemon process group {pgid}")
            else:
                # Same process group — only kill the specific PID to avoid self-kill
                logger.debug(f"Manager daemon {pid} shares our process group, sending SIGTERM to PID only")
                os.kill(pid, signal.SIGTERM)
        except Exception as e:
            logger.debug(f"Failed to kill manager daemon process group: {e}, trying single process")
            try:
                os.kill(pid, signal.SIGTERM)
            except ProcessLookupError:
                logger.info("Manager daemon already exited")
                _remove_manager_pid(pidfile)
                return

        # Wait a bit for it to exit
        start = time.time()
        while time.time() - start < timeout:
            try:
                os.kill(pid, 0)
            except ProcessLookupError:
                break
            time.sleep(0.2)

        # If still alive, SIGKILL
        try:
            os.kill(pid, 0)
            logger.warning("Manager daemon did not exit, sending SIGKILL")
            try:
                pgid = os.getpgid(pid)
                my_pgid = os.getpgid(os.getpid())
                if pgid != my_pgid:
                    os.killpg(pgid, signal.SIGKILL)
                else:
                    os.kill(pid, signal.SIGKILL)
            except Exception:
                os.kill(pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
        finally:
            _remove_manager_pid(pidfile)
    except Exception as e:
        logger.debug(f"Failed to stop manager daemon for {pidfile}: {e}")


# ---------- Scheduled restart (cron-like) ----------

def _parse_cron(cron_str: str):
    """Parse cron string like 'HH:MM' or 'HH:MM@0,1,3' (weekdays 0=Mon..6=Sun)."""
    if not cron_str:
        return None
    try:
        parts = cron_str.split('@')
        time_part = parts[0].strip()
        h, m = int(time_part.split(':')[0]), int(time_part.split(':')[1])
        if not (0 <= h <= 23 and 0 <= m <= 59):
            return None
        weekdays = None
        if len(parts) > 1 and parts[1].strip():
            weekdays = [int(d) for d in parts[1].strip().split(',') if d.strip().isdigit()]
            weekdays = [d for d in weekdays if 0 <= d <= 6]
            if not weekdays:
                weekdays = None
        return {"hour": h, "minute": m, "weekdays": weekdays}
    except Exception:
        return None


def _should_restart_now(sr: dict, now: datetime) -> bool:
    """Check if scheduled restart should trigger at the given moment."""
    parsed = _parse_cron(sr.get("cron", ""))
    if not parsed:
        return False
    if now.hour != parsed["hour"] or now.minute != parsed["minute"]:
        return False
    weekdays = parsed.get("weekdays")
    if weekdays is not None and now.weekday() not in weekdays:
        return False
    last = sr.get("last_restart")
    if last:
        try:
            last_dt = datetime.fromisoformat(last)
            if (now - last_dt).total_seconds() < 120:
                return False
        except Exception:
            pass
    return True


def _append_audit_entry(audit_file: Path, entry: dict):
    """Append an audit log entry (lightweight, no backend dependency)."""
    try:
        entries = []
        if audit_file.exists():
            try:
                entries = json.loads(audit_file.read_text(encoding="utf-8"))
            except Exception:
                entries = []
        entries.append(entry)
        # keep last 5000 entries
        if len(entries) > 5000:
            entries = entries[-5000:]
        audit_file.write_text(json.dumps(entries, ensure_ascii=False, indent=None), encoding="utf-8")
    except Exception:
        pass


def _scheduled_restart_check(mgr: Manager):
    """Single check: iterate services and restart those whose cron matches now."""
    try:
        config_path = mgr.config_path
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f) or {}
    except Exception as e:
        mgr.logger.warning(f"Scheduled restart: failed to load config: {e}")
        return

    now = datetime.now()
    changed = False
    audit_file = LOGS_DIR / 'audit.json'

    for svc_cfg in config.get('services', []):
        sr = svc_cfg.get('scheduled_restart')
        if not sr or not sr.get("enabled") or not sr.get("cron"):
            continue
        svc_name = svc_cfg.get("name", "unknown")
        if _should_restart_now(sr, now):
            mgr.logger.info(f"Scheduled restart triggered for {svc_name}")
            try:
                svc = mgr.services_map.get(svc_name)
                if svc:
                    svc.stop()
                    time.sleep(1)
                    svc.start()
                    mgr.logger.info(f"Scheduled restart completed for {svc_name}")
                    _append_audit_entry(audit_file, {
                        "timestamp": now.isoformat(),
                        "user": "system", "role": "system",
                        "action": "restart", "target": svc_name,
                        "detail": "scheduled restart", "result": "success",
                    })
                else:
                    mgr.logger.warning(f"Scheduled restart: service '{svc_name}' not found in manager")
            except Exception as e:
                mgr.logger.error(f"Scheduled restart failed for {svc_name}: {e}")
                _append_audit_entry(audit_file, {
                    "timestamp": now.isoformat(),
                    "user": "system", "role": "system",
                    "action": "restart", "target": svc_name,
                    "detail": f"scheduled restart failed: {e}", "result": "failed",
                })
            sr["last_restart"] = now.isoformat()
            changed = True

    if changed:
        try:
            with open(config_path, 'w', encoding='utf-8') as f:
                yaml.dump(config, f, default_flow_style=False, allow_unicode=True, sort_keys=False)
        except Exception as e:
            mgr.logger.warning(f"Scheduled restart: failed to save config: {e}")


def _start_scheduled_restart_thread(mgr: Manager):
    """Launch a daemon thread that checks scheduled restarts every 30 seconds."""
    def _loop():
        mgr.logger.info("Scheduled restart checker thread started")
        while True:
            time.sleep(30)
            try:
                _scheduled_restart_check(mgr)
            except Exception as e:
                mgr.logger.error(f"Scheduled restart check error: {e}")
    t = threading.Thread(target=_loop, daemon=True, name="scheduled-restart")
    t.start()
    return t


def run_monitor_forever(mgr: Manager, scope_label: str, pidfile: Path):
    """Keep the process alive so ServiceProcess watcher threads can perform auto-restart."""
    mgr.logger.info(f"Entering monitor loop (scope={scope_label})")
    _write_manager_pid(pidfile)
    # Start scheduled restart checker only for full-scope monitors
    if scope_label == 'all':
        _start_scheduled_restart_thread(mgr)
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        mgr.logger.info("Monitor interrupted (KeyboardInterrupt)")
    finally:
        _remove_manager_pid(pidfile)


def main():
    parser = argparse.ArgumentParser(
    description='Manage services with auto-restart and logging'
    )
    parser.add_argument(
        'action',
        choices=['start', 'stop', 'status', 'restart'],
        help='Action to perform'
    )
    parser.add_argument(
        '--service',
        default=None,
        help='Operate on a single service (e.g. service_A). If omitted, operates on all services.'
    )
    parser.add_argument(
        '--daemon',
        action='store_true',
        help='Keep manager running to monitor (auto-restart) after start/restart for scoped operations.'
    )
    parser.add_argument(
        '--config',
        default=str(CONFIG_FILE),
        help=f'Config file path (default: {CONFIG_FILE})'
    )
    args = parser.parse_args()
    
    try:
        mgr = Manager(args.config)
        mgr.setup()

        if args.action == 'status':
            mgr.status()
            return

        if args.service:
            if args.action == 'start':
                # Stop old daemon manager first to prevent it from interfering
                _stop_manager_daemon(LOGS_DIR / f'manager-{args.service}.pid', mgr.logger)
                mgr.start_service(args.service)
                if args.daemon:
                    run_monitor_forever(mgr, f'service:{args.service}', LOGS_DIR / f'manager-{args.service}.pid')
            elif args.action == 'stop':
                # IMPORTANT: stop daemon manager FIRST to prevent its watcher
                # from auto-restarting the service after we kill it
                _stop_manager_daemon(LOGS_DIR / f'manager-{args.service}.pid', mgr.logger)
                # then stop the service process itself
                mgr.stop_service(args.service)
            elif args.action == 'restart':
                # Stop old daemon manager first
                _stop_manager_daemon(LOGS_DIR / f'manager-{args.service}.pid', mgr.logger)
                mgr.restart_service(args.service)
                if args.daemon:
                    run_monitor_forever(mgr, f'service:{args.service}', LOGS_DIR / f'manager-{args.service}.pid')
            return

        # Default: operate on all
        if args.action == 'start':
            # Stop old global daemon manager if exists
            _stop_manager_daemon(LOGS_DIR / 'manager-all.pid', mgr.logger)
            mgr.start_all()
            print(f"\nServices started. Check logs in: {LOGS_DIR}/")
            if args.daemon:
                run_monitor_forever(mgr, 'all', LOGS_DIR / 'manager-all.pid')
            else:
                # Keep running to monitor services (foreground mode)
                try:
                    _write_manager_pid(LOGS_DIR / 'manager-all.pid')
                    _start_scheduled_restart_thread(mgr)
                    while True:
                        time.sleep(1)
                except KeyboardInterrupt:
                    print("\nInterrupt received, stopping...")
                    mgr.stop_all()
                finally:
                    _remove_manager_pid(LOGS_DIR / 'manager-all.pid')
        elif args.action == 'stop':
            # Stop global daemon manager FIRST
            _stop_manager_daemon(LOGS_DIR / 'manager-all.pid', mgr.logger)
            mgr.stop_all()
        elif args.action == 'restart':
            _stop_manager_daemon(LOGS_DIR / 'manager-all.pid', mgr.logger)
            mgr.restart_all()
            if args.daemon:
                run_monitor_forever(mgr, 'all', LOGS_DIR / 'manager-all.pid')
    except Exception as e:
        import traceback
        tb = traceback.extract_tb(e.__traceback__)
        for frame in tb:
            print(f'ERROR: {e} FILENAME: {frame.filename} LINENO: {frame.lineno} FUNCTIONNAME: {frame.name} ')

        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
