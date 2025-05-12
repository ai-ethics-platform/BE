from typing import Any, List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app import models, schemas
from app.api import deps
from app.services import user_service

router = APIRouter()


@router.get("/me", response_model=schemas.User)
async def read_user_me(
    current_user: models.User = Depends(deps.get_current_user),
) -> Any:
    """
    현재 로그인한 사용자 정보 조회
    """
    return current_user


@router.put("/me", response_model=schemas.User)
async def update_user_me(
    user_in: schemas.UserUpdate,
    current_user: models.User = Depends(deps.get_current_user),
) -> Any:
    """
    현재 로그인한 사용자 정보 업데이트
    """
    user = await user_service.update(
        db_obj=current_user, obj_in=user_in
    )
    return user


@router.get("/stats", response_model=schemas.UserStats)
async def get_user_stats(
    current_user: models.User = Depends(deps.get_current_user),
) -> Any:
    """
    사용자 게임 통계 조회
    """
    stats = await user_service.get_stats(user_id=current_user.id)
    return stats


@router.post("/consent", response_model=schemas.User)
async def update_user_consent(
    consent_in: schemas.ConsentUpdate,
    current_user: models.User = Depends(deps.get_current_user),
) -> Any:
    """
    사용자 동의 정보 업데이트
    """
    user = await user_service.update_consent(
        user=current_user,
        data_consent=consent_in.data_consent,
        voice_consent=consent_in.voice_consent
    )
    return user 