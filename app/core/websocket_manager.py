# app/core/websocket_manager.py
import json
import asyncio
from typing import Dict, Set, Optional
from fastapi import WebSocket, WebSocketDisconnect
from datetime import datetime
from fastapi.encoders import jsonable_encoder

from app import schemas


class WebSocketManager:
    def __init__(self):
        # 세션별 연결된 클라이언트들
        self.active_connections: Dict[str, Set[WebSocket]] = {}
        # WebSocket별 사용자 정보
        self.connection_info: Dict[WebSocket, dict] = {}
        # 연결 상태 모니터링
        self.connection_stats: Dict[str, dict] = {}
        # 연결 상태 추적
        self.connection_health: Dict[WebSocket, dict] = {}

    
    async def connect(self, websocket: WebSocket, session_id: str, user_info: dict):
        """WebSocket 연결 - 동시 접속 제한 없음"""
        # accept는 이미 호출된 상태로 가정
        
        if session_id not in self.active_connections:
            self.active_connections[session_id] = set()
            self.connection_stats[session_id] = {
                "total_connections": 0,
                "current_connections": 0,
                "max_concurrent": 0,
                "created_at": datetime.utcnow().isoformat(),
                "last_activity": datetime.utcnow().isoformat()
            }
        
        self.active_connections[session_id].add(websocket)
        self.connection_info[websocket] = {
            "session_id": session_id,
            "user_info": user_info,
            "connected_at": datetime.utcnow().isoformat(),
            "last_heartbeat": datetime.utcnow().isoformat()
        }
        
        # 연결 상태 추적 (더 관대한 설정)
        self.connection_health[websocket] = {
            "is_alive": True,
            "last_ping": datetime.utcnow().isoformat(),
            "failed_sends": 0,
            "consecutive_failures": 0  # 연속 실패 횟수
        }
        
        # 통계 업데이트
        self.connection_stats[session_id]["total_connections"] += 1
        self.connection_stats[session_id]["current_connections"] = len(self.active_connections[session_id])
        self.connection_stats[session_id]["max_concurrent"] = max(
            self.connection_stats[session_id]["max_concurrent"],
            self.connection_stats[session_id]["current_connections"]
        )
        self.connection_stats[session_id]["last_activity"] = datetime.utcnow().isoformat()
        
        print(f"🔗 WebSocket 연결: 세션 {session_id}, 현재 연결 수: {self.connection_stats[session_id]['current_connections']}")
        
        # 연결 성공 메시지 전송 (오류 시에도 연결 유지)
        try:
            await websocket.send_text(json.dumps(jsonable_encoder({
                "type": "connection_established",
                "session_id": session_id,
                "user_info": user_info,
                "timestamp": datetime.utcnow().isoformat(),
                "connection_count": self.connection_stats[session_id]["current_connections"]
            })))
            print(f"✅ 연결 확인 메시지 전송 성공: 세션 {session_id}")
        except Exception as e:
            print(f"⚠️ 연결 확인 메시지 전송 실패 (연결 유지): {e}")
            # 연결은 유지하되 실패 횟수만 증가
            if websocket in self.connection_health:
                self.connection_health[websocket]["failed_sends"] += 1
    
    def disconnect(self, websocket: WebSocket):
        """WebSocket 연결 해제"""
        if websocket in self.connection_info:
            session_id = self.connection_info[websocket]["session_id"]
            if session_id in self.active_connections:
                self.active_connections[session_id].discard(websocket)
                if not self.active_connections[session_id]:
                    del self.active_connections[session_id]
                    if session_id in self.connection_stats:
                        del self.connection_stats[session_id]
                else:
                    # 통계 업데이트
                    self.connection_stats[session_id]["current_connections"] = len(self.active_connections[session_id])
                    self.connection_stats[session_id]["last_activity"] = datetime.utcnow().isoformat()
                    print(f"🔌 WebSocket 해제: 세션 {session_id}, 현재 연결 수: {self.connection_stats[session_id]['current_connections']}")
            del self.connection_info[websocket]
            
        if websocket in self.connection_health:
            del self.connection_health[websocket]
    
    async def broadcast_to_session(self, session_id: str, message: dict):
        """특정 세션의 모든 클라이언트에게 메시지 브로드캐스트 - 안정성 개선"""
        if session_id not in self.active_connections:
            print(f"⚠️ 세션 {session_id}에 활성 연결이 없습니다.")
            return
        
        disconnected = set()
        connection_count = len(self.active_connections[session_id])
        success_count = 0
        
        print(f"📢 브로드캐스트 시작: 세션 {session_id}, 대상 연결 수: {connection_count}")
        
        for connection in self.active_connections[session_id].copy():  # 복사본으로 순회
            try:
                await connection.send_text(json.dumps(jsonable_encoder(message)))
                success_count += 1
                
                # 연결 상태 업데이트
                if connection in self.connection_health:
                    self.connection_health[connection]["last_ping"] = datetime.utcnow().isoformat()
                    self.connection_health[connection]["failed_sends"] = 0
                
            except WebSocketDisconnect:
                print(f"🔌 WebSocket 연결 끊김 감지: 세션 {session_id}")
                disconnected.add(connection)
            except Exception as e:
                print(f"❌ WebSocket 전송 오류: {e}")
                # 일시적인 오류는 무시하고 연결 유지
                if connection in self.connection_health:
                    self.connection_health[connection]["failed_sends"] += 1
                    # 10번 연속 실패 시에만 연결 해제 (더 관대한 정책)
                    if self.connection_health[connection]["failed_sends"] >= 10:
                        print(f"⚠️ 연결 {id(connection)}이 10번 연속 실패하여 해제됩니다.")
                        disconnected.add(connection)
        
        # 연결이 끊어진 클라이언트들만 정리
        for connection in disconnected:
            self.disconnect(connection)
        
        print(f"📢 브로드캐스트 완료: 세션 {session_id}, 성공: {success_count}/{connection_count}")
        
        # 통계 업데이트
        if session_id in self.connection_stats:
            self.connection_stats[session_id]["last_activity"] = datetime.utcnow().isoformat()
    
    async def send_personal_message(self, websocket: WebSocket, message: dict):
        """개별 클라이언트에게 메시지 전송 - 안정성 개선"""
        try:
            await websocket.send_text(json.dumps(jsonable_encoder(message)))
            
            # 연결 상태 업데이트
            if websocket in self.connection_health:
                self.connection_health[websocket]["last_ping"] = datetime.utcnow().isoformat()
                self.connection_health[websocket]["failed_sends"] = 0
            
            return True
            
        except WebSocketDisconnect:
            print("🔌 WebSocket 연결 끊김 감지")
            self.disconnect(websocket)
            return False
        except Exception as e:
            print(f"❌ 개인 메시지 전송 오류: {e}")
            
            # 실패 횟수 증가
            if websocket in self.connection_health:
                self.connection_health[websocket]["failed_sends"] += 1
                # 10번 연속 실패 시에만 연결 해제
                if self.connection_health[websocket]["failed_sends"] >= 40:
                    print(f"⚠️ 연결이 10번 연속 실패하여 해제됩니다.")
                    self.disconnect(websocket)
                    return False
            
            # 일시적인 오류는 연결을 유지
            return False
    
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
    
    def get_connection_stats(self, session_id: str) -> Optional[dict]:
        """세션의 연결 통계 조회"""
        return self.connection_stats.get(session_id)
    
    def get_all_stats(self) -> Dict[str, dict]:
        """모든 세션의 통계 조회"""
        return self.connection_stats.copy()
    
    def get_connection_health(self, session_id: str) -> Dict[str, dict]:
        """세션의 연결 상태 조회"""
        health_info = {}
        if session_id in self.active_connections:
            for connection in self.active_connections[session_id]:
                if connection in self.connection_health:
                    health_info[str(id(connection))] = self.connection_health[connection]
        return health_info
    
    async def ping_connections(self, session_id: str):
        """연결 상태 확인을 위한 ping 전송"""
        if session_id not in self.active_connections:
            return
        
        disconnected = set()
        for connection in self.active_connections[session_id].copy():
            try:
                await connection.send_text(json.dumps({
                    "type": "ping",
                    "timestamp": datetime.utcnow().isoformat()
                }))
                
                # 연결 상태 업데이트
                if connection in self.connection_health:
                    self.connection_health[connection]["last_ping"] = datetime.utcnow().isoformat()
                    
            except Exception as e:
                print(f"❌ Ping 실패: {e}")
                disconnected.add(connection)
        
        # 끊어진 연결 정리
        for connection in disconnected:
            self.disconnect(connection)


# 전역 WebSocket 매니저 인스턴스
websocket_manager = WebSocketManager() 