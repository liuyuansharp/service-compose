"""Scheduled restart logic — cron parsing, checking, execution."""

import subprocess
import sys
from datetime import datetime, timedelta
from typing import Dict, Optional

from .config import SERVICE_DIR, load_config, save_config, logger
from .audit import append_audit_log


def _parse_cron(cron_str: str) -> Optional[Dict]:
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


def _should_restart_now(sr: Dict, now: datetime) -> bool:
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


def _do_scheduled_restart(service_name: str):
    cmd = [sys.executable, str(SERVICE_DIR / 'manage_services.py'), 'restart',
           '--service', service_name, '--daemon']
    try:
        subprocess.Popen(cmd, cwd=str(SERVICE_DIR), stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        append_audit_log(user="system", role="system", action="restart", target=service_name, detail="scheduled restart")
    except Exception as e:
        logger.error(f"Scheduled restart failed for {service_name}: {e}")
        append_audit_log(user="system", role="system", action="restart", target=service_name, detail=f"scheduled restart failed: {e}", result="failed")


async def scheduled_restart_loop():
    """Background loop: every 30s check if any service needs scheduled restart."""
    import asyncio
    logger.info("Scheduled restart checker started")
    while True:
        await asyncio.sleep(30)
        try:
            config = load_config()
            now = datetime.now()
            changed = False
            for svc in config.get('services', []):
                sr = svc.get('scheduled_restart')
                if sr and sr.get("enabled") and sr.get("cron"):
                    if _should_restart_now(sr, now):
                        svc_name = svc.get("name", "unknown")
                        logger.info(f"Scheduled restart triggered for {svc_name}")
                        _do_scheduled_restart(svc_name)
                        sr["last_restart"] = now.isoformat()
                        changed = True
            if changed:
                save_config(config)
        except Exception as e:
            logger.error(f"Scheduled restart check error: {e}")
