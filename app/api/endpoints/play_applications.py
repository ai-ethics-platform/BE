from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app import models, schemas
from app.core.deps import get_db, get_current_user
from app.services import play_application_service


router = APIRouter()


@router.post(
    "",
    response_model=schemas.PlayApplicationResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_play_application(
    application_in: schemas.PlayApplicationCreate,
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
) -> Any:
    """
    현재 로그인한 사용자의 데모 이용 신청

    - 신청 기록 없음: pending 신청 생성
    - rejected: 기존 신청을 pending으로 변경하여 재신청
    - pending: 중복 신청 불가
    - approved: 중복 신청 불가
    """
    try:
        application = await play_application_service.create_or_reapply(
            db=db,
            user_id=current_user.id,
            application_in=application_in,
        )

        return application

    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        )


@router.get(
    "/me",
    response_model=schemas.PlayApplicationStatusResponse,
)
async def get_my_play_application_status(
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
) -> Any:
    """
    현재 로그인한 사용자의 데모 승인 상태 조회

    신청 기록이 없으면:
        status = null

    신청 기록이 있으면:
        pending / approved / rejected
    """
    application = (
        await play_application_service.get_application_by_user_id(
            db=db,
            user_id=current_user.id,
        )
    )

    if application is None:
        return {
            "status": None,
        }

    return {
        "status": application.status,
    }