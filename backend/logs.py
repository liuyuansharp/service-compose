"""Log reading, rotation, and maintenance utilities."""

import json
import shutil
from collections import deque
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from .config import (
    LOGS_DIR, LOG_INDEX_STRIDE, LOG_INDEX_CACHE, logger,
    MAX_LOG_BYTES, MAX_LOG_BACKUPS, MAX_TOTAL_LOG_BYTES,
)
from .services import extract_log_level


# ---------- Log chain ----------

def get_log_chain(service: str) -> List[Path]:
    base = LOGS_DIR / f"{service}.log"
    chain = []
    backups = []
    for f in LOGS_DIR.iterdir():
        name = f.name
        prefix = f"{service}.log."
        if name.startswith(prefix) and not name.endswith('.idx'):
            suffix = name[len(prefix):]
            if suffix.isdigit():
                backups.append((int(suffix), f))
    backups.sort(key=lambda x: x[0], reverse=True)
    for _, f in backups:
        if f.exists():
            chain.append(f)
    if base.exists():
        chain.append(base)
    return chain


# ---------- Index ----------

def load_log_index(log_file: Path) -> Dict:
    key = str(log_file)
    try:
        stat = log_file.stat()
    except Exception:
        return {"stride": LOG_INDEX_STRIDE, "offsets": [0], "total_lines": 0, "size": 0, "mtime": 0}
    cached = LOG_INDEX_CACHE.get(key)
    if cached and cached.get("mtime") == stat.st_mtime and cached.get("size") == stat.st_size:
        return cached
    idx_path = log_file.with_suffix(log_file.suffix + ".idx")
    if idx_path.exists():
        try:
            data = json.loads(idx_path.read_text(encoding="utf-8"))
            if data.get("mtime") == stat.st_mtime and data.get("size") == stat.st_size and data.get("stride") == LOG_INDEX_STRIDE:
                LOG_INDEX_CACHE[key] = data
                return data
        except Exception:
            pass
    offsets = [0]
    total_lines = 0
    with open(log_file, "rb") as f:
        while True:
            line = f.readline()
            if not line:
                break
            total_lines += 1
            if total_lines % LOG_INDEX_STRIDE == 0:
                offsets.append(f.tell())
    data = {
        "stride": LOG_INDEX_STRIDE,
        "offsets": offsets,
        "total_lines": total_lines,
        "size": stat.st_size,
        "mtime": stat.st_mtime,
    }
    try:
        idx_path.write_text(json.dumps(data), encoding="utf-8")
    except Exception:
        pass
    LOG_INDEX_CACHE[key] = data
    return data


# ---------- Chained read ----------

def get_chained_total_lines(chain: List[Path]) -> Tuple[int, List[Tuple[Path, int]]]:
    total = 0
    file_lines = []
    for f in chain:
        idx = load_log_index(f)
        n = idx.get("total_lines", 0)
        file_lines.append((f, n))
        total += n
    return total, file_lines


def read_log_lines(log_file: Path, start_line: int, max_lines: int) -> Tuple[List[Tuple[int, str]], int]:
    index = load_log_index(log_file)
    total_lines = index.get("total_lines", 0)
    if total_lines <= 0:
        return [], 0
    if start_line < 0:
        start_line = max(total_lines + start_line, 0)
    start_line = min(start_line, total_lines)
    stride = index.get("stride", LOG_INDEX_STRIDE)
    offsets = index.get("offsets", [0])
    bucket = start_line // stride
    byte_offset = offsets[bucket] if bucket < len(offsets) else 0
    current_line = bucket * stride
    results: List[Tuple[int, str]] = []
    with open(log_file, "rb") as f:
        f.seek(byte_offset)
        while current_line < start_line:
            line = f.readline()
            if not line:
                break
            current_line += 1
        while len(results) < max_lines:
            line = f.readline()
            if not line:
                break
            results.append((current_line, line.decode("utf-8", errors="ignore")))
            current_line += 1
    return results, total_lines


def read_chained_log_lines(chain: List[Path], start_line: int, max_lines: int) -> Tuple[List[Tuple[int, str]], int]:
    total_lines, file_lines = get_chained_total_lines(chain)
    if total_lines <= 0:
        return [], 0
    if start_line < 0:
        start_line = max(total_lines + start_line, 0)
    start_line = min(start_line, total_lines)
    results: List[Tuple[int, str]] = []
    cumulative = 0
    for fpath, flines in file_lines:
        if len(results) >= max_lines:
            break
        file_end = cumulative + flines
        if file_end <= start_line:
            cumulative = file_end
            continue
        local_start = max(start_line - cumulative, 0)
        remaining = max_lines - len(results)
        file_results, _ = read_log_lines(fpath, local_start, remaining)
        for local_idx, line in file_results:
            results.append((cumulative + local_idx, line))
        cumulative = file_end
    return results[:max_lines], total_lines


# ---------- Rotation / Maintenance ----------

def rotate_log_if_needed(log_file: Path):
    try:
        if not log_file.exists():
            return
        base = log_file.name
        backups = sorted(
            [f for f in log_file.parent.iterdir()
             if f.name.startswith(base + ".") and f.name[len(base)+1:].isdigit()],
            key=lambda p: int(p.name[len(base)+1:])
        )
        for old in backups[MAX_LOG_BACKUPS:]:
            old.unlink(missing_ok=True)
        if log_file.stat().st_size > MAX_LOG_BYTES:
            for i in range(MAX_LOG_BACKUPS, 0, -1):
                src = log_file.parent / f"{base}.{i}"
                dst = log_file.parent / f"{base}.{i + 1}"
                if src.exists():
                    if i >= MAX_LOG_BACKUPS:
                        src.unlink(missing_ok=True)
                    else:
                        shutil.move(str(src), str(dst))
            shutil.move(str(log_file), str(log_file.parent / f"{base}.1"))
            log_file.touch()
            LOG_INDEX_CACHE.pop(str(log_file), None)
    except Exception as exc:
        logger.warning(f"Log rotate failed for {log_file}: {exc}")


def enforce_total_log_size():
    try:
        all_log_files = sorted(
            [f for f in LOGS_DIR.iterdir() if f.is_file() and '.log' in f.name and not f.name.endswith('.idx')],
            key=lambda p: p.stat().st_mtime
        )
        total = sum(f.stat().st_size for f in all_log_files)
        if total <= MAX_TOTAL_LOG_BYTES:
            return
        logger.info(f"Total log size {total // (1024*1024)}MB exceeds limit, cleaning up...")
        for f in all_log_files:
            if total <= MAX_TOTAL_LOG_BYTES:
                break
            if f.suffix.lstrip('.').isdigit() or (f.name.count('.') >= 2 and f.name.split('.')[-1].isdigit()):
                fsize = f.stat().st_size
                f.unlink(missing_ok=True)
                base_log = f.parent / f.name.rsplit('.', 1)[0]
                LOG_INDEX_CACHE.pop(str(base_log), None)
                total -= fsize
    except Exception as exc:
        logger.warning(f"Total log size enforcement error: {exc}")
