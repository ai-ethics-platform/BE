# app/services/user_service.py

- get_user · function · L8-L13 — async def get_user(db: AsyncSession, user_id: int) -> Optional[models.User]
- get_user_by_email · function · L16-L21 — async def get_user_by_email(db: AsyncSession, email: str) -> Optional[models.User]
- get_user_by_username · function · L24-L29 — async def get_user_by_username(db: AsyncSession, username: str) -> Optional[models.User]
- create_user · function · L32-L52 — async def create_user(db: AsyncSession, user_in: schemas.UserCreate) -> models.User
- authenticate_user · function · L55-L64 — async def authenticate_user(db: AsyncSession, username: str, password: str) -> Optional[models.User]
- create_guest · function · L67-L84 — async def create_guest(db: AsyncSession, guest_id: str) -> models.User
- update · function · L87-L88 — async def update(db_obj: models.User, obj_in: schemas.UserUpdate) -> models.User
