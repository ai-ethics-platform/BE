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
router = APIRouter()

#   WebSocket Endpoint
@router.websocket("/voice/{session_id}")
async def voice_session_ws(
    websocket: WebSocket,
    session_id: str,
    db: AsyncSession = Depends(get_db),
):
    print("✅ WebSocket 도달 확인")
    # 1. 연결 수락 전에 토큰 검증
    token = websocket.query_params.get("token", "").strip('"')
    print("📥 받은 토큰: ", token)

    payload = verify_token(token)
    print("🔍 디코딩된 payload: ", payload)

    if not token or not payload:
        print("❌ WebSocket 연결 거부됨 - 토큰 문제")
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    user_id = payload.get("sub")

    # 2. 초기 연결 처리
    # dict 형태로 넘기기
    await _handle_init(db, session_id, {
        "user_id": user_id,
        "guest_id": None,
        "nickname": "익명유저"
})

    # 3. 메시지 수신 루프
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
            # 3) 녹음 시작
            elif mtype == "start_recording":
                participant = await voice_service.start_recording(
                    db=db,
                    session_id=session_id,
                    user_id=user_id,
                    guest_id=None,
                )
                print(f"🎙️ 녹음 시작됨: {participant.recording_file_path}")
                await websocket.send_json({
                    "type": "recording_started",
                    "data": {
                        "path": participant.recording_file_path,
                        "started_at": str(participant.recording_started_at)
                    }
                })
            # 4) 녹음 종료
            elif mtype == "stop_recording":
                participant, duration = await voice_service.stop_recording(
                    db=db,
                    session_id=session_id,
                    user_id=user_id,
                    guest_id=None,
                )
                print(f"🛑 녹음 종료됨: {participant.recording_file_path}, duration={duration}s")
                await websocket.send_json({
                    "type": "recording_stopped",
                    "data": {
                        "path": participant.recording_file_path,
                        "ended_at": str(participant.recording_ended_at),
                        "duration": duration
                    }
                })
            # 5) 방장만 다음 페이지 신호
            elif mtype == "next_page":
                print(f"🟢 next_page 메시지 수신! data={data}, user_id={user_id}")
                from app.services.voice_service import VoiceService
                from app.services.room_service import RoomService
                # session_id로 voice_session을 조회해서 room_id를 얻음
                voice_session = await VoiceService.get_voice_session_by_id(db, session_id)
                if not voice_session:
                    await websocket.send_json({
                        "type": "error",
                        "message": "존재하지 않는 음성 세션입니다."
                    })
                    continue
                room_id = voice_session.room_id
                # user_id/guest_id를 명확하게 int/None으로 변환
                check_user_id = data.get("user_id")
                check_guest_id = data.get("guest_id")
                try:
                    check_user_id = int(check_user_id) if check_user_id is not None else None
                except Exception:
                    check_user_id = None
                try:
                    user_id_int = int(user_id) if user_id is not None else None
                except Exception:
                    user_id_int = None
                participant = None
                if check_user_id is not None:
                    participant = await RoomService.get_room_participant_by_room_id(
                        db=db,
                        room_id=room_id,
                        user_id=check_user_id,
                        guest_id=None
                    )
                elif check_guest_id is not None:
                    participant = await RoomService.get_room_participant_by_room_id(
                        db=db,
                        room_id=room_id,
                        user_id=None,
                        guest_id=check_guest_id
                    )
                elif user_id_int is not None:
                    participant = await RoomService.get_room_participant_by_room_id(
                        db=db,
                        room_id=room_id,
                        user_id=user_id_int,
                        guest_id=None
                    )
                if not participant or not participant.is_host:
                    print("❌ 방장 아님, next_page 거부")
                    await websocket.send_json({
                        "type": "error",
                        "message": "방장만 다음 페이지로 넘길 수 있습니다."
                    })
                    continue
                print("✅ 방장 확인, next_page 브로드캐스트 시작")
                await manager.broadcast_to_session(
                    session_id,
                    {"type": "next_page"}
                )
                print("✅ next_page 브로드캐스트 완료")
                # 방장 본인에게 안내 메시지 전송 -> 내 test 용이기도 함
                await websocket.send_json({
                    "type": "info",
                    "message": "next_page 신호를 보냈습니다."
                })
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