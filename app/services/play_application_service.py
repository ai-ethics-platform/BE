from datetime import datetime
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app import models, schemas


async def get_application_by_user_id(
    db: AsyncSession,
    user_id: int,
) -> Optional[models.PlayApplication]:
    """
    사용자 ID로 데모 신청 정보 조회
    """
    result = await db.execute(
        select(models.PlayApplication).where(
            models.PlayApplication.user_id == user_id
        )
    )

    return result.scalar_one_or_none()


async def create_or_reapply(
    db: AsyncSession,
    user_id: int,
    application_in: schemas.PlayApplicationCreate,
) -> models.PlayApplication:
    """
    데모 신청 생성 또는 거절 후 재신청

    - 신청 기록 없음:
        새 신청 생성 (pending)

    - pending:
        중복 신청 불가

    - approved:
        이미 승인된 사용자이므로 신청 불가

    - rejected:
        기존 신청 정보를 갱신하고 pending으로 변경
    """

    existing_application = await get_application_by_user_id(
        db=db,
        user_id=user_id,
    )

    # 기존 신청이 없는 경우
    if existing_application is None:
        application = models.PlayApplication(
            user_id=user_id,
            last_name=application_in.last_name.strip(),
            first_name=application_in.first_name.strip(),
            email=str(application_in.email),
            message=(
                application_in.message.strip()
                if application_in.message
                else None
            ),
            status="pending",
        )

        db.add(application)

        await db.commit()
        await db.refresh(application)

        return application

    # 이미 승인 대기 중
    if existing_application.status == "pending":
        raise ValueError(
            "이미 승인 대기 중인 신청이 있습니다."
        )

    # 이미 승인된 사용자
    if existing_application.status == "approved":
        raise ValueError(
            "이미 데모 이용이 승인된 사용자입니다."
        )

    # 거절된 사용자의 재신청
    if existing_application.status == "rejected":
        now = datetime.utcnow()

        existing_application.last_name = (
            application_in.last_name.strip()
        )
        existing_application.first_name = (
            application_in.first_name.strip()
        )
        existing_application.email = str(
            application_in.email
        )
        existing_application.message = (
            application_in.message.strip()
            if application_in.message
            else None
        )

        existing_application.status = "pending"

        # 새로운 신청으로 취급
        existing_application.applied_at = now

        # 이전 승인 시각이 남아있지 않도록 초기화
        existing_application.approved_at = None

        existing_application.updated_at = now

        await db.commit()
        await db.refresh(existing_application)

        return existing_application

    # 혹시 DB에 예상하지 못한 status가 들어간 경우
    raise ValueError(
        f"알 수 없는 신청 상태입니다: {existing_application.status}"
    )