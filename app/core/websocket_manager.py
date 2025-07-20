# app/core/websocket_manager.py
import json
import asyncio
from typing import Dict, Set, Optional
from fastapi import WebSocket, WebSocketDisconnect
from datetime import datetime

from app import schemas


class WebSocketManager:
    def __init__(self):
        # 세션별 연결된 클라이언트들
        self.active_connections: Dict[str, Set[WebSocket]] = {}
        # WebSocket별 사용자 정보
        self.connection_info: Dict[WebSocket, dict] = {}
    
    async def connect(self, websocket: WebSocket, session_id: str, user_info: dict):
        """WebSocket 연결"""
        # accept는 이미 호출된 상태로 가정
        
        if session_id not in self.active_connections:
            self.active_connections[session_id] = set()
        
        self.active_connections[session_id].add(websocket)
        self.connection_info[websocket] = {
            "session_id": session_id,
            "user_info": user_info
        }
        
        # 연결 성공 메시지 전송
        await websocket.send_text(json.dumps({
            "type": "connection_established",
            "session_id": session_id,
            "user_info": user_info,
            "timestamp": datetime.utcnow().isoformat()
        }))
    
    def disconnect(self, websocket: WebSocket):
        """WebSocket 연결 해제"""
        if websocket in self.connection_info:
            session_id = self.connection_info[websocket]["session_id"]
            if session_id in self.active_connections:
                self.active_connections[session_id].discard(websocket)
                if not self.active_connections[session_id]:
                    del self.active_connections[session_id]
            del self.connection_info[websocket]
    
    async def broadcast_to_session(self, session_id: str, message: dict):
        """특정 세션의 모든 클라이언트에게 메시지 브로드캐스트"""
        if session_id in self.active_connections:
            disconnected = set()
            for connection in self.active_connections[session_id]:
                try:
                    await connection.send_text(json.dumps(message))
                except WebSocketDisconnect:
                    disconnected.add(connection)
                except Exception as e:
                    print(f"WebSocket 전송 오류: {e}")
                    disconnected.add(connection)
            
            # 연결이 끊어진 클라이언트들 정리
            for connection in disconnected:
                self.disconnect(connection)
    
    async def send_personal_message(self, websocket: WebSocket, message: dict):
        """개별 클라이언트에게 메시지 전송"""
        try:
            await websocket.send_text(json.dumps(message))
        except WebSocketDisconnect:
            self.disconnect(websocket)
        except Exception as e:
            print(f"개인 메시지 전송 오류: {e}")
            self.disconnect(websocket)
    
    async def broadcast_voice_status(self, session_id: str, participant: schemas.VoiceParticipant):
        """음성 상태 변경 브로드캐스트"""
        message = schemas.VoiceStatusBroadcast(
            participant_id=participant.id,
            nickname=participant.nickname,
            is_mic_on=participant.is_mic_on,
            is_speaking=participant.is_speaking
        )
        await self.broadcast_to_session(session_id, message.dict())
    
    async def broadcast_participant_event(self, session_id: str, event_type: str, participant: schemas.VoiceParticipant):
        """참가자 입장/퇴장 이벤트 브로드캐스트"""
        message = schemas.ParticipantEvent(
            type=event_type,
            participant_id=participant.id,
            nickname=participant.nickname
        )
        await self.broadcast_to_session(session_id, message.dict())
    
    def get_session_participants(self, session_id: str) -> Set[WebSocket]:
        """세션의 참가자들 조회"""
        return self.active_connections.get(session_id, set())
    
    def get_connection_count(self, session_id: str) -> int:
        """세션의 연결 수 조회"""
        return len(self.active_connections.get(session_id, set()))


# 전역 WebSocket 매니저 인스턴스
websocket_manager = WebSocketManager() 