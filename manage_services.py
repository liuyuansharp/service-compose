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

from backend.config import topological_sort

ROOT = Path(__file__).resolve().parent
CONFIG_PATH = ROOT / 'services_config.json'
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


class ServiceProcess:
    """Manages a single service process with auto-restart, logging, and pid tracking."""
    
    # Exponential backoff: 1s, 2s, 4s, 8s, 16s, 32s, then cap at 60s
    RESTART_DELAYS = [1, 2, 4, 8, 16, 32, 60]
    MAX_RESTART_ATTEMPTS_PER_MINUTE = 5  # Prevent restart storms
    
    def __init__(self, name, cmd, args, log, pidfile, restart_on_exit=True):
        self.name = name
        self.cmd = cmd
        self.args = args or []
        self.log_file = LOGS_DIR / log
        self.pidfile = LOGS_DIR / pidfile
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

    def start(self):
        """Start the service process."""
        with self._lock:
            if self.process and self.process.poll() is None:
                self.logger.info(f"Already running (pid={self.process.pid})")
                return

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
            
            if not self.process:
                self._remove_pidfile()
                self.logger.info("Not running, nothing to stop")
                return
            
            if self.process.poll() is not None:
                self._remove_pidfile()
                self.logger.info("Already stopped")
                return
            
            self.logger.info(f"Stopping (pid={self.process.pid}), timeout={timeout}s")
            
            try:
                # Terminate the whole process group
                try:
                    os.killpg(os.getpgid(self.process.pid), signal.SIGTERM)
                    self.logger.debug("Sent SIGTERM to process group")
                except Exception as e:
                    self.logger.debug(f"Failed to kill process group: {e}, trying single process")
                    self.process.terminate()
                
                try:
                    self.process.wait(timeout=timeout)
                    self.logger.info("Process terminated gracefully")
                except subprocess.TimeoutExpired:
                    self.logger.warning(f"Process did not exit after {timeout}s, killing")
                    try:
                        os.killpg(os.getpgid(self.process.pid), signal.SIGKILL)
                    except Exception:
                        self.process.kill()
                    self.process.wait()
                    self.logger.info("Process killed")
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
                
                try:
                    self.logger.info("Attempting to restart...")
                    self.start()
                except Exception as e:
                    self.logger.error(f"Failed to restart: {e}")
            break

    def is_running(self):
        """Check if process is running."""
        return self.process and self.process.poll() is None


class Manager:
    """Manages services (unified, no platform distinction)."""
    
    def __init__(self, config_path=CONFIG_PATH):
        self.config_path = Path(config_path)
        self.logger = setup_logger('Manager', str(LOGS_DIR / 'manager.log'))
        self._load_config()
        self.services = []
        self.services_map = {}

    def _load_config(self):
        """Load configuration from JSON file."""
        try:
            with open(self.config_path) as f:
                cfg = json.load(f)
            self.services_cfg = cfg.get('services', [])
            self.logger.info(f"Loaded config from {self.config_path}")
        except Exception as e:
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
                s.get('log'),
                s.get('pidfile'),
                s.get('restart_on_exit', True)
            )
            self.services.append(sp)
            self.services_map[sp.name] = sp
        self.logger.info(f"Initialized {len(self.services)} services")

    def _get_start_levels(self):
        """Return ordered start levels based on dependency graph."""
        try:
            return topological_sort({"services": self.services_cfg})
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
    """Stop a daemonized manager process recorded in pidfile (best-effort)."""
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

        logger.info(f"Stopping manager daemon pid={pid} (pidfile={pidfile})")
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
            os.kill(pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
        finally:
            _remove_manager_pid(pidfile)
    except Exception as e:
        logger.debug(f"Failed to stop manager daemon for {pidfile}: {e}")


def run_monitor_forever(mgr: Manager, scope_label: str, pidfile: Path):
    """Keep the process alive so ServiceProcess watcher threads can perform auto-restart."""
    mgr.logger.info(f"Entering monitor loop (scope={scope_label})")
    _write_manager_pid(pidfile)
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
        default=str(CONFIG_PATH),
        help=f'Config file path (default: {CONFIG_PATH})'
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
                mgr.start_service(args.service)
                if args.daemon:
                    run_monitor_forever(mgr, f'service:{args.service}', LOGS_DIR / f'manager-{args.service}.pid')
            elif args.action == 'stop':
                # stop service itself
                mgr.stop_service(args.service)
                # also stop daemonized service manager if exists
                _stop_manager_daemon(LOGS_DIR / f'manager-{args.service}.pid', mgr.logger)
            elif args.action == 'restart':
                mgr.restart_service(args.service)
                if args.daemon:
                    run_monitor_forever(mgr, f'service:{args.service}', LOGS_DIR / f'manager-{args.service}.pid')
            return

        # Default: operate on all
        if args.action == 'start':
            mgr.start_all()
            print(f"\nServices started. Check logs in: {LOGS_DIR}/")
            # Keep running to monitor services
            try:
                while True:
                    time.sleep(1)
            except KeyboardInterrupt:
                print("\nInterrupt received, stopping...")
                mgr.stop_all()
        elif args.action == 'stop':
            mgr.stop_all()
        elif args.action == 'restart':
            mgr.restart_all()
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
