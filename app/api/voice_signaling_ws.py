from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query, status
from typing import Dict, List
from app.core.security import verify_token

router = APIRouter()

# WebRTC 시그널링용 연결 매니저
class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, List[WebSocket]] = {}

    async def connect(self, room_code: str, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.setdefault(room_code, []).append(websocket)

    async def disconnect(self, room_code: str, websocket: WebSocket):
        if room_code in self.active_connections:
            self.active_connections[room_code].remove(websocket)
            if not self.active_connections[room_code]:
                del self.active_connections[room_code]

    async def broadcast(self, room_code: str, message: dict, sender: WebSocket):
        for conn in self.active_connections.get(room_code, []):
            if conn != sender:
                await conn.send_json(message)

manager = ConnectionManager()

@router.websocket("/ws/voice/signaling")
async def signaling_ws(
    websocket: WebSocket,
    room_code: str = Query(..., description="참여할 방 코드"),
    token: str = Query(..., description="JWT 인증 토큰")
):
    # 1. 토큰 검증 (불일치 시 연결 거부)
    payload = verify_token(token)
    if not token or not payload:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return
    # 2. 연결 수락 및 방 입장
    await manager.connect(room_code, websocket)
    try:
        while True:
            data = await websocket.receive_json()
            # data 예시: {"type": "offer", ...}, {"type": "answer", ...}, {"type": "candidate", ...}
            await manager.broadcast(room_code, data, sender=websocket)
    except WebSocketDisconnect:
        await manager.disconnect(room_code, websocket)

# --- 내 개인적 정리 ---
# 이 엔드포인트는 WebRTC 연결 협상에 필요한 시그널링 메시지(offer/answer/candidate)를
# 같은 room_code로 접속한 다른 참가자들에게 중계(relay)
# 실제 음성 데이터(오디오 스트림)는 백엔드를 거치지 않고, 프론트엔드끼리 직접 송수신(P2P)
# 프론트엔드는 이 엔드포인트에 WebSocket으로 연결 후, offer/answer/candidate 메시지를 주고받아야 함