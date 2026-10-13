# app/core/deps.py

- get_db · function · L21-L32 — async def get_db() -> AsyncGenerator[AsyncSession, None]
- get_current_user · function · L35-L97 — async def get_current_user( db: AsyncSession = Depends(get_db), token: str = Depends(oauth2_scheme) ) -> User
- get_current_approved_user · function · L99-L131 — async def get_current_approved_user( db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user), ) -> User
- get_current_active_user · function · L134-L146 — async def get_current_active_user( current_user: User = Depends(get_current_user), ) -> User
- get_current_admin_user · function · L149-L165 — async def get_current_admin_user( current_user: User = Depends(get_current_user), ) -> User
- get_current_user_or_guest · function · L168-L225 — async def get_current_user_or_guest( db: AsyncSession = Depends(get_db), token: Optional[str] = Depends(oauth2_scheme) ) -> Union[User, dict, None]
