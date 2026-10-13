# app/api/endpoints/voice.py

- create_voice_session · function · L15-L58 — async def create_voice_session( session_data: schemas.VoiceSessionCreate, db: AsyncSession = Depends(get_db), current_user: Union[models.User, dict] = Depends(get_current_user_or_guest) ) -> Any
- get_voice_session_by_room_code · function · L62-L86 — async def get_voice_session_by_room_code( room_code: str, db: AsyncSession = Depends(get_db) ) -> Any
- get_voice_session_by_id · function · L90-L114 — async def get_voice_session_by_id( session_id: str, db: AsyncSession = Depends(get_db) ) -> Any
- join_voice_session · function · L118-L177 — async def join_voice_session( session_id: str, join_data: schemas.VoiceJoinRequest, db: AsyncSession = Depends(get_db), current_user: Union[models.User, dict] = Depends(get_current_user_or_guest) ) -> Any
- update_voice_status · function · L181-L228 — async def update_voice_status( session_id: str, status_data: schemas.VoiceStatusUpdate, db: AsyncSession = Depends(get_db), current_user: Union[models.User, dict] = Depends(get_current_user_or_guest) ) -> Any
- leave_voice_session · function · L232-L273 — async def leave_voice_session( session_id: str, db: AsyncSession = Depends(get_db), current_user: Union[models.User, dict] = Depends(get_current_user_or_guest) ) -> Any
- websocket_endpoint · function · L277-L367 — async def websocket_endpoint(websocket: WebSocket, session_id: str)
