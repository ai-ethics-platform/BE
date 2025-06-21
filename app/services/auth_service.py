from datetime import datetime, timedelta
from typing import Optional

from jose import jwt
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.security import get_password_hash, verify_password
from app.services.user_service import get_user_by_username

async def authenticate(
    db: AsyncSession,
    username: str,
    password: str
) -> Optional[dict]:
    """
    사용자 인증
    """
    user = await get_user_by_username(db=db, username=username)
    if not user:
        return None
    if not verify_password(password, user.hashed_password):
        return None
    return user

def create_access_token(user_id: int, expires_minutes: int = None) -> str:
    """
    JWT 액세스 토큰 생성
    """
    expire = datetime.utcnow() + timedelta(minutes=expires_minutes or settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode = {
        "exp": expire,
        "sub": str(user_id)
    }
    return jwt.encode(
        to_encode,
        settings.SECRET_KEY,
        algorithm=settings.ALGORITHM
    )

def create_refresh_token(user_id: int) -> str:
    expire = datetime.utcnow() + timedelta(days=7)  # 7일 유효
    to_encode = {"exp": expire, "sub": str(user_id), "type": "refresh"}
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)

# --- Guest Token Functions ---
def create_access_token_guest(guest_id: str, expires_minutes: int = 60) -> str:
    expire = datetime.utcnow() + timedelta(minutes=expires_minutes)
    to_encode = {
        "exp": expire,
        "guest_id": guest_id,
        "type": "guest"
    }
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)

def create_refresh_token_guest(guest_id: str) -> str:
    expire = datetime.utcnow() + timedelta(days=7)
    to_encode = {
        "exp": expire,
        "guest_id": guest_id,
        "type": "guest_refresh"
    }
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM) 