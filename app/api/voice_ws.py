"""
app/api/voice_ws.py
실시간 음성 세션용 WebSocket 라우터
  • /ws/voice/{session_id}
  • 한 세션에 N명이 동시에 접속, 상태 브로드캐스트
"""

# app/api/voice_ws.py
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, status
from typing import Dict, List, Optional
import json
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_db
from app.services.voice_service import voice_service
from app.schemas.voice import VoiceStatusBroadcast, ParticipantEvent
from app.core.websocket_manager import websocket_manager as manager
from app.core.security import verify_token
from app.core import security
print("📥 받은 토큰: ", security.verify_token)
router = APIRouter()

#   WebSocket Endpoint
@router.websocket("/voice/{session_id}")
async def voice_session_ws(
    websocket: WebSocket,
    session_id: str,
    db: AsyncSession = Depends(get_db),
):
    # 1. 연결 수락 전에 토큰 검증
    token = websocket.query_params.get("token")
    if not token or not verify_token(token):
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    await websocket.accept()

    try:
        while True:
            raw = await websocket.receive_text()
            msg = json.loads(raw)

            mtype: str = msg.get("type")
            data: dict = msg.get("data", {})

            # 1) 최초 init
            if mtype == "init":
                await manager.connect(websocket, session_id, user_info=data)
                await _handle_init(db, session_id, data)

                await manager.broadcast_to_session(
                    session_id,
                    ParticipantEvent(
                        type="join",
                        participant_id=data.get("user_id") or data.get("guest_id"),
                        nickname=data["nickname"],
                    ).model_dump()
                )

            # 2) 마이크/발화 상태 변경
            elif mtype == "voice_status_update":
                participant = await voice_service.update_voice_status(
                    db=db,
                    session_id=session_id,
                    user_id=data.get("user_id"),
                    guest_id=data.get("guest_id"),
                    is_mic_on=data["is_mic_on"],
                    is_speaking=data.get("is_speaking", False),
                )
                await manager.broadcast_to_session(
                    session_id,
                    VoiceStatusBroadcast(
                        participant_id=participant.id,
                        nickname=participant.nickname,
                        is_mic_on=participant.is_mic_on,
                        is_speaking=participant.is_speaking,
                    ).model_dump()
                )

    except WebSocketDisconnect:
        manager.disconnect(websocket)
        await manager.broadcast_to_session(
            session_id,
            ParticipantEvent(type="leave", participant_id=None, nickname="-").model_dump()
        )

async def _handle_init(db: AsyncSession, session_id: str, data: dict):
    """초기 접속 시 DB 참가자 존재 여부를 확인하고 없으면 join."""
    user_id = data.get("user_id")
    guest_id = data.get("guest_id")
    nickname = data["nickname"]

    participant = await voice_service.get_participant_by_user(
        db=db,
        session_id=session_id,
        user_id=user_id,
        guest_id=guest_id,
    )
    if not participant:
        await voice_service.join_voice_session(
            db=db,
            session_id=session_id,
            user_id=user_id,
            guest_id=guest_id,
            nickname=nickname,
        )