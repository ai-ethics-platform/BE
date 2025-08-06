from datetime import timedelta
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status, Body
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from jose import jwt, JWTError

from app import schemas
from app.core import security
from app.core.config import settings
from app.services import user_service, auth_service
from app.core.deps import get_db

router = APIRouter()


@router.post("/login", response_model=schemas.Token)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """
    OAuth2 호환 토큰 로그인, 아이디와 비밀번호 사용 (form-data)
    """
    user = await auth_service.authenticate(
        db=db,
        username=form_data.username,
        password=form_data.password
    )
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="아이디 또는 비밀번호가 올바르지 않습니다",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token = auth_service.create_access_token(user.id)
    refresh_token = auth_service.create_refresh_token(user.id)
    return {
        "access_token": access_token, 
        "refresh_token": refresh_token,
        "token_type": "bearer"
    }


@router.post("/login-json", response_model=schemas.Token)
async def login_json(
    user_credentials: schemas.UserLogin,
    db: AsyncSession = Depends(get_db)
) -> Any:
    """
    JSON 형식 토큰 로그인, 아이디와 비밀번호 사용
    """
    user = await auth_service.authenticate(
        db=db,
        username=user_credentials.username,
        password=user_credentials.password
    )
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="아이디 또는 비밀번호가 올바르지 않습니다",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token = auth_service.create_access_token(user.id)
    refresh_token = auth_service.create_refresh_token(user.id)
    return {
        "access_token": access_token, 
        "refresh_token": refresh_token,
        "token_type": "bearer"
    }


@router.post("/signup", response_model=schemas.User)
async def register_user(
    user_in: schemas.UserCreate,
    db: AsyncSession = Depends(get_db)
) -> Any:
    """
    새로운 사용자 등록
    """
    # Check if username is already taken
    user = await user_service.get_user_by_username(db=db, username=user_in.username)
    if user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already registered"
        )
    
    # Check if email is already registered
    user = await user_service.get_user_by_email(db=db, email=user_in.email)
    if user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Create new user
    user = await user_service.create_user(db=db, user_in=user_in)
    return user


@router.post("/guest")
async def guest_login(
    guest_id: str = Body(..., embed=True)
):
    # DB 저장 없이 토큰만 발급
    access_token = auth_service.create_access_token_guest(guest_id, expires_minutes=60)
    refresh_token = auth_service.create_refresh_token_guest(guest_id)
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer"
    }


@router.post("/check-username", response_model=schemas.UsernameCheck)
async def check_username_available(
    username_in: schemas.UsernameCheck,
    db: AsyncSession = Depends(get_db)
) -> Any:
    """
    아이디 중복 확인
    """
    user = await user_service.get_user_by_username(db=db, username=username_in.username)
    return {"username": username_in.username, "available": user is None}


@router.post("/find-username", response_model=schemas.UsernameCheck)
async def find_username(
    user_info: schemas.FindUsernameRequest,
    db: AsyncSession = Depends(get_db)
) -> Any:
    """
    아이디 찾기 (이메일, 생년월일, 성별로 확인)
    """
    user = await user_service.get_user_by_email(db=db, email=user_info.email)
    if not user or user.birthdate != user_info.birthdate or user.gender != user_info.gender:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="일치하는 사용자 정보를 찾을 수 없습니다",
        )
    
    # 아이디의 앞 3글자만 보여주고 나머지는 *로 마스킹
    masked_username = user.username[:3] + "*" * (len(user.username) - 3)
    return {"username": masked_username, "available": None}


@router.post("/refresh", response_model=schemas.Token)
async def refresh_token(
    refresh_token: str = Body(..., embed=True),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """
    Refresh token을 사용하여 새로운 access token 발급
    """
    try:
        # Refresh token 검증
        payload = jwt.decode(
            refresh_token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
        )
        
        # Refresh token 타입 확인
        if payload.get("type") != "refresh":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid token type"
            )
        
        user_id = int(payload.get("sub"))
        
        # 사용자 존재 확인
        user = await user_service.get_user_by_id(db=db, user_id=user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # 새로운 access token 발급
        new_access_token = auth_service.create_access_token(user.id)
        new_refresh_token = auth_service.create_refresh_token(user.id)
        
        return {
            "access_token": new_access_token,
            "refresh_token": new_refresh_token,
            "token_type": "bearer"
        }
        
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Token refresh failed"
        ) 