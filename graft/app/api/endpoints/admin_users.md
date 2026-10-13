# app/api/endpoints/admin_users.py

- serialize_user · function · L14-L20 — def serialize_user(user: User) -> dict
- search_user · function · L24-L60 — async def search_user( username: str = Query( ..., min_length=1, max_length=50, description="검색할 사용자 아이디", ), db: AsyncSession = Depends(get_db), current_admin: User = Depends(get_current_admin_user), ) -> Any
- get_admin_users · function · L63-L81 — async def get_admin_users( db: AsyncSession = Depends(get_db), current_admin: User = Depends(get_current_admin_user), ) -> Any
- grant_admin_permission · function · L84-L120 — async def grant_admin_permission( user_id: int, db: AsyncSession = Depends(get_db), current_admin: User = Depends(get_current_admin_user), ) -> Any
- revoke_admin_permission · function · L124-L162 — async def revoke_admin_permission( user_id: int, db: AsyncSession = Depends(get_db), current_admin: User = Depends(get_current_admin_user), ) -> Any
