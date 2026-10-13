from typing import Any, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app import models, schemas
from app.core.deps import get_current_admin_user, get_db
from app.services import admin_play_application_service


router = APIRouter()


def handle_service_error(exc: ValueError) -> None:
    """
    서비스 계층에서 발생한 ValueError를
    적절한 HTTP 응답으로 변환
    """
    message = str(exc)

    if "찾을 수 없습니다" in message:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=message,
        )

    raise HTTPException(
        status_code=status.HTTP_409_CONFLICT,
        detail=message,
    )


@router.get(
    "",
    response_model=List[schemas.PlayApplicationResponse],
)
async def get_play_applications(
    status_filter: Optional[str] = Query(
        default=None,
        alias="status",
        description="pending, approved, rejected 중 하나",
    ),
    db: AsyncSession = Depends(get_db),
    current_admin: models.User = Depends(get_current_admin_user),
) -> Any:
    """
    관리자용 플레이 신청 목록 조회

    - status 미지정: 전체 조회
    - status=pending: 승인 대기
    - status=approved: 승인
    - status=rejected: 거절
    """
    allowed_statuses = {
        "pending",
        "approved",
        "rejected",
    }

    if (
        status_filter is not None
        and status_filter not in allowed_statuses
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                "status는 pending, approved, rejected "
                "중 하나여야 합니다."
            ),
        )

    applications = (
        await admin_play_application_service.get_all_applications(
            db=db,
            status_filter=status_filter,
        )
    )

    return applications


@router.patch(
    "/{application_id}/approve",
    response_model=schemas.PlayApplicationActionResponse,
)
async def approve_play_application(
    application_id: int,
    db: AsyncSession = Depends(get_db),
    current_admin: models.User = Depends(get_current_admin_user),
) -> Any:
    """
    승인 대기 신청 승인

    pending -> approved
    """
    try:
        application = (
            await admin_play_application_service.approve_application(
                db=db,
                application_id=application_id,
            )
        )

        return {
            "id": application.id,
            "status": application.status,
            "message": "신청을 승인했습니다.",
        }

    except ValueError as exc:
        handle_service_error(exc)


@router.patch(
    "/{application_id}/reject",
    response_model=schemas.PlayApplicationActionResponse,
)
async def reject_play_application(
    application_id: int,
    db: AsyncSession = Depends(get_db),
    current_admin: models.User = Depends(get_current_admin_user),
) -> Any:
    """
    승인 대기 신청 거절

    pending -> rejected
    """
    try:
        application = (
            await admin_play_application_service.reject_application(
                db=db,
                application_id=application_id,
            )
        )

        return {
            "id": application.id,
            "status": application.status,
            "message": "신청을 거절했습니다.",
        }

    except ValueError as exc:
        handle_service_error(exc)


@router.patch(
    "/{application_id}/cancel-approval",
    response_model=schemas.PlayApplicationActionResponse,
)
async def cancel_play_application_approval(
    application_id: int,
    db: AsyncSession = Depends(get_db),
    current_admin: models.User = Depends(get_current_admin_user),
) -> Any:
    """
    승인된 신청의 승인 취소

    approved -> pending
    """
    try:
        application = (
            await admin_play_application_service.cancel_approval(
                db=db,
                application_id=application_id,
            )
        )

        return {
            "id": application.id,
            "status": application.status,
            "message": "승인을 취소했습니다.",
        }

    except ValueError as exc:
        handle_service_error(exc)


@router.delete(
    "/rejected",
)
async def delete_rejected_play_applications(
    db: AsyncSession = Depends(get_db),
    current_admin: models.User = Depends(get_current_admin_user),
) -> Any:
    """
    거절 상태의 신청 목록 전체 삭제
    """
    deleted_count = (
        await admin_play_application_service.delete_rejected_applications(
            db=db,
        )
    )

    return {
        "deleted_count": deleted_count,
        "message": f"거절 신청 {deleted_count}건을 삭제했습니다.",
    }