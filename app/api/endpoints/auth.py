from datetime import timedelta
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm

from app import schemas
from app.api import deps
from app.core import security
from app.core.config import settings
from app.services import user_service

router = APIRouter()


@router.post("/login", response_model=schemas.Token)
async def login_access_token(
    form_data: OAuth2PasswordRequestForm = Depends()
) -> Any:
    """
    OAuth2 호환 토큰 로그인, 아이디와 비밀번호 사용
    """
    user = await user_service.authenticate(
        username=form_data.username,
        password=form_data.password
    )
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="아이디 또는 비밀번호가 올바르지 않습니다",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    return {
        "access_token": security.create_access_token(
            user.id, expires_delta=access_token_expires
        ),
        "token_type": "bearer",
    }


@router.post("/register", response_model=schemas.User)
async def register_user(
    user_in: schemas.UserCreate,
) -> Any:
    """
    새로운 사용자 등록
    """
    # 아이디 중복 확인
    user = await user_service.get_by_username(username=user_in.username)
    if user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="이미 사용 중인 아이디입니다",
        )
    
    # 사용자 생성
    user = await user_service.create(user_in=user_in)
    return user


@router.post("/guest", response_model=schemas.Token)
async def login_guest() -> Any:
    """
    게스트 로그인, 임시 토큰 발급
    """
    guest_user = await user_service.create_guest()
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    return {
        "access_token": security.create_access_token(
            guest_user.id, expires_delta=access_token_expires
        ),
        "token_type": "bearer",
    }


@router.post("/check-username", response_model=schemas.UsernameCheck)
async def check_username_available(
    username_in: schemas.UsernameCheck,
) -> Any:
    """
    아이디 중복 확인
    """
    user = await user_service.get_by_username(username=username_in.username)
    return {"username": username_in.username, "available": user is None} 