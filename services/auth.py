"""
鉴权核心服务模块。

用途：
1. 负责用户密码哈希与校验。
2. 负责 JWT 访问令牌的签发与解析。
3. 负责基于令牌查询当前登录用户，并提供 FastAPI 依赖函数。

依赖的环境变量名：
- SECRET_KEY：JWT 签名密钥
- ACCESS_TOKEN_EXPIRE_MINUTES：访问令牌有效期（分钟）

对外暴露的函数列表：
- hash_password
- verify_password
- create_access_token
- decode_access_token
- get_current_user
- require_current_user
- oauth2_scheme
"""

from __future__ import annotations

import os
from datetime import datetime, timedelta, timezone
from typing import Any

from dotenv import load_dotenv
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy import select
from sqlalchemy.orm import Session

from database import get_db
from models.user import User

load_dotenv()

SECRET_KEY = os.getenv("SECRET_KEY")
if not SECRET_KEY:
    raise RuntimeError(
        "SECRET_KEY is not set. Please create a .env file based on .env.example."
    )

ACCESS_TOKEN_EXPIRE_MINUTES = int(
    os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "10080")
)
ALGORITHM = "HS256"

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


def hash_password(plain: str) -> str:
    """对明文密码进行哈希。"""
    return pwd_context.hash(plain)


def verify_password(plain: str, hashed: str) -> bool:
    """校验明文密码与哈希密码是否匹配。"""
    return pwd_context.verify(plain, hashed)


def create_access_token(data: dict[str, Any]) -> str:
    """创建 JWT 访问令牌，要求 payload 中包含 sub。"""
    to_encode = data.copy()
    subject = to_encode.get("sub")
    if not subject:
        raise ValueError("Token payload must include 'sub'.")

    expire = datetime.now(timezone.utc) + timedelta(
        minutes=ACCESS_TOKEN_EXPIRE_MINUTES
    )
    to_encode["exp"] = expire
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def decode_access_token(token: str) -> dict[str, Any] | None:
    """解析 JWT 访问令牌，解析失败或过期时返回 None。"""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        if not payload.get("sub"):
            return None
        return payload
    except JWTError:
        return None


def get_current_user(token: str, db: Session) -> User | None:
    """根据访问令牌解析当前用户。"""
    payload = decode_access_token(token)
    if not payload:
        return None

    username = payload.get("sub")
    if not username:
        return None

    statement = select(User).where(User.username == username)
    return db.scalar(statement)


def require_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> User:
    """要求当前请求必须已登录，否则抛出 401。"""
    user = get_current_user(token, db)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="未登录或登录已过期",
        )
    return user
