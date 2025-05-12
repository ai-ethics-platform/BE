from typing import Dict, List, Any

from fastapi import WebSocket


class ConnectionManager:
    """
    웹소켓 연결 관리 클래스
    """
    def __init__(self):
        # 방 ID별로 연결된 웹소켓 관리
        self.active_connections: Dict[int, List[WebSocket]] = {}
        # 웹소켓과 사용자 ID 매핑
        self.socket_to_user: Dict[WebSocket, int] = {}
        # 방 ID별 사용자 ID 목록
        self.room_users: Dict[int, List[int]] = {}

    async def connect(self, websocket: WebSocket, room_id: int, user_id: int):
        """
        새로운 웹소켓 연결 등록
        """
        await websocket.accept()
        
        # 방 연결 목록에 추가
        if room_id not in self.active_connections:
            self.active_connections[room_id] = []
        self.active_connections[room_id].append(websocket)
        
        # 사용자 매핑 추가
        self.socket_to_user[websocket] = user_id
        
        # 방 사용자 목록에 추가
        if room_id not in self.room_users:
            self.room_users[room_id] = []
        if user_id not in self.room_users[room_id]:
            self.room_users[room_id].append(user_id)
        
        # 새로운 연결 알림
        await self.broadcast(
            room_id,
            {
                "type": "player_connect",
                "user_id": user_id,
                "active_users": self.room_users[room_id]
            }
        )

    def disconnect(self, websocket: WebSocket, room_id: int, user_id: int):
        """
        웹소켓 연결 해제 처리
        """
        # 방 연결 목록에서 제거
        if room_id in self.active_connections:
            if websocket in self.active_connections[room_id]:
                self.active_connections[room_id].remove(websocket)
            
            # 방에 더 이상 연결이 없으면 방 정보 삭제
            if not self.active_connections[room_id]:
                del self.active_connections[room_id]
        
        # 사용자 매핑 제거
        if websocket in self.socket_to_user:
            del self.socket_to_user[websocket]
        
        # 방 사용자 목록에서 제거 (같은 사용자의 다른 연결이 없을 경우)
        user_exists = False
        if room_id in self.active_connections:
            for ws in self.active_connections[room_id]:
                if self.socket_to_user.get(ws) == user_id:
                    user_exists = True
                    break
        
        if not user_exists and room_id in self.room_users:
            if user_id in self.room_users[room_id]:
                self.room_users[room_id].remove(user_id)
            
            # 방에 더 이상 사용자가 없으면 방 사용자 정보 삭제
            if not self.room_users[room_id]:
                del self.room_users[room_id]

    async def broadcast(self, room_id: int, message: Any):
        """
        특정 방의 모든 연결에 메시지 브로드캐스트
        """
        if room_id in self.active_connections:
            for connection in self.active_connections[room_id]:
                await connection.send_json(message)
    
    async def send_personal_message(self, websocket: WebSocket, message: Any):
        """
        특정 연결에만 메시지 전송
        """
        await websocket.send_json(message) 