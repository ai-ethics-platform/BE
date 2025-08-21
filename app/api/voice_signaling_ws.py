from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query, status
from typing import Dict, List, Optional
from app.core.security import verify_token

router = APIRouter()

# WebRTC 시그널링용 연결 매니저 (from/to 라우팅 지원)
class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, List[WebSocket]] = {}
        # 방별 피어ID -> WebSocket
        self.room_peers: Dict[str, Dict[str, WebSocket]] = {}
        # WebSocket -> 피어ID
        self.ws_to_peer: Dict[WebSocket, str] = {}

    async def connect(self, room_code: str, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.setdefault(room_code, []).append(websocket)
        self.room_peers.setdefault(room_code, {})

    async def register_peer(self, room_code: str, websocket: WebSocket, peer_id: str) -> List[str]:
        # 동일 ID가 이미 있으면 기존 연결을 교체
        self.room_peers.setdefault(room_code, {})[peer_id] = websocket
        self.ws_to_peer[websocket] = peer_id
        # 현재 방의 다른 피어 목록 반환(본인 제외)
        return [pid for pid, ws in self.room_peers[room_code].items() if ws is not websocket]

    def get_peer_id(self, websocket: WebSocket) -> Optional[str]:
        return self.ws_to_peer.get(websocket)

    async def unregister_peer(self, room_code: str, websocket: WebSocket):
        # 역방향 매핑 제거
        peer_id = self.ws_to_peer.pop(websocket, None)
        if peer_id and room_code in self.room_peers:
            existed = self.room_peers[room_code].get(peer_id)
            if existed is websocket:
                self.room_peers[room_code].pop(peer_id, None)

    async def disconnect(self, room_code: str, websocket: WebSocket):
        await self.unregister_peer(room_code, websocket)
        if room_code in self.active_connections:
            if websocket in self.active_connections[room_code]:
                self.active_connections[room_code].remove(websocket)
            if not self.active_connections[room_code]:
                self.active_connections.pop(room_code, None)
                self.room_peers.pop(room_code, None)

    async def send_to(self, room_code: str, target_peer_id: str, message: dict):
        target_ws = self.room_peers.get(room_code, {}).get(target_peer_id)
        if target_ws:
            await target_ws.send_json(message)

    async def broadcast(self, room_code: str, message: dict, sender: Optional[WebSocket] = None):
        for conn in self.active_connections.get(room_code, []):
            if sender is None or conn is not sender:
                await conn.send_json(message)

manager = ConnectionManager()

@router.websocket("/ws/signaling")
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
            mtype = data.get("type")

            # 2-1) 피어 등록: { type: 'join', peer_id: 'user-123' }
            if mtype == "join":
                peer_id = str(data.get("peer_id") or payload.get("sub"))
                existing_peers = await manager.register_peer(room_code, websocket, peer_id)
                # 본인에게 현재 참가자 리스트 전달
                await websocket.send_json({
                    "type": "peers",
                    "peers": existing_peers
                })
                # 다른 참가자들에게 새 피어 알림
                await manager.broadcast(room_code, {
                    "type": "peer_joined",
                    "peer_id": peer_id
                }, sender=websocket)
                continue

            # 2-2) 시그널링: offer/answer/candidate 라우팅
            if mtype in ("offer", "answer", "candidate"):
                from_peer = manager.get_peer_id(websocket)
                to_peer = data.get("to")
                routed = dict(data)
                routed["from"] = from_peer

                if to_peer:
                    await manager.send_to(room_code, to_peer, routed)
                else:
                    # 대상이 없으면 브로드캐스트 (호환)
                    await manager.broadcast(room_code, routed, sender=websocket)
                continue

            # 그 외 메시지는 브로드캐스트 (디버그/확장용)
            await manager.broadcast(room_code, data, sender=websocket)

    except WebSocketDisconnect:
        peer_id = manager.get_peer_id(websocket)
        await manager.disconnect(room_code, websocket)
        if peer_id:
            await manager.broadcast(room_code, {
                "type": "peer_left",
                "peer_id": peer_id
            })

# --- 내 개인적 정리 ---
# 이 엔드포인트는 WebRTC 연결 협상에 필요한 시그널링 메시지(offer/answer/candidate)를
# 같은 room_code로 접속한 다른 참가자들에게 중계(relay)
# 실제 음성 데이터(오디오 스트림)는 백엔드를 거치지 않고, 프론트엔드끼리 직접 송수신(P2P)
# 프론트엔드는 이 엔드포인트에 WebSocket으로 연결 후, offer/answer/candidate 메시지를 주고받아야 함