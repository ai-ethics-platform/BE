from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app import models, schemas
from app.core.security import get_password_hash, verify_password


async def get_user(db: AsyncSession, user_id: int) -> Optional[models.User]:
    """
    사용자 ID로 사용자 정보 조회
    """
    result = await db.execute(select(models.User).filter(models.User.id == user_id))
    return result.scalar_one_or_none()


async def get_user_by_email(db: AsyncSession, email: str) -> Optional[models.User]:
    """
    이메일로 사용자 정보 조회
    """
    result = await db.execute(select(models.User).filter(models.User.email == email))
    return result.scalar_one_or_none()


async def get_user_by_username(db: AsyncSession, username: str) -> Optional[models.User]:
    """
    사용자명으로 사용자 정보 조회
    """
    result = await db.execute(select(models.User).filter(models.User.username == username))
    return result.scalar_one_or_none()


async def create_user(db: AsyncSession, user_in: schemas.UserCreate) -> models.User:
    """
    새로운 사용자 생성
    """
    db_user = models.User(
        email=user_in.email,
        username=user_in.username,
        hashed_password=get_password_hash(user_in.password),
        birthdate=user_in.birthdate,
        gender=user_in.gender,
        education_level=user_in.education_level,
        major=user_in.major or "기타",
        is_active=True,
        is_guest=False,
        data_consent=user_in.data_consent,
        voice_consent=user_in.voice_consent
    )
    db.add(db_user)
    await db.commit()
    await db.refresh(db_user)
    return db_user


async def authenticate_user(db: AsyncSession, username: str, password: str) -> Optional[models.User]:
    """
    사용자 인증
    """
    user = await get_user_by_username(db, username)
    if not user:
        return None
    if not verify_password(password, user.hashed_password):
        return None
    return user


async def create_guest(db: AsyncSession, guest_id: str) -> models.User:
    db_user = models.User(
        username=guest_id,
        email=f"{guest_id}@guest.local",
        hashed_password="",
        birthdate="",
        gender="기타",
        education_level="기타",
        major="기타",
        is_active=True,
        is_guest=True,
        data_consent=False,
        voice_consent=False
    )
    db.add(db_user)
    await db.commit()
    await db.refresh(db_user)
    return db_user


async def update(db_obj: models.User, obj_in: schemas.UserUpdate) -> models.User:
    return db_obj