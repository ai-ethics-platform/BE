# app/core/websocket_manager.py

- WebSocketManager · class · L12-L244 — class WebSocketManager
- __init__ · method · L13-L21 — def __init__(self): # 세션별 연결된 클라이언트들
- connect · method · L24-L79 — async def connect(self, websocket: WebSocket, session_id: str, user_info: dict)
- disconnect · method · L81-L99 — def disconnect(self, websocket: WebSocket)
- broadcast_to_session · method · L101-L144 — async def broadcast_to_session(self, session_id: str, message: dict)
- send_personal_message · method · L146-L175 — async def send_personal_message(self, websocket: WebSocket, message: dict)
- broadcast_voice_status · method · L177-L185 — async def broadcast_voice_status(self, session_id: str, participant: schemas.VoiceParticipant)
- broadcast_participant_event · method · L187-L194 — async def broadcast_participant_event(self, session_id: str, event_type: str, participant: schemas.VoiceParticipant)
- get_session_participants · method · L196-L198 — def get_session_participants(self, session_id: str) -> Set[WebSocket]
- get_connection_count · method · L200-L202 — def get_connection_count(self, session_id: str) -> int
- get_connection_stats · method · L204-L206 — def get_connection_stats(self, session_id: str) -> Optional[dict]
- get_all_stats · method · L208-L210 — def get_all_stats(self) -> Dict[str, dict]
- get_connection_health · method · L212-L219 — def get_connection_health(self, session_id: str) -> Dict[str, dict]
- ping_connections · method · L221-L244 — async def ping_connections(self, session_id: str)
