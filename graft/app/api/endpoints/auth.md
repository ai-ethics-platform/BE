# app/api/endpoints/auth.py

- login · function · L19-L43 — async def login( form_data: OAuth2PasswordRequestForm = Depends(), db: AsyncSession = Depends(get_db) ) -> Any
- login_json · function · L47-L71 — async def login_json( user_credentials: schemas.UserLogin, db: AsyncSession = Depends(get_db) ) -> Any
- register_user · function · L75-L100 — async def register_user( user_in: schemas.UserCreate, db: AsyncSession = Depends(get_db) ) -> Any
- guest_login · function · L104-L131 — async def guest_login( guest_id: str = Body(..., embed=True), db: AsyncSession = Depends(get_db) )
- check_username_available · function · L135-L143 — async def check_username_available( username_in: schemas.UsernameCheck, db: AsyncSession = Depends(get_db) ) -> Any
- find_username · function · L147-L163 — async def find_username( user_info: schemas.FindUsernameRequest, db: AsyncSession = Depends(get_db) ) -> Any
- refresh_token · function · L167-L234 — async def refresh_token( refresh_token: str = Body(..., embed=True), db: AsyncSession = Depends(get_db) ) -> Any
