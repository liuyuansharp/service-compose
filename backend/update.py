"""Update / rollback / backup helpers."""

import hashlib
import json
import shutil
import tarfile
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Tuple

from .config import RUN_DIR, CONFIG_FILE, logger
from .models import BackupInfo


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
    for path in (RUN_DIR / "deployments").glob(f"{prefix}*"):
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
    deployments_dir = RUN_DIR / "deployments"
    for backup in backups[keep:]:
        path = deployments_dir / backup.name
        if path.exists():
            shutil.rmtree(path, ignore_errors=True)


def _safe_extract_tar(tar: tarfile.TarFile, dest: Path):
    for member in tar.getmembers():
        member_path = (dest / member.name).resolve()
        if not str(member_path).startswith(str(dest.resolve())):
            raise ValueError("Invalid tar entry path")
    tar.extractall(dest)


def _run_restart(service: str):
    import sys
    import subprocess
    cmd = [f"{RUN_DIR}/manage_services", 'restart', "--config", f"{CONFIG_FILE}",
           '--service', service, '--daemon']
    result = subprocess.run(cmd, cwd=str(RUN_DIR), capture_output=True, text=True, timeout=60)
    if result.returncode != 0:
        raise RuntimeError(result.stderr or result.stdout or 'Restart failed')


def rollback_to_backup(service: str, backup_name: str):
    deployments_dir = RUN_DIR / "deployments"
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


def perform_update(task_id: str, service: str, file_path: Path, update_tasks: Dict):
    task = update_tasks.get(task_id)
    if not task:
        return
    task["status"] = "extracting"
    task["update_progress"] = 5
    task["message"] = "Extracting package"
    package_hash = compute_sha256(file_path)
    task["package_hash"] = package_hash
    extract_root = RUN_DIR / "updates" / f"{service}-{task_id}"
    if extract_root.exists():
        shutil.rmtree(extract_root, ignore_errors=True)
    extract_root.mkdir(parents=True, exist_ok=True)
    with tarfile.open(file_path, "r:gz") as tar:
        _safe_extract_tar(tar, extract_root)
    entries = [p for p in extract_root.iterdir() if p.name not in ('__MACOSX',)]
    source_dir = entries[0] if len(entries) == 1 and entries[0].is_dir() else extract_root
    manifest = read_manifest(source_dir)
    if not manifest:
        raise RuntimeError("manifest.json missing in package")
    incoming_version = manifest.get("version")
    incoming_hash = manifest.get("package_hash")
    if incoming_hash and incoming_hash != package_hash:
        raise RuntimeError("package hash mismatch")
    current_manifest = read_manifest(RUN_DIR / "deployments" / service)
    current_version = current_manifest.get("version") if current_manifest else None
    if incoming_version and current_version and not is_newer_version(current_version, incoming_version):
        raise RuntimeError("incoming version is not newer")
    task["update_progress"] = 35
    task["status"] = "validating"
    task["message"] = "Validation complete"
    target_dir = RUN_DIR / "deployments" / service
    target_dir.parent.mkdir(parents=True, exist_ok=True)
    backup_dir = None
    if target_dir.exists():
        backup_dir = RUN_DIR / "deployments" / f"{service}_backup_{datetime.now().strftime('%Y%m%d%H%M%S')}"
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
