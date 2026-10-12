# app/services/custom_game_service.py

- _generate_code · function · L12-L14 — def _generate_code(length: int = 10) -> str
- CustomGameService · class · L17-L61 — class CustomGameService
- create · method · L19-L44 — async def create( db: AsyncSession, *, teacher_name: str, teacher_school: str, teacher_email: str, title: str, representative_image_url: Optional[str], data: dict ) -> models.CustomGame: # unique code
- get_by_code · method · L47-L51 — async def get_by_code(db: AsyncSession, code: str) -> Optional[models.CustomGame]
- _generate_unique_code · method · L54-L61 — async def _generate_unique_code(db: AsyncSession) -> str
