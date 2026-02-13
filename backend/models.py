"""Pydantic models for API request/response."""

from typing import Dict, List, Optional
from pydantic import BaseModel


class ServiceStatus(BaseModel):
    name: str
    running: bool
    health: str = "stopped"
    health_reason: Optional[str] = None
    pid: Optional[int] = None
    uptime: Optional[str] = None
    uptime_seconds: Optional[int] = None
    restart_count: int = 0
    last_log: Optional[str] = None
    scheduled_restart: Optional[Dict] = None
    depends_on: List[str] = []


class PlatformStatus(BaseModel):
    status: str
    services: List[ServiceStatus]
    timestamp: str


class LogEntry(BaseModel):
    timestamp: str
    level: str
    message: str
    service: str


class ServiceControl(BaseModel):
    action: str
    service: Optional[str] = None


class BatchServiceControl(BaseModel):
    action: str
    services: List[str]


class SystemMetrics(BaseModel):
    cpu_percent: float
    cpu_count: int
    cpu_percents: List[float] = []
    memory_percent: float
    memory_used: int
    memory_total: int
    disk_percent: float
    disk_used: int
    disk_total: int
    disk_free: int
    timestamp: str


class DiskPartitionInfo(BaseModel):
    device: str
    mountpoint: str
    fstype: str
    total_gb: int
    used_gb: int
    free_gb: int
    percent: float
    io_read_speed: float = 0.0     # MB/s
    io_write_speed: float = 0.0    # MB/s
    io_read_total: float = 0.0     # GB cumulative
    io_write_total: float = 0.0    # GB cumulative


class DashboardStatus(BaseModel):
    status: str
    services: List[ServiceStatus]
    metrics: SystemMetrics
    timestamp: str


class ServiceInfo(BaseModel):
    name: str
    version: str
    commit_hash: str
    build_date: str
    uptime: Optional[str] = None
    uptime_seconds: Optional[int] = None


class UpdateTaskResponse(BaseModel):
    task_id: str


class UpdateProgress(BaseModel):
    task_id: str
    status: str
    update_progress: int
    message: Optional[str] = None


class BackupInfo(BaseModel):
    name: str
    created_at: str


class LoginRequest(BaseModel):
    username: str
    password: str


class UserProfile(BaseModel):
    username: str
    role: str = "admin"
    visible_cards: List[str] = []
    created_at: Optional[str] = None


class LoginResponse(BaseModel):
    token: str
    user: UserProfile


class UserCreateRequest(BaseModel):
    username: str
    password: str
    role: str = "readonly"
    visible_cards: List[str] = []


class UserUpdateRequest(BaseModel):
    password: Optional[str] = None
    role: Optional[str] = None
    visible_cards: Optional[List[str]] = None


class UserListItem(BaseModel):
    id: int
    username: str
    role: str
    visible_cards: List[str]
    created_at: Optional[str] = None


class ScheduledRestartRequest(BaseModel):
    service: str
    enabled: bool = False
    cron: str = ""
