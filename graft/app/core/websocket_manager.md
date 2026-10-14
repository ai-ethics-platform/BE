# app/core/websocket_manager.py

- WebSocketManager · class · L14-L259 — class WebSocketManager
- __init__ · method · L15-L23 — def __init__(self): # 세션별 연결된 클라이언트들
- connect · method · L26-L81 — async def connect(self, websocket: WebSocket, session_id: str, user_info: dict)
- disconnect · method · L83-L101 — def disconnect(self, websocket: WebSocket)
- broadcast_to_session · method · L103-L159 — async def broadcast_to_session(self, session_id: str, message: dict)
- send_personal_message · method · L161-L190 — async def send_personal_message(self, websocket: WebSocket, message: dict)
- broadcast_voice_status · method · L192-L200 — async def broadcast_voice_status(self, session_id: str, participant: schemas.VoiceParticipant)
- broadcast_participant_event · method · L202-L209 — async def broadcast_participant_event(self, session_id: str, event_type: str, participant: schemas.VoiceParticipant)
- get_session_participants · method · L211-L213 — def get_session_participants(self, session_id: str) -> Set[WebSocket]
- get_connection_count · method · L215-L217 — def get_connection_count(self, session_id: str) -> int
- get_connection_stats · method · L219-L221 — def get_connection_stats(self, session_id: str) -> Optional[dict]
- get_all_stats · method · L223-L225 — def get_all_stats(self) -> Dict[str, dict]
- get_connection_health · method · L227-L234 — def get_connection_health(self, session_id: str) -> Dict[str, dict]
- ping_connections · method · L236-L259 — async def ping_connections(self, session_id: str)
