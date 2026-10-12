# app/api/voice_signaling_ws.py

- ConnectionManager · class · L8-L56 — class ConnectionManager
- __init__ · method · L9-L14 — def __init__(self)
- connect · method · L16-L19 — async def connect(self, room_code: str, websocket: WebSocket)
- register_peer · method · L21-L26 — async def register_peer(self, room_code: str, websocket: WebSocket, peer_id: str) -> List[str]: # 동일 ID가 이미 있으면 기존 연결을 교체
- get_peer_id · method · L28-L29 — def get_peer_id(self, websocket: WebSocket) -> Optional[str]
- unregister_peer · method · L31-L37 — async def unregister_peer(self, room_code: str, websocket: WebSocket): # 역방향 매핑 제거
- disconnect · method · L39-L46 — async def disconnect(self, room_code: str, websocket: WebSocket)
- send_to · method · L48-L51 — async def send_to(self, room_code: str, target_peer_id: str, message: dict)
- broadcast · method · L53-L56 — async def broadcast(self, room_code: str, message: dict, sender: Optional[WebSocket] = None)
- signaling_ws · function · L61-L120 — async def signaling_ws( websocket: WebSocket, room_code: str = Query(..., description="참여할 방 코드"), token: str = Query(..., description="JWT 인증 토큰") ): # 1. 토큰 검증 (불일치 시 연결 거부)
