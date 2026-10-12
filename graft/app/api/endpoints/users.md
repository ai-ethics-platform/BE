# app/api/endpoints/users.py

- read_user_me · function · L14-L20 — async def read_user_me( current_user: models.User = Depends(get_current_user), ) -> Any
- update_user_me · function · L24-L34 — async def update_user_me( user_in: schemas.UserUpdate, current_user: models.User = Depends(get_current_user), ) -> Any
- get_user_stats · function · L38-L45 — async def get_user_stats( current_user: models.User = Depends(get_current_user), ) -> Any
