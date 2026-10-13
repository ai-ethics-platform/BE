# app/services/auth_service.py

- authenticate · function · L11-L24 — async def authenticate( db: AsyncSession, username: str, password: str ) -> Optional[dict]
- create_access_token · function · L26-L39 — def create_access_token(user_id: int, expires_minutes: int = None) -> str
- create_refresh_token · function · L41-L44 — def create_refresh_token(user_id: int) -> str
- create_access_token_guest · function · L47-L54 — def create_access_token_guest(guest_id: str, expires_minutes: int = 60) -> str
- create_refresh_token_guest · function · L56-L63 — def create_refresh_token_guest(guest_id: str) -> str
