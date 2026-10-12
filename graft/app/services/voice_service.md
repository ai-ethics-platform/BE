# app/services/voice_service.py

- VoiceService · class · L15-L408 — class VoiceService
- create_voice_session · method · L18-L66 — async def create_voice_session( db: AsyncSession, room_code: str, creator_id: Optional[int], creator_nickname: str ) -> models.VoiceSession
- get_voice_session_by_room_code · method · L69-L85 — async def get_voice_session_by_room_code( db: AsyncSession, room_code: str ) -> Optional[models.VoiceSession]
- _generate_session_id · method · L88-L90 — def _generate_session_id() -> str
- get_voice_session_by_id · method · L93-L103 — async def get_voice_session_by_id( db: AsyncSession, session_id: str ) -> Optional[models.VoiceSession]
- join_voice_session · method · L106-L161 — async def join_voice_session( db: AsyncSession, session_id: str, user_id: Optional[int], guest_id: Optional[str], nickname: str ) -> Union[models.VoiceParticipant, List[models.VoiceParticipant]]
- update_voice_status · method · L164-L201 — async def update_voice_status( db: AsyncSession, session_id: str, user_id: Optional[int], guest_id: Optional[str], is_mic_on: bool, is_speaking: bool = False ) -> models.VoiceParticipant
- leave_voice_session · method · L204-L246 — async def leave_voice_session( db: AsyncSession, session_id: str, user_id: Optional[int], guest_id: Optional[str] ) -> bool
- start_recording · method · L249-L297 — async def start_recording( db: AsyncSession, session_id: str, user_id: Optional[int], guest_id: Optional[str] ) -> models.VoiceParticipant
- stop_recording · method · L300-L340 — async def stop_recording( db: AsyncSession, session_id: str, user_id: Optional[int], guest_id: Optional[str] ) -> tuple[models.VoiceParticipant, int]
- upload_recording · method · L343-L374 — async def upload_recording( db: AsyncSession, session_id: str, user_id: Optional[int], guest_id: Optional[str], file_path: str ) -> models.VoiceRecording
- get_session_participants · method · L377-L386 — async def get_session_participants( db: AsyncSession, session_id: str ) -> List[models.VoiceParticipant]
- get_participant_by_user · method · L389-L408 — async def get_participant_by_user( db: AsyncSession, session_id: str, user_id: Optional[int], guest_id: Optional[str] ) -> Optional[models.VoiceParticipant]
