import os
from datetime import datetime, timedelta
from typing import Optional
from enum import Enum

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError
from passlib.context import CryptContext
from pydantic import BaseModel

SECRET_KEY = os.getenv("SECRET_KEY", "campus-secondhand-secret-key-change-in-prod")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24  # 24 hours

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")


class UserRole(str, Enum):
    ADMIN = "ADMIN"
    USER = "USER"


class CurrentUser(BaseModel):
    user_id: int
    username: str
    role: UserRole
    status: str


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode["exp"] = expire
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


async def get_current_user(token: str = Depends(oauth2_scheme)) -> CurrentUser:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("sub")
        role = payload.get("role")
        username = payload.get("username", "")
        user_status = payload.get("status", "ACTIVE")

        if user_id is None or role is None:
            raise HTTPException(status_code=401, detail="无效的认证信息")

        user = CurrentUser(
            user_id=int(user_id),
            username=username,
            role=UserRole(role),
            status=user_status,
        )

        if user.status != "ACTIVE":
            raise HTTPException(status_code=403, detail="账号已被禁用")

        return user

    except JWTError:
        raise HTTPException(status_code=401, detail="Token 无效或已过期")


def require_admin(current_user: CurrentUser = Depends(get_current_user)) -> CurrentUser:
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="仅系统管理员可执行该操作")
    return current_user


def ensure_item_owner_or_admin(item, current_user: CurrentUser):
    if current_user.role == UserRole.ADMIN:
        return
    if item.owner_id != current_user.user_id:
        raise HTTPException(status_code=403, detail="无权操作该物品")
