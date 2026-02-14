"""Scheduled restart helpers — cron parsing and next-restart calculation.

The actual scheduled restart execution loop now lives in backend/service_compose.py.
This module only provides utility functions needed by the backend API to parse
cron expressions and compute the next scheduled restart time for display.
"""

from datetime import datetime, timedelta
from typing import Dict, Optional


def _parse_cron(cron_str: str) -> Optional[Dict]:
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


def _calc_next_restart(sr_cfg: Dict) -> Optional[str]:
    """Calculate the next scheduled restart ISO timestamp."""
    if not sr_cfg.get("enabled") or not sr_cfg.get("cron"):
        return None
    parsed = _parse_cron(sr_cfg["cron"])
    if not parsed:
        return None
    now = datetime.now()
    target_today = now.replace(hour=parsed["hour"], minute=parsed["minute"], second=0, microsecond=0)
    weekdays = parsed.get("weekdays")
    for day_offset in range(8):
        candidate = target_today + timedelta(days=day_offset)
        if day_offset == 0 and candidate <= now:
            continue
        if weekdays is not None and candidate.weekday() not in weekdays:
            continue
        return candidate.isoformat()
    return None
