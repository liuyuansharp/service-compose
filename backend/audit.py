"""Audit log read/write."""

import json
import threading
from datetime import datetime
from typing import Dict, List, Optional, Tuple

from .config import AUDIT_LOG_FILE, AUDIT_LOG_MAX_ENTRIES, logger

_audit_lock = threading.Lock()


def append_audit_log(user: str, role: str, action: str, target: str = "", detail: str = "", result: str = "success"):
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
            if len(entries) > AUDIT_LOG_MAX_ENTRIES:
                entries = entries[-AUDIT_LOG_MAX_ENTRIES:]
            AUDIT_LOG_FILE.write_text(json.dumps(entries, ensure_ascii=False, indent=None), encoding="utf-8")
    except Exception as exc:
        logger.warning(f"Failed to write audit log: {exc}")


def read_audit_logs(limit: int = 200, offset: int = 0, username: Optional[str] = None) -> Tuple[List[Dict], int]:
    if not AUDIT_LOG_FILE.exists():
        return [], 0
    try:
        entries = json.loads(AUDIT_LOG_FILE.read_text(encoding="utf-8"))
    except Exception:
        return [], 0
    if username:
        entries = [e for e in entries if e.get("user") == username]
    total = len(entries)
    entries = list(reversed(entries))
    entries = entries[offset:offset + limit]
    return entries, total
