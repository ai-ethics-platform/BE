import json
import secrets
import string
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app import models


def _generate_code(length: int = 10) -> str:
    alphabet = string.ascii_lowercase + string.digits
    return ''.join(secrets.choice(alphabet) for _ in range(length))


class CustomGameService:
    @staticmethod
    async def create(
        db: AsyncSession,
        *,
        teacher_name: str,
        teacher_school: str,
        teacher_email: str,
        title: str,
        representative_image_url: Optional[str],
        data: dict
    ) -> models.CustomGame:
        # unique code
        code = await CustomGameService._generate_unique_code(db)

        game = models.CustomGame(
            code=code,
            teacher_name=teacher_name,
            teacher_school=teacher_school,
            teacher_email=teacher_email,
            title=title,
            representative_image_url=representative_image_url,
            data=json.dumps(data, ensure_ascii=False)
        )
        db.add(game)
        await db.commit()
        await db.refresh(game)
        return game

    @staticmethod
    async def get_by_code(db: AsyncSession, code: str) -> Optional[models.CustomGame]:
        result = await db.execute(
            select(models.CustomGame).where(models.CustomGame.code == code)
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def _generate_unique_code(db: AsyncSession) -> str:
        while True:
            code = _generate_code()
            exists = await db.execute(
                select(models.CustomGame.id).where(models.CustomGame.code == code)
            )
            if exists.scalar_one_or_none() is None:
                return code


custom_game_service = CustomGameService()



