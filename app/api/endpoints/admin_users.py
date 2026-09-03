from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_admin_user, get_db
from app.models.user import User


router = APIRouter()


def serialize_user(user: User) -> dict:
    return {
        "id": user.id,
        "username": user.username,
        "email": user.email,
        "is_admin": user.is_admin,
    }


@router.get("/search")
async def search_user(
    username: str = Query(
        ...,
        min_length=1,
        max_length=50,
        description="검색할 사용자 아이디",
    ),
    db: AsyncSession = Depends(get_db),
    current_admin: User = Depends(get_current_admin_user),
) -> Any:
    """
    관리자 권한을 관리할 일반 계정을 아이디로 검색합니다.
    """
    normalized_username = username.strip()

    if not normalized_username:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="사용자 아이디를 입력해주세요.",
        )

    result = await db.execute(
        select(User).where(
            User.username == normalized_username,
            User.is_guest.is_(False),
        )
    )

    user = result.scalar_one_or_none()

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="해당 사용자를 찾을 수 없습니다.",
        )

    return serialize_user(user)


@router.patch("/{user_id}/grant-admin")
async def grant_admin_permission(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    current_admin: User = Depends(get_current_admin_user),
) -> Any:
    """
    선택한 사용자에게 관리자 권한을 부여합니다.
    """
    user = await db.get(User, user_id)

    if user is None or user.is_guest:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="해당 사용자를 찾을 수 없습니다.",
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="비활성화된 계정에는 관리자 권한을 부여할 수 없습니다.",
        )

    if user.is_admin:
        return {
            **serialize_user(user),
            "message": "이미 관리자 권한이 있는 계정입니다.",
        }

    user.is_admin = True

    await db.commit()
    await db.refresh(user)

    return {
        **serialize_user(user),
        "message": "관리자 권한을 추가했습니다.",
    }


@router.patch("/{user_id}/revoke-admin")
async def revoke_admin_permission(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    current_admin: User = Depends(get_current_admin_user),
) -> Any:
    """
    선택한 사용자의 관리자 권한을 해제합니다.

    현재 로그인한 관리자가 자기 권한을 직접 해제하는 것은 허용하지 않습니다.
    """
    user = await db.get(User, user_id)

    if user is None or user.is_guest:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="해당 사용자를 찾을 수 없습니다.",
        )

    if user.id == current_admin.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="현재 로그인한 계정의 관리자 권한은 해제할 수 없습니다.",
        )

    if not user.is_admin:
        return {
            **serialize_user(user),
            "message": "이미 관리자 권한이 없는 계정입니다.",
        }

    user.is_admin = False

    await db.commit()
    await db.refresh(user)

    return {
        **serialize_user(user),
        "message": "관리자 권한을 해제했습니다.",
    }
