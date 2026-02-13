from contextlib import asynccontextmanager
from datetime import datetime, timedelta
from typing import Dict, List, Optional

import asyncio
import json
import sys
import uuid

from . import config as _config

if "--config" in sys.argv:
    try:
        config_index = sys.argv.index("--config")
        if config_index + 1 < len(sys.argv):
            _config.update_run_dir(sys.argv[config_index + 1])
            _config.logger.info(f"Using services config: {sys.argv[config_index + 1]}")
    except Exception:
        pass

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, Query, Depends, UploadFile, File, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles

from .config import (
    RUN_DIR, LOGS_DIR, logger,
    load_config, save_config, get_all_services,
    METRICS_HISTORY, MAX_METRICS_HISTORY_POINTS,
    UPDATE_TASKS, update_run_dir, CONFIG_FILE
)
from .auth import (
    init_auth_db, authenticate_user, create_access_token, decode_token,
    get_current_user, get_user_from_request,
    require_admin, require_operator, VALID_ROLES,
    SessionLocal, User,
)
from .models import (
    PlatformStatus, DashboardStatus,
    ServiceControl, BatchServiceControl,
    DiskPartitionInfo,
    LoginRequest, LoginResponse, UserProfile,
    UserCreateRequest, UserUpdateRequest,
    ScheduledRestartRequest,
    UpdateTaskResponse, UpdateProgress,
    BackupInfo,
)
from .services import (
    get_service_status, get_system_metrics, get_disk_partitions,
    get_service_info, build_process_tree,
)
from .logs import (
    get_log_chain, read_chained_log_lines, rotate_log_if_needed,
)
from .tasks import metrics_sampler, system_metrics_persist_loop, log_maintenance, load_system_metrics_history
from .scheduled import scheduled_restart_loop, _parse_cron, _calc_next_restart
from .audit import append_audit_log, read_audit_logs
from .update import list_backups, rollback_to_backup, perform_update
from .services import extract_log_level
from .config import build_dependency_graph, get_reverse_dependents


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_auth_db()
    asyncio.create_task(metrics_sampler())
    asyncio.create_task(system_metrics_persist_loop())
    asyncio.create_task(log_maintenance())
    asyncio.create_task(scheduled_restart_loop())
    yield


app = FastAPI(
    title="Service Manager Dashboard API",
    description="Unified service monitoring and control API",
    version="2.0.0",
    docs_url="/api/docs",
    openapi_url="/api/openapi.json",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.post("/api/login", response_model=LoginResponse)
async def login(login_data: LoginRequest):
    user = authenticate_user(login_data.username, login_data.password)
    if not user:
        append_audit_log(user=login_data.username, role="unknown", action="login", result="failed", detail="invalid credentials")
        raise HTTPException(status_code=401, detail="Incorrect username or password")
    token = create_access_token({"sub": user["username"]})
    append_audit_log(user=user["username"], role=user.get("role", "admin"), action="login")
    return {
        "token": token,
        "user": {
            "username": user["username"],
            "role": user.get("role", "admin"),
            "visible_cards": user.get("visible_cards", []),
            "created_at": user.get("created_at"),
        }
    }


@app.get("/api/me", response_model=UserProfile)
async def get_me(current_user: dict = Depends(get_current_user)):
    return {
        "username": current_user["username"],
        "role": current_user.get("role", "admin"),
        "visible_cards": current_user.get("visible_cards", []),
        "created_at": current_user.get("created_at"),
    }


@app.get("/api/users")
async def list_users(current_user: dict = Depends(get_current_user)):
    require_admin(current_user)
    session = SessionLocal()
    try:
        users = session.query(User).order_by(User.id).all()
        result = []
        for u in users:
            vc = []
            if u.visible_cards:
                try:
                    vc = json.loads(u.visible_cards)
                except Exception:
                    vc = []
            result.append({
                "id": u.id,
                "username": u.username,
                "role": u.role or "admin",
                "visible_cards": vc,
                "created_at": u.created_at.isoformat() if u.created_at else None,
            })
        return result
    finally:
        session.close()


@app.post("/api/users")
async def create_user(req: UserCreateRequest, current_user: dict = Depends(get_current_user)):
    require_admin(current_user)
    if req.role not in VALID_ROLES:
        raise HTTPException(status_code=400, detail=f"Invalid role. Must be one of: {', '.join(VALID_ROLES)}")
    session = SessionLocal()
    try:
        existing = session.query(User).filter(User.username == req.username).first()
        if existing:
            raise HTTPException(status_code=409, detail="Username already exists")
        from .auth import pwd_context
        user = User(
            username=req.username,
            password_hash=pwd_context.hash(req.password),
            role=req.role,
            visible_cards=json.dumps(req.visible_cards) if req.visible_cards else ""
        )
        session.add(user)
        session.commit()
        session.refresh(user)
        append_audit_log(user=current_user["username"], role=current_user.get("role", "admin"), action="create_user", target=req.username, detail=f"role={req.role}")
        return {"status": "success", "id": user.id, "username": user.username}
    finally:
        session.close()


@app.put("/api/users/{user_id}")
async def update_user(user_id: int, req: UserUpdateRequest, current_user: dict = Depends(get_current_user)):
    require_admin(current_user)
    session = SessionLocal()
    try:
        user = session.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        if req.role is not None:
            if req.role not in VALID_ROLES:
                raise HTTPException(status_code=400, detail=f"Invalid role. Must be one of: {', '.join(VALID_ROLES)}")
            if user.role == "admin" and req.role != "admin":
                admin_count = session.query(User).filter(User.role == "admin").count()
                if admin_count <= 1:
                    raise HTTPException(status_code=400, detail="Cannot remove the last admin user")
            user.role = req.role
        if req.password is not None and req.password.strip():
            from .auth import pwd_context
            user.password_hash = pwd_context.hash(req.password)
        if req.visible_cards is not None:
            user.visible_cards = json.dumps(req.visible_cards) if req.visible_cards else ""
        changes = []
        if req.role is not None:
            changes.append(f"role={req.role}")
        if req.password is not None and req.password.strip():
            changes.append("password=***")
        if req.visible_cards is not None:
            changes.append(f"visible_cards={len(req.visible_cards)} items")
        session.commit()
        append_audit_log(user=current_user["username"], role=current_user.get("role", "admin"), action="update_user", target=user.username, detail=", ".join(changes))
        return {"status": "success"}
    finally:
        session.close()


@app.delete("/api/users/{user_id}")
async def delete_user(user_id: int, current_user: dict = Depends(get_current_user)):
    require_admin(current_user)
    session = SessionLocal()
    try:
        user = session.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        if user.username == current_user["username"]:
            raise HTTPException(status_code=400, detail="Cannot delete yourself")
        if user.role == "admin":
            admin_count = session.query(User).filter(User.role == "admin").count()
            if admin_count <= 1:
                raise HTTPException(status_code=400, detail="Cannot delete the last admin user")
        session.delete(user)
        session.commit()
        append_audit_log(user=current_user["username"], role=current_user.get("role", "admin"), action="delete_user", target=user.username)
        return {"status": "success"}
    finally:
        session.close()


@app.get("/api/services")
async def list_services(current_user: dict = Depends(get_current_user)):
    services = get_all_services()
    return {"services": services}


@app.get("/api/services/graph")
async def get_service_graph(current_user: dict = Depends(get_current_user)):
    config = load_config()
    services = get_all_services(config)
    graph = build_dependency_graph(config)
    reverse = get_reverse_dependents(config)
    nodes = [{"id": svc["name"], "label": svc["name"], "depends_on": svc.get("depends_on", [])} for svc in services]
    edges = []
    for name, deps in graph.items():
        for dep in deps:
            edges.append({"from": dep, "to": name})
    return {"nodes": nodes, "edges": edges, "graph": graph, "reverse": reverse}


@app.put("/api/preferences/service-order")
async def put_service_order(request: Request, current_user: dict = Depends(get_current_user)):
    require_operator(current_user)
    body = await request.json()
    order = body.get("order", [])
    if not isinstance(order, list) or not all(isinstance(n, str) for n in order):
        raise HTTPException(status_code=400, detail="order must be a list of service name strings")
    try:
        config = load_config()
        services = config.get("services", [])
        svc_map = {s["name"]: s for s in services}
        reordered = []
        for name in order:
            if name in svc_map:
                reordered.append(svc_map.pop(name))
        for s in svc_map.values():
            reordered.append(s)
        config["services"] = reordered
        save_config(config)
        return {"ok": True, "order": [s["name"] for s in reordered]}
    except Exception as e:
        logger.error(f"Failed to save service order: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.put("/api/scheduled-restart")
async def set_scheduled_restart(req: ScheduledRestartRequest, current_user: dict = Depends(get_current_user)):
    require_operator(current_user)
    if req.enabled and req.cron:
        parsed = _parse_cron(req.cron)
        if not parsed:
            raise HTTPException(status_code=400, detail="Invalid cron format. Use 'HH:MM' or 'HH:MM@0,1,2,3,4'")
    try:
        config = load_config()
        sr_data = {"enabled": req.enabled, "cron": req.cron}
        found = False
        for svc in config.get("services", []):
            if svc.get("name") == req.service:
                old_sr = svc.get("scheduled_restart", {})
                sr_data["last_restart"] = old_sr.get("last_restart")
                svc["scheduled_restart"] = sr_data
                found = True
                break
        if not found:
            raise HTTPException(status_code=404, detail=f"Service '{req.service}' not found")
        save_config(config)
        append_audit_log(
            user=current_user["username"],
            role=current_user.get("role", "admin"),
            action="update_schedule",
            target=req.service,
            detail=f"enabled={req.enabled}, cron={req.cron}" if req.enabled else "disabled",
        )
        next_restart = _calc_next_restart(sr_data) if req.enabled else None
        return {"ok": True, "next_restart": next_restart}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to set scheduled restart: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/status", response_model=PlatformStatus)
async def get_status(current_user: dict = Depends(get_current_user)) -> PlatformStatus:
    try:
        config = load_config()
        services_status = []
        for service_cfg in config.get("services", []):
            service_name = service_cfg.get("name", "unknown")
            pidfile = LOGS_DIR / f"{service_name}.pid"
            logfile = LOGS_DIR / f"{service_name}.log"
            heartbeat = service_cfg.get("heartbeat")
            services_status.append(
                get_service_status(
                    service_name,
                    pidfile,
                    logfile,
                    heartbeat,
                    scheduled_restart_cfg=service_cfg.get("scheduled_restart"),
                    depends_on=service_cfg.get("depends_on", []),
                )
            )

        if any(s.health == "abnormal" for s in services_status):
            overall_status = "abnormal"
        elif any(s.health == "running" for s in services_status):
            overall_status = "running"
        else:
            overall_status = "stopped"

        return PlatformStatus(
            status=overall_status,
            services=services_status,
            timestamp=datetime.now().isoformat()
        )
    except Exception as e:
        logger.error(f"Error getting status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


async def build_dashboard_status() -> DashboardStatus:
    config = load_config()
    services_status = []
    for service_cfg in config.get("services", []):
        service_name = service_cfg.get("name", "unknown")
        pidfile = LOGS_DIR / f"{service_name}.pid"
        logfile = LOGS_DIR / f"{service_name}.log"
        heartbeat = service_cfg.get("heartbeat")
        services_status.append(
            get_service_status(
                service_name,
                pidfile,
                logfile,
                heartbeat,
                scheduled_restart_cfg=service_cfg.get("scheduled_restart"),
                depends_on=service_cfg.get("depends_on", []),
            )
        )
    metrics = get_system_metrics()

    if any(s.health == "abnormal" for s in services_status):
        overall_status = "abnormal"
    elif any(s.health == "running" for s in services_status):
        overall_status = "running"
    else:
        overall_status = "stopped"

    return DashboardStatus(
        status=overall_status,
        services=services_status,
        metrics=metrics,
        timestamp=datetime.now().isoformat()
    )


@app.get("/api/dashboard", response_model=DashboardStatus)
async def get_dashboard_status(current_user: dict = Depends(get_current_user)) -> DashboardStatus:
    return await build_dashboard_status()


@app.get("/api/dashboard/sse")
async def dashboard_sse(request: Request, token: Optional[str] = Query(None)):
    get_user_from_request(request, token)

    async def event_generator():
        while True:
            if await request.is_disconnected():
                break
            try:
                status = await build_dashboard_status()
                yield f"data: {status.model_dump_json()}\n\n"
            except Exception as e:
                logger.error(f"SSE dashboard error: {e}")
                break
            await asyncio.sleep(2)
    return StreamingResponse(event_generator(), media_type="text/event-stream")


_service_locks: Dict[str, asyncio.Lock] = {}
_service_locks_meta_lock = asyncio.Lock()


async def _get_service_lock(service_name: str) -> asyncio.Lock:
    async with _service_locks_meta_lock:
        if service_name not in _service_locks:
            _service_locks[service_name] = asyncio.Lock()
        return _service_locks[service_name]


async def _run_service_command(action: str, service: Optional[str], timeout: float = 30) -> dict:
    cmd = [
        f"{RUN_DIR}/manage_services",
        action,
        f"--config",
        f"{CONFIG_FILE}"
    ]
    if service:
        cmd.extend(['--service', service])
        if action in ("start", "restart"):
            cmd.append('--daemon')
    else:
        if action in ("start", "restart"):
            cmd.append('--daemon')

    is_daemon = "--daemon" in cmd

    if is_daemon:
        await asyncio.create_subprocess_exec(
            *cmd,
            cwd=str(RUN_DIR),
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        return {
            "status": "success",
            "action": action,
            "service": service or "all",
            "message": f"Successfully executed '{action}'",
            "command": " ".join(cmd),
            "output": "",
            "stderr": "",
            "daemon": True,
        }

    proc = await asyncio.create_subprocess_exec(
        *cmd,
        cwd=str(RUN_DIR),
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    try:
        stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=timeout)
    except asyncio.TimeoutError:
        proc.kill()
        await proc.wait()
        raise HTTPException(status_code=500, detail=f"Command timeout after {timeout}s for {service or 'all'}")

    stdout_str = stdout.decode(errors='replace') if stdout else ""
    stderr_str = stderr.decode(errors='replace') if stderr else ""

    if proc.returncode != 0:
        raise HTTPException(status_code=400, detail=f"Failed to {action} {service or 'services'}: {stderr_str}")

    return {
        "status": "success",
        "action": action,
        "service": service or "all",
        "message": f"Successfully executed '{action}'",
        "command": " ".join(cmd),
        "output": stdout_str,
        "stderr": stderr_str,
        "daemon": False,
    }


@app.post("/api/control")
async def control_service(control: ServiceControl, current_user: dict = Depends(get_current_user)):
    require_operator(current_user)
    service_key = control.service or "__all__"
    lock = await _get_service_lock(service_key)

    if lock.locked():
        raise HTTPException(status_code=409, detail=f"Service '{control.service or 'all'}' is already being operated on")

    async with lock:
        try:
            logger.info(f"Control action: {control.action} service={control.service} user={current_user['username']}")
            result = await _run_service_command(control.action, control.service)
            append_audit_log(user=current_user["username"], role=current_user.get("role", "admin"), action=control.action, target=control.service or "all")
            return result
        except HTTPException:
            append_audit_log(user=current_user["username"], role=current_user.get("role", "admin"), action=control.action, target=control.service or "all", result="failed", detail="error")
            raise
        except Exception as e:
            import traceback
            tb = traceback.extract_tb(e.__traceback__)
            for frame in tb:
                print(f'ERROR: {e} FILENAME: {frame.filename} LINENO: {frame.lineno} FUNCTIONNAME: {frame.name} ')
                logger.error(f'ERROR: {e} FILENAME: {frame.filename} LINENO: {frame.lineno} FUNCTIONNAME: {frame.name} ')
            logger.error(f"Control error: {e}")
            
            append_audit_log(user=current_user["username"], role=current_user.get("role", "admin"), action=control.action, target=control.service or "all", result="failed", detail=str(e))
            raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/batch-control")
async def batch_control_services(batch: BatchServiceControl, current_user: dict = Depends(get_current_user)):
    require_operator(current_user)
    if not batch.services:
        raise HTTPException(status_code=400, detail="No services specified")
    if len(batch.services) > 50:
        raise HTTPException(status_code=400, detail="Too many services (max 50)")

    async def _control_one(service_name: str) -> dict:
        lock = await _get_service_lock(service_name)
        if lock.locked():
            return {"service": service_name, "status": "skipped", "message": f"Service '{service_name}' is being operated by another user"}
        async with lock:
            try:
                result = await _run_service_command(batch.action, service_name)
                append_audit_log(user=current_user["username"], role=current_user.get("role", "admin"), action=batch.action, target=service_name)
                return result
            except HTTPException as he:
                return {"service": service_name, "status": "failed", "message": he.detail}
            except Exception as e:
                return {"service": service_name, "status": "failed", "message": str(e)}

    results = await asyncio.gather(*[_control_one(s) for s in batch.services])
    succeeded = sum(1 for r in results if r.get("status") == "success")
    skipped = sum(1 for r in results if r.get("status") == "skipped")
    failed = sum(1 for r in results if r.get("status") == "failed")

    append_audit_log(user=current_user["username"], role=current_user.get("role", "admin"), action=f"batch_{batch.action}", target=",".join(batch.services), detail=f"ok={succeeded} skipped={skipped} failed={failed}")

    return {
        "status": "success" if failed == 0 else ("partial" if succeeded > 0 else "failed"),
        "action": batch.action,
        "total": len(batch.services),
        "succeeded": succeeded,
        "skipped": skipped,
        "failed": failed,
        "results": results,
    }


@app.get("/api/logs")
async def get_logs(
    service: str = Query(...),
    lines: str = Query("100"),
    offset: int = Query(0),
    search: Optional[str] = Query(None),
    level: Optional[str] = Query(None),
    range: Optional[str] = Query(None, alias="range"),
    current_user: dict = Depends(get_current_user)
) -> Dict:
    _range_seconds = {"1h": 3600, "6h": 6*3600, "24h": 24*3600, "7d": 7*24*3600, "30d": 30*24*3600}
    time_cutoff = None
    if range and range != "all" and range in _range_seconds:
        time_cutoff = datetime.now() - timedelta(seconds=_range_seconds[range])
    try:
        log_file = LOGS_DIR / f"{service}.log"
        chain = get_log_chain(service)
        if not chain:
            return {"service": service, "logs": [], "total": 0, "displayed": 0}
        rotate_log_if_needed(log_file)

        if search or level or time_cutoff:
            indexed_logs = []
            global_idx = 0
            for fpath in chain:
                try:
                    with open(fpath, 'r', encoding='utf-8', errors='ignore') as f:
                        for line in f:
                            indexed_logs.append((global_idx, line))
                            global_idx += 1
                except Exception:
                    pass
            total_lines = global_idx
        else:
            try:
                n_lines = int(lines)
            except Exception:
                n_lines = 0 if str(lines).lower() in ("all", "0") else 100
            if n_lines <= 0:
                n_lines = 500
            n_lines = min(n_lines, 500)
            indexed_logs, total_lines = read_chained_log_lines(chain, offset, n_lines)
            indexed_logs = [(idx, line) for idx, line in indexed_logs]

        if level:
            level_upper = level.upper()
            indexed_logs = [(idx, line) for idx, line in indexed_logs if extract_log_level(line) == level_upper]

        if time_cutoff:
            def _line_in_range(line: str) -> bool:
                ts_str = line[:19]
                try:
                    ts = datetime.strptime(ts_str, "%Y-%m-%d %H:%M:%S")
                    return ts >= time_cutoff
                except Exception:
                    return True
            indexed_logs = [(idx, line) for idx, line in indexed_logs if _line_in_range(line)]

        if search:
            lowered = search.lower()
            filtered_indexed_logs = [(idx, line) for idx, line in indexed_logs if lowered in line.lower()]
        else:
            filtered_indexed_logs = indexed_logs

        try:
            n_lines = int(lines)
        except Exception:
            n_lines = 0 if str(lines).lower() in ("all", "0") else 100
        if n_lines > 0:
            n_lines = min(n_lines, 500)

        if search or level or time_cutoff:
            filtered_total = len(filtered_indexed_logs)
            if n_lines <= 0 or str(lines).lower() == "all":
                logs_to_return = filtered_indexed_logs
                real_offset = 0
            else:
                if offset < 0:
                    start = max(filtered_total + offset, 0)
                else:
                    start = min(offset, filtered_total)
                end = min(start + n_lines, filtered_total)
                logs_to_return = filtered_indexed_logs[start:end]
                real_offset = start
        else:
            filtered_total = total_lines
            logs_to_return = filtered_indexed_logs
            real_offset = max(filtered_total + offset, 0) if offset < 0 else offset

        entries = []
        for idx, log_line in logs_to_return:
            if log_line.strip():
                entry_level = extract_log_level(log_line)
                line_number = idx + 1
                entries.append({
                    "raw": log_line.rstrip(),
                    "level": entry_level,
                    "timestamp": log_line[:19] if len(log_line) > 19 else "",
                    "line": line_number,
                })

        log_size = sum(f.stat().st_size for f in chain if f.exists())

        return {
            "service": service,
            "logs": entries,
            "total": filtered_total,
            "total_all": total_lines,
            "displayed": len(entries),
            "searched": filtered_total if search else total_lines,
            "offset": real_offset,
            "has_more_prev": real_offset > 0,
            "has_more_next": real_offset + len(entries) < filtered_total,
            "log_size": log_size
        }
    except Exception as e:
        logger.error(f"Failed to get logs: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/logs/search-matches")
async def search_log_matches(
    service: str = Query(...),
    search: str = Query(...),
    level: Optional[str] = Query(None),
    range: Optional[str] = Query(None, alias="range"),
    current_user: dict = Depends(get_current_user)
) -> Dict:
    _range_seconds = {"1h": 3600, "6h": 6*3600, "24h": 24*3600, "7d": 7*24*3600, "30d": 30*24*3600}
    time_cutoff = None
    if range and range != "all" and range in _range_seconds:
        time_cutoff = datetime.now() - timedelta(seconds=_range_seconds[range])
    try:
        chain = get_log_chain(service)
        if not chain:
            return {"matches": [], "total_matches": 0, "total_lines": 0}
        lowered = search.lower()
        level_upper = level.upper() if level else None
        matches = []
        global_idx = 0
        for fpath in chain:
            try:
                with open(fpath, 'r', encoding='utf-8', errors='ignore') as f:
                    for line in f:
                        global_idx += 1
                        if level_upper and extract_log_level(line) != level_upper:
                            continue
                        if time_cutoff:
                            ts_str = line[:19]
                            try:
                                ts = datetime.strptime(ts_str, "%Y-%m-%d %H:%M:%S")
                                if ts < time_cutoff:
                                    continue
                            except Exception:
                                pass
                        if lowered in line.lower():
                            matches.append(global_idx)
            except Exception:
                pass
        return {"matches": matches, "total_matches": len(matches), "total_lines": global_idx}
    except Exception as e:
        logger.error(f"Search matches error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/logs/download")
async def download_logs(service: str = Query(...), current_user: dict = Depends(get_current_user)):
    try:
        chain = get_log_chain(service)
        if not chain:
            raise HTTPException(status_code=404, detail=f"Log file for {service} not found")
        if len(chain) == 1:
            return FileResponse(
                path=chain[0],
                filename=f"{service}-logs-{datetime.now().strftime('%Y%m%d-%H%M%S')}.log",
                media_type="text/plain"
            )
        async def merged_stream():
            for fpath in chain:
                try:
                    with open(fpath, 'rb') as f:
                        while True:
                            chunk = f.read(65536)
                            if not chunk:
                                break
                            yield chunk
                except Exception:
                    pass
        return StreamingResponse(
            merged_stream(),
            media_type="text/plain",
            headers={"Content-Disposition": f'attachment; filename="{service}-logs-{datetime.now().strftime("%Y%m%d-%H%M%S")}.log"'}
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Download error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/logs/level-counts")
async def get_log_level_counts(
    service: str = Query(...),
    range: Optional[str] = Query(None, alias="range"),
    current_user: dict = Depends(get_current_user)
) -> Dict:
    _range_seconds = {"1h": 3600, "6h": 6*3600, "24h": 24*3600, "7d": 7*24*3600, "30d": 30*24*3600}
    time_cutoff = None
    if range and range != "all" and range in _range_seconds:
        time_cutoff = datetime.now() - timedelta(seconds=_range_seconds[range])
    chain = get_log_chain(service)
    counts = {"ERROR": 0, "WARNING": 0, "INFO": 0, "DEBUG": 0}
    for fpath in chain:
        try:
            with open(fpath, 'r', encoding='utf-8', errors='ignore') as f:
                for line in f:
                    if time_cutoff:
                        ts_str = line[:19]
                        try:
                            ts = datetime.strptime(ts_str, "%Y-%m-%d %H:%M:%S")
                            if ts < time_cutoff:
                                continue
                        except Exception:
                            pass
                    lvl = extract_log_level(line)
                    if lvl in counts:
                        counts[lvl] += 1
        except Exception:
            pass
    return {"service": service, "counts": counts}


@app.get("/api/metrics/history")
async def get_metrics_history(
    service: str = Query(...),
    limit: int = Query(MAX_METRICS_HISTORY_POINTS, ge=1, le=MAX_METRICS_HISTORY_POINTS),
    start: Optional[str] = Query(None),
    end: Optional[str] = Query(None),
    step_seconds: int = Query(0, ge=0),
    current_user: dict = Depends(get_current_user)
) -> Dict:
    try:
        history = list(METRICS_HISTORY.get(service, []))
        def _parse_iso_timestamp(value: Optional[str]) -> Optional[datetime]:
            if not value:
                return None
            try:
                safe = value.replace('Z', '')
                return datetime.fromisoformat(safe)
            except Exception:
                return None
        start_dt = _parse_iso_timestamp(start)
        end_dt = _parse_iso_timestamp(end)
        if start_dt or end_dt:
            filtered = []
            for point in history:
                ts = _parse_iso_timestamp(point.get("timestamp"))
                if not ts:
                    continue
                if start_dt and ts < start_dt:
                    continue
                if end_dt and ts > end_dt:
                    continue
                filtered.append(point)
            history = filtered
        if step_seconds and step_seconds > 0:
            buckets: Dict[int, Dict] = {}
            for point in history:
                ts = _parse_iso_timestamp(point.get("timestamp"))
                if not ts:
                    continue
                bucket = int(ts.timestamp() // step_seconds)
                buckets[bucket] = point
            history = [buckets[key] for key in sorted(buckets.keys())]
        if limit and len(history) > limit:
            history = history[-limit:]
        return {"service": service, "interval_seconds": 10, "points": history, "count": len(history)}
    except Exception as e:
        logger.error(f"Failed to get metrics history: {e}")
        raise HTTPException(status_code=500, detail=str(e))


_RANGE_SECONDS = {"1h": 3600, "6h": 6*3600, "24h": 24*3600, "7d": 7*24*3600, "30d": 30*24*3600}


@app.get("/api/system-metrics/history")
async def get_system_metrics_history(
    range: str = Query("1h"),
    current_user: dict = Depends(get_current_user),
) -> Dict:
    try:
        entries = load_system_metrics_history()
        now = datetime.now()
        if range != "all" and range in _RANGE_SECONDS:
            cutoff = now - timedelta(seconds=_RANGE_SECONDS[range])
            def _parse_iso(value: Optional[str]) -> Optional[datetime]:
                if not value:
                    return None
                try:
                    return datetime.fromisoformat(value.replace('Z', ''))
                except Exception:
                    return None
            entries = [e for e in entries if _parse_iso(e.get("t")) and _parse_iso(e.get("t")) >= cutoff]
        max_points = 500
        if len(entries) > max_points:
            step = len(entries) // max_points
            entries = entries[::step]
        return {"range": range, "points": entries, "count": len(entries)}
    except Exception as e:
        logger.error(f"Failed to get system metrics history: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/metrics/sse")
async def metrics_sse(request: Request, service: str = Query(...), token: Optional[str] = Query(None)):
    get_user_from_request(request, token)
    async def event_generator():
        while True:
            if await request.is_disconnected():
                break
            try:
                latest = METRICS_HISTORY.get(service, [])
                point = latest[-1] if latest else None
                if point:
                    yield f"data: {json.dumps(point)}\n\n"
            except Exception as e:
                logger.error(f"SSE metrics error: {e}")
                break
            await asyncio.sleep(10)
    return StreamingResponse(event_generator(), media_type="text/event-stream")


@app.get("/api/disks", response_model=List[DiskPartitionInfo])
async def list_disks(current_user: dict = Depends(get_current_user)):
    return get_disk_partitions()


@app.get("/api/process-tree")
async def get_process_tree(
    service: str = Query(...),
    current_user: dict = Depends(get_current_user)
):
    pidfile = LOGS_DIR / f"{service}.pid"
    pid = None
    if pidfile.exists():
        try:
            pid = int(pidfile.read_text().strip())
        except Exception:
            pid = None
    if not pid:
        return {"service": service, "pid": None, "tree": None, "flat": []}

    tree = build_process_tree(pid)
    if not tree:
        return {"service": service, "pid": pid, "tree": None, "flat": []}

    flat = []
    def _flatten(node, depth=0):
        flat.append({
            "pid": node["pid"], "ppid": node["ppid"], "depth": depth,
            "name": node["name"], "cmdline": node["cmdline"], "status": node["status"],
            "cpu_percent": node["cpu_percent"], "memory_mb": node["memory_mb"],
            "memory_percent": node["memory_percent"], "read_bytes": node["read_bytes"],
            "write_bytes": node["write_bytes"], "num_threads": node["num_threads"],
            "create_time": node["create_time"],
        })
        for child in node.get("children", []):
            _flatten(child, depth + 1)
    _flatten(tree)

    return {"service": service, "pid": pid, "tree": tree, "flat": flat}


@app.post("/api/process-tree/kill")
async def kill_process(
    pid: int = Query(...),
    service: str = Query(...),
    kill_children: bool = Query(False),
    current_user: dict = Depends(get_current_user)
):
    import psutil
    require_operator(current_user)
    killed = []
    failed = []
    try:
        proc = psutil.Process(pid)
        targets = [proc]
        if kill_children:
            try:
                targets = proc.children(recursive=True) + [proc]
            except Exception:
                pass
        for p in targets:
            try:
                p_pid = p.pid
                p.terminate()
                killed.append(p_pid)
            except Exception as e:
                failed.append({"pid": p.pid, "error": str(e)})
        import time
        time.sleep(0.5)
        for p in targets:
            try:
                if p.is_running():
                    p.kill()
            except Exception:
                pass
    except psutil.NoSuchProcess:
        raise HTTPException(status_code=404, detail=f"Process {pid} not found")
    except psutil.AccessDenied:
        raise HTTPException(status_code=403, detail=f"Access denied for PID {pid}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    detail = f"killed={killed}"
    if failed:
        detail += f", failed={failed}"
    append_audit_log(user=current_user["username"], role=current_user.get("role", "admin"), action="kill_pid", target=service, detail=detail)
    return {"status": "success", "killed": killed, "failed": failed}


@app.get("/api/info")
async def get_info(service: str = Query(...), current_user: dict = Depends(get_current_user)):
    return get_service_info(service)


@app.post("/api/update/upload", response_model=UpdateTaskResponse)
async def upload_update_package(
    service: str = Query(...),
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_user)
):
    require_operator(current_user)
    if not file.filename or not file.filename.endswith(".tar.gz"):
        raise HTTPException(status_code=400, detail="Only .tar.gz packages are supported")
    upload_dir = RUN_DIR / "uploads"
    upload_dir.mkdir(exist_ok=True)
    task_id = uuid.uuid4().hex
    file_path = upload_dir / f"{service}-{task_id}.tar.gz"
    content = await file.read()
    file_path.write_bytes(content)

    UPDATE_TASKS[task_id] = {
        "service": service,
        "status": "queued",
        "update_progress": 0,
        "message": "Upload completed"
    }
    append_audit_log(user=current_user["username"], role=current_user.get("role", "admin"), action="upload", target=service, detail=f"file={file.filename}")
    asyncio.create_task(_run_update_task(task_id, service, file_path))
    return {"task_id": task_id}


async def _run_update_task(task_id: str, service: str, file_path):
    try:
        await asyncio.to_thread(perform_update, task_id, service, file_path, UPDATE_TASKS)
    except Exception as exc:
        task = UPDATE_TASKS.get(task_id)
        if task:
            task["status"] = "failed"
            task["message"] = str(exc)


@app.get("/api/update/progress", response_model=UpdateProgress)
async def get_update_progress(task_id: str = Query(...), current_user: dict = Depends(get_current_user)):
    task = UPDATE_TASKS.get(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Update task not found")
    return UpdateProgress(task_id=task_id, status=task["status"], update_progress=task["update_progress"], message=task.get("message"))


@app.get("/api/update/backups", response_model=List[BackupInfo])
async def get_update_backups(service: str = Query(...), current_user: dict = Depends(get_current_user)):
    return list_backups(service)


@app.post("/api/update/rollback")
async def rollback_update(service: str = Query(...), backup: str = Query(...), current_user: dict = Depends(get_current_user)):
    require_operator(current_user)
    try:
        rollback_to_backup(service, backup)
        append_audit_log(user=current_user["username"], role=current_user.get("role", "admin"), action="rollback", target=service, detail=f"backup={backup}")
        return {"status": "success", "message": "rollback completed"}
    except Exception as exc:
        append_audit_log(user=current_user["username"], role=current_user.get("role", "admin"), action="rollback", target=service, detail=f"backup={backup}", result="failed")
        raise HTTPException(status_code=400, detail=str(exc))


@app.get("/api/audit-logs")
async def get_audit_logs(
    limit: int = Query(200, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    current_user: dict = Depends(get_current_user),
):
    role = current_user.get("role", "admin")
    username_filter = None if role == "admin" else current_user["username"]
    entries, total = read_audit_logs(limit=limit, offset=offset, username=username_filter)
    return {"logs": entries, "total": total, "offset": offset, "limit": limit}


class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, List[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, service: str):
        await websocket.accept()
        self.active_connections.setdefault(service, []).append(websocket)
        logger.info(f"WebSocket connected for service: {service}")

    def disconnect(self, websocket: WebSocket, service: str):
        if service in self.active_connections:
            if websocket in self.active_connections[service]:
                self.active_connections[service].remove(websocket)
            if not self.active_connections[service]:
                del self.active_connections[service]
        logger.info(f"WebSocket disconnected for service: {service}")

    async def broadcast(self, service: str, message: dict):
        if service in self.active_connections:
            for connection in self.active_connections[service]:
                try:
                    await connection.send_json(message)
                except Exception as e:
                    logger.warning(f"Failed to send message: {e}")


manager = ConnectionManager()


@app.websocket("/api/ws/logs/{service}")
async def websocket_logs(websocket: WebSocket, service: str):
    token = websocket.query_params.get("token")
    if not token:
        await websocket.close(code=1008)
        return
    try:
        decode_token(token)
    except HTTPException:
        await websocket.close(code=1008)
        return

    await manager.connect(websocket, service)
    log_file = LOGS_DIR / f"{service}.log"

    try:
        file_position = 0
        if log_file.exists():
            file_position = log_file.stat().st_size
        pause = False
        while True:
            try:
                data = await asyncio.wait_for(websocket.receive_json(), timeout=1.0)
                if data.get("action") == "pause":
                    pause = True
                elif data.get("action") == "resume":
                    pause = False
                elif data.get("action") == "clear":
                    file_position = log_file.stat().st_size if log_file.exists() else 0
            except asyncio.TimeoutError:
                pass
            except Exception:
                break
            if not pause and log_file.exists():
                try:
                    current_size = log_file.stat().st_size
                    if current_size < file_position:
                        file_position = 0
                    if current_size > file_position:
                        with open(log_file, 'r', encoding='utf-8', errors='ignore') as f:
                            f.seek(file_position)
                            new_logs = f.readlines()
                            file_position = current_size
                            for log_line in new_logs:
                                if log_line.strip():
                                    level = extract_log_level(log_line)
                                    await websocket.send_json({
                                        "type": "log",
                                        "service": service,
                                        "raw": log_line.rstrip(),
                                        "level": level,
                                        "timestamp": log_line[:19] if len(log_line) > 19 else "",
                                    })
                except Exception as e:
                    logger.warning(f"Error reading logs: {e}")
            await asyncio.sleep(0.5)
    except WebSocketDisconnect:
        logger.info(f"WebSocket client disconnected for service: {service}")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
    finally:
        manager.disconnect(websocket, service)
        try:
            await websocket.close(code=1000)
        except Exception:
            pass


# ---- WebShell Terminal (pty) ----

@app.websocket("/api/ws/terminal")
async def websocket_terminal(websocket: WebSocket, token: Optional[str] = Query(None)):
    """Interactive shell via WebSocket + pty."""
    if not token:
        await websocket.close(code=1008)
        return
    try:
        user = decode_token(token)
    except HTTPException:
        await websocket.close(code=1008)
        return

    await websocket.accept()

    try:
        require_operator(user)
    except HTTPException as e:
        await websocket.send_text(f"\r\n\x1b[31mPermission denied: {e.detail}\x1b[0m\r\n")
        await websocket.close(code=1008)
        return

    logger.info(f"WebShell terminal opened by user={user['username']}")

    import pty
    import os
    import fcntl
    import struct
    import termios
    import signal
    import errno

    child_pid = None
    master_fd = None

    try:
        # Use pty.fork() which handles setsid / controlling terminal properly
        child_pid, master_fd = pty.fork()

        if child_pid == 0:
            # ---- Child process: exec a shell ----
            shell = os.environ.get("SHELL", "/bin/bash")
            env = os.environ.copy()
            env["TERM"] = "xterm-256color"
            env["LANG"] = os.environ.get("LANG", "en_US.UTF-8")
            os.chdir(str(RUN_DIR))
            os.execvpe(shell, [shell, "--login"], env)
            # never returns

        # ---- Parent process ----

        # Read from pty → send to websocket (background task)
        async def pty_reader():
            loop = asyncio.get_event_loop()
            try:
                while True:
                    try:
                        data = await loop.run_in_executor(
                            None, lambda: os.read(master_fd, 4096)
                        )
                        if not data:
                            break
                        await websocket.send_text(
                            data.decode("utf-8", errors="replace")
                        )
                    except OSError as e:
                        if e.errno == errno.EIO:
                            # Child exited → EIO on master fd
                            break
                        raise
            except asyncio.CancelledError:
                pass
            except Exception:
                pass

        reader_task = asyncio.create_task(pty_reader())

        try:
            while True:
                message = await websocket.receive()
                if message.get("type") == "websocket.disconnect":
                    break

                data = message.get("text") or ""
                if not data:
                    raw = message.get("bytes")
                    if raw:
                        data = raw.decode("utf-8", errors="replace")

                if not data:
                    continue

                # Check if it's a JSON resize command
                if data.startswith("{"):
                    try:
                        cmd = json.loads(data)
                        if cmd.get("type") == "resize":
                            cols = int(cmd.get("cols", 80))
                            rows = int(cmd.get("rows", 24))
                            winsize = struct.pack("HHHH", rows, cols, 0, 0)
                            fcntl.ioctl(master_fd, termios.TIOCSWINSZ, winsize)
                            continue
                    except (json.JSONDecodeError, ValueError):
                        pass

                # Write to pty
                os.write(master_fd, data.encode("utf-8"))

        except WebSocketDisconnect:
            pass
        except Exception as e:
            logger.error(f"WebShell error: {e}")
        finally:
            reader_task.cancel()
            try:
                await reader_task
            except asyncio.CancelledError:
                pass

    except Exception as e:
        logger.error(f"WebShell setup error: {e}")
        try:
            await websocket.send_text(f"\r\n\x1b[31mTerminal error: {e}\x1b[0m\r\n")
        except Exception:
            pass
    finally:
        # Cleanup
        if master_fd is not None:
            try:
                os.close(master_fd)
            except OSError:
                pass
        if child_pid is not None and child_pid > 0:
            try:
                os.kill(child_pid, signal.SIGTERM)
            except OSError:
                pass
            try:
                os.waitpid(child_pid, os.WNOHANG)
            except (OSError, ChildProcessError):
                pass
        try:
            await websocket.close(code=1000)
        except Exception:
            pass
        logger.info(f"WebShell terminal closed for user={user['username']}")


@app.get("/api/health")
async def health_check():
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}


frontend_dist = RUN_DIR / 'frontend' / 'dist'
if frontend_dist.exists():
    app.mount("/", StaticFiles(directory=frontend_dist, html=True), name="frontend")


if __name__ == "__main__":
    import argparse
    import uvicorn

    parser = argparse.ArgumentParser(description="Service Manager Dashboard API")
    parser.add_argument("--host", default="0.0.0.0", help="Host to bind to")
    parser.add_argument("--port", type=int, default=8080, help="Port to bind to")
    parser.add_argument("--reload", action="store_true", help="Enable auto-reload")
    parser.add_argument("--config", type=str, default="", help="Services Config")
    args = parser.parse_args()

    logger.info(f"Starting Service Manager Dashboard API on {args.host}:{args.port}")
    logger.info(f"API documentation: http://{args.host}:{args.port}/api/docs")
          
    uvicorn.run(
        app,
        host=args.host,
        port=args.port,
        reload=args.reload,
        log_level="info"
    )
