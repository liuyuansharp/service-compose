"""Authentication: database, JWT, password hashing, dependencies."""

import json
import os
import sqlite3
from datetime import datetime, timedelta
from typing import Dict, List, Optional

from fastapi import Depends, HTTPException, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy import Column, DateTime, Integer, String, create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

from .config import AUTH_DB_PATH, SECRET_KEY, ALGORITHM, ACCESS_TOKEN_EXPIRE_MINUTES, logger

# ---------- Database ----------
AUTH_DB_URL = f"sqlite:///{AUTH_DB_PATH}"
engine = create_engine(AUTH_DB_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)
Base = declarative_base()

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
security = HTTPBearer(auto_error=False)


class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False)
    role = Column(String, default="admin", nullable=False)
    visible_cards = Column(String, default="", nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)


# ---------- Init ----------

def init_auth_db():
    AUTH_DB_PATH.parent.mkdir(exist_ok=True)
    Base.metadata.create_all(bind=engine)
    conn = sqlite3.connect(str(AUTH_DB_PATH))
    cursor = conn.cursor()
    existing = {row[1] for row in cursor.execute("PRAGMA table_info(users)").fetchall()}
    if "role" not in existing:
        cursor.execute("ALTER TABLE users ADD COLUMN role TEXT NOT NULL DEFAULT 'admin'")
    if "visible_cards" not in existing:
        cursor.execute("ALTER TABLE users ADD COLUMN visible_cards TEXT NOT NULL DEFAULT ''")
    conn.commit()
    conn.close()
    session = SessionLocal()
    try:
        count = session.query(User).count()
        if count == 0:
            default_password = os.getenv('DEFAULT_ADMIN_PASSWORD', 'ly1234')
            session.add(User(username='liuyuan', password_hash=pwd_context.hash(default_password), role='admin'))
            session.commit()
            logger.info("Created default admin user 'liuyuan'")
    finally:
        session.close()


# ---------- Helpers ----------

def get_user_by_username(username: str) -> Optional[Dict]:
    session = SessionLocal()
    try:
        user = session.query(User).filter(User.username == username).first()
        if not user:
            return None
        vc = []
        if user.visible_cards:
            try:
                vc = json.loads(user.visible_cards)
            except Exception:
                vc = []
        return {
            "id": user.id,
            "username": user.username,
            "password_hash": user.password_hash,
            "role": user.role or "admin",
            "visible_cards": vc,
            "created_at": user.created_at.isoformat() if user.created_at else None
        }
    finally:
        session.close()


def verify_password(plain_password: str, password_hash: str) -> bool:
    try:
        return pwd_context.verify(plain_password, password_hash)
    except Exception:
        return False


def authenticate_user(username: str, password: str) -> Optional[Dict]:
    user = get_user_by_username(username)
    if not user:
        return None
    if not verify_password(password, user['password_hash']):
        return None
    return user


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def decode_token(token: str) -> Dict:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise HTTPException(status_code=401, detail="Invalid authentication token")
        user = get_user_by_username(username)
        if not user:
            raise HTTPException(status_code=401, detail="User not found")
        return user
    except JWTError as exc:
        logger.warning(f"JWT decode error: {exc}")
        raise HTTPException(status_code=401, detail="Invalid authentication token") from exc


async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    if not credentials:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return decode_token(credentials.credentials)


def get_user_from_request(request: Request, token_param: Optional[str] = None) -> Dict:
    token = token_param
    if not token:
        auth_header = request.headers.get('authorization')
        if auth_header and auth_header.lower().startswith('bearer '):
            token = auth_header.split(' ', 1)[1]
    if not token:
        raise HTTPException(status_code=401, detail="Missing authentication token")
    return decode_token(token)


# ---------- Role Helpers ----------

VALID_ROLES = {"admin", "operator", "readonly"}


def require_role(current_user: dict, *allowed_roles: str):
    role = current_user.get("role", "admin")
    if role not in allowed_roles:
        raise HTTPException(status_code=403, detail="Permission denied")


def require_admin(current_user: dict):
    require_role(current_user, "admin")


def require_operator(current_user: dict):
    require_role(current_user, "admin", "operator")
