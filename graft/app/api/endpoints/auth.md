# app/api/endpoints/auth.py

- login · function · L19-L45 — async def login( request: Request, form_data: OAuth2PasswordRequestForm = Depends(), db: AsyncSession = Depends(get_db) ) -> Any
- login_json · function · L49-L75 — async def login_json( request: Request, user_credentials: schemas.UserLogin, db: AsyncSession = Depends(get_db) ) -> Any
- register_user · function · L79-L104 — async def register_user( user_in: schemas.UserCreate, db: AsyncSession = Depends(get_db) ) -> Any
- guest_login · function · L108-L135 — async def guest_login( guest_id: str = Body(..., embed=True), db: AsyncSession = Depends(get_db) )
- check_username_available · function · L139-L147 — async def check_username_available( username_in: schemas.UsernameCheck, db: AsyncSession = Depends(get_db) ) -> Any
- find_username · function · L151-L167 — async def find_username( user_info: schemas.FindUsernameRequest, db: AsyncSession = Depends(get_db) ) -> Any
- refresh_token · function · L171-L238 — async def refresh_token( refresh_token: str = Body(..., embed=True), db: AsyncSession = Depends(get_db) ) -> Any
