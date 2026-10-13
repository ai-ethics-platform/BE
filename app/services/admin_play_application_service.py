from datetime import datetime
from typing import List, Optional

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app import models


async def get_all_applications(
    db: AsyncSession,
    status_filter: Optional[str] = None,
) -> List[models.PlayApplication]:
    """
    전체 데모 신청 목록 조회

    status_filter:
    - None: 전체
    - pending: 승인 대기
    - approved: 승인
    - rejected: 거절
    """
    query = select(models.PlayApplication)

    if status_filter is not None:
        query = query.where(
            models.PlayApplication.status == status_filter
        )

    query = query.order_by(
        models.PlayApplication.applied_at.desc()
    )

    result = await db.execute(query)

    return list(result.scalars().all())


async def get_application_by_id(
    db: AsyncSession,
    application_id: int,
) -> Optional[models.PlayApplication]:
    """
    신청 ID로 신청 정보 조회
    """
    result = await db.execute(
        select(models.PlayApplication).where(
            models.PlayApplication.id == application_id
        )
    )

    return result.scalar_one_or_none()


async def approve_application(
    db: AsyncSession,
    application_id: int,
) -> models.PlayApplication:
    """
    승인 대기 신청 승인

    pending -> approved
    """
    application = await get_application_by_id(
        db=db,
        application_id=application_id,
    )

    if application is None:
        raise ValueError("신청 정보를 찾을 수 없습니다.")

    if application.status != "pending":
        raise ValueError(
            "승인 대기 상태의 신청만 승인할 수 있습니다."
        )

    now = datetime.utcnow()

    application.status = "approved"
    application.approved_at = now
    application.updated_at = now

    await db.commit()
    await db.refresh(application)

    return application


async def reject_application(
    db: AsyncSession,
    application_id: int,
) -> models.PlayApplication:
    """
    승인 대기 신청 거절

    pending -> rejected
    """
    application = await get_application_by_id(
        db=db,
        application_id=application_id,
    )

    if application is None:
        raise ValueError("신청 정보를 찾을 수 없습니다.")

    if application.status != "pending":
        raise ValueError(
            "승인 대기 상태의 신청만 거절할 수 있습니다."
        )

    now = datetime.utcnow()

    application.status = "rejected"
    application.approved_at = None
    application.updated_at = now

    await db.commit()
    await db.refresh(application)

    return application


async def cancel_approval(
    db: AsyncSession,
    application_id: int,
) -> models.PlayApplication:
    """
    승인 취소

    approved -> pending
    """
    application = await get_application_by_id(
        db=db,
        application_id=application_id,
    )

    if application is None:
        raise ValueError("신청 정보를 찾을 수 없습니다.")

    if application.status != "approved":
        raise ValueError(
            "승인된 신청만 승인을 취소할 수 있습니다."
        )

    now = datetime.utcnow()

    application.status = "pending"
    application.approved_at = None
    application.updated_at = now

    await db.commit()
    await db.refresh(application)

    return application


async def delete_rejected_applications(
    db: AsyncSession,
) -> int:
    """
    거절 상태의 신청을 모두 삭제

    반환값:
    삭제된 신청 건수
    """
    result = await db.execute(
        delete(models.PlayApplication).where(
            models.PlayApplication.status == "rejected"
        )
    )

    deleted_count = result.rowcount or 0

    await db.commit()

    return deleted_count