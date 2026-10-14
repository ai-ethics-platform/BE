# app/api/endpoints/game_diagnostics.py

- receive_game_diagnostics · function · L22-L58 — async def receive_game_diagnostics(request: Request, db: AsyncSession = Depends(get_db), user=Depends(get_current_user_or_guest))
