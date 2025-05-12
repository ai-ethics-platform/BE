from typing import Generator, Optional

from fastapi import Depends, HTTPException, status, WebSocket
from fastapi.security import OAuth2PasswordBearer
from jose import jwt
from jose.exceptions import JWTError
from pydantic import ValidationError
from sqlalchemy.ext.asyncio import AsyncSession

from app import models, schemas
from app.core import security
from app.core.config import settings
from app.db.session import get_db
from app.services import user_service

# OAuth2 토큰 URL 설정
oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.API_V1_STR}/auth/login")


async def get_current_user(
    db: AsyncSession = Depends(get_db),
    token: str = Depends(oauth2_scheme),
) -> models.User:
    """
    현재 인증된 사용자 가져오기
    """
    try:
        # JWT 토큰 디코딩
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[security.ALGORITHM]
        )
        token_data = schemas.TokenPayload(**payload)
    except (JWTError, ValidationError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="유효하지 않은 인증 정보",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # 사용자 정보 조회
    user = await user_service.get(id=token_data.sub)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="사용자를 찾을 수 없습니다",
        )
    
    return user


async def get_current_user_ws(token: str) -> Optional[models.User]:
    """
    웹소켓 연결용 사용자 인증
    """
    if not token:
        return None
    
    try:
        # JWT 토큰 디코딩
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[security.ALGORITHM]
        )
        token_data = schemas.TokenPayload(**payload)
    except (JWTError, ValidationError):
        return None
    
    # 사용자 정보 조회
    user = await user_service.get(id=token_data.sub)
    if not user:
        return None
    
    return user 