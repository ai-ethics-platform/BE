from typing import Any, Union
from fastapi import APIRouter, Depends, HTTPException, status, WebSocket, WebSocketDisconnect
from sqlalchemy.ext.asyncio import AsyncSession
import json

from app import models, schemas
from app.core.deps import get_db, get_current_user_or_guest
from app.services.voice_service import VoiceService
from app.core.websocket_manager import websocket_manager

router = APIRouter()


@router.post("/sessions", response_model=schemas.VoiceSession)
async def create_voice_session(
    session_data: schemas.VoiceSessionCreate,
    db: AsyncSession = Depends(get_db),
    current_user: Union[models.User, dict] = Depends(get_current_user_or_guest)
) -> Any:
    """음성 세션 생성 또는 기존 세션 조회"""
    try:
        # 사용자 정보 추출
        user_id = current_user.id if isinstance(current_user, models.User) else None
        nickname = current_user.nickname if isinstance(current_user, models.User) else current_user.get("nickname", "게스트")
        
        # 1. 방 코드로 기존 음성 세션이 있는지 확인
        existing_session = await VoiceService.get_voice_session_by_room_code(
            db=db, room_code=session_data.room_code
        )
        
        if existing_session:
            # 기존 세션이 있으면 그 세션 반환
            print(f"✅ 기존 음성 세션 발견: {existing_session.session_id}")
            return existing_session
        else:
            # 없으면 새로 생성
            print(f"🆕 새 음성 세션 생성: {session_data.room_code}")
            voice_session = await VoiceService.create_voice_session(
                db=db,
                room_code=session_data.room_code,
                creator_id=user_id,
                creator_nickname=nickname
            )
            return voice_session
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"음성 세션 생성 중 오류가 발생했습니다: {str(e)}"
        )


@router.get("/sessions/room/{room_code}", response_model=schemas.VoiceSession)
async def get_voice_session_by_room_code(
    room_code: str,
    db: AsyncSession = Depends(get_db)
) -> Any:
    """방 코드로 음성 세션 조회"""
    try:
        voice_session = await VoiceService.get_voice_session_by_room_code(
            db=db, room_code=room_code
        )
        
        if not voice_session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="해당 방의 음성 세션이 없습니다."
            )
        
        return voice_session
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"음성 세션 조회 중 오류가 발생했습니다: {str(e)}"
        )


@router.get("/sessions/{session_id}", response_model=schemas.VoiceSession)
async def get_voice_session_by_id(
    session_id: str,
    db: AsyncSession = Depends(get_db)
) -> Any:
    """세션 ID로 음성 세션 조회"""
    try:
        voice_session = await VoiceService.get_voice_session_by_id(
            db=db, session_id=session_id
        )
        
        if not voice_session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="존재하지 않는 음성 세션입니다."
            )
        
        return voice_session
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"음성 세션 조회 중 오류가 발생했습니다: {str(e)}"
        )


@router.post("/sessions/{session_id}/join", response_model=schemas.VoiceJoinResponse)
async def join_voice_session(
    session_id: str,
    join_data: schemas.VoiceJoinRequest,
    db: AsyncSession = Depends(get_db),
    current_user: Union[models.User, dict] = Depends(get_current_user_or_guest)
) -> Any:
    """음성 세션 참가"""
    try:
        # 사용자 정보 추출
        user_id = current_user.id if isinstance(current_user, models.User) else None
        guest_id = None if isinstance(current_user, models.User) else current_user.get("guest_id")
        
        participant = await VoiceService.join_voice_session(
            db=db,
            session_id=session_id,
            user_id=user_id,
            guest_id=guest_id,
            nickname=join_data.nickname
        )
        
        # 세션 정보 조회
        voice_session = await VoiceService.get_voice_session_by_id(db=db, session_id=session_id)
        
        return schemas.VoiceJoinResponse(
            session=voice_session,
            participant=participant,
            message="음성 세션에 참가했습니다."
        )
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"음성 세션 참가 중 오류가 발생했습니다: {str(e)}"
        )


@router.post("/sessions/{session_id}/status", response_model=schemas.VoiceStatusResponse)
async def update_voice_status(
    session_id: str,
    status_data: schemas.VoiceStatusUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: Union[models.User, dict] = Depends(get_current_user_or_guest)
) -> Any:
    """음성 상태 업데이트 (마이크 ON/OFF)"""
    try:
        # 사용자 정보 추출
        user_id = current_user.id if isinstance(current_user, models.User) else None
        guest_id = None if isinstance(current_user, models.User) else current_user.get("guest_id")
        
        participant = await VoiceService.update_voice_status(
            db=db,
            session_id=session_id,
            user_id=user_id,
            guest_id=guest_id,
            is_mic_on=status_data.is_mic_on,
            is_speaking=status_data.is_speaking
        )
        
        # WebSocket으로 상태 변경 브로드캐스트
        await websocket_manager.broadcast_voice_status(session_id, participant)
        
        return schemas.VoiceStatusResponse(
            participant=participant,
            message="음성 상태가 업데이트되었습니다."
        )
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"음성 상태 업데이트 중 오류가 발생했습니다: {str(e)}"
        )


@router.post("/sessions/{session_id}/leave", response_model=schemas.VoiceLeaveResponse)
async def leave_voice_session(
    session_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: Union[models.User, dict] = Depends(get_current_user_or_guest)
) -> Any:
    """음성 세션 퇴장"""
    try:
        # 사용자 정보 추출
        user_id = current_user.id if isinstance(current_user, models.User) else None
        guest_id = None if isinstance(current_user, models.User) else current_user.get("guest_id")
        
        await VoiceService.leave_voice_session(
            db=db,
            session_id=session_id,
            user_id=user_id,
            guest_id=guest_id
        )
        
        return schemas.VoiceLeaveResponse(
            session_id=session_id,
            message="음성 세션에서 퇴장했습니다."
        )
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"음성 세션 퇴장 중 오류가 발생했습니다: {str(e)}"
        )


@router.websocket("/ws/voice/{session_id}")
async def websocket_endpoint(websocket: WebSocket, session_id: str):
    """WebSocket 연결 - 음성 세션 실시간 통신"""
    await websocket_manager.connect(websocket, session_id)
    try:
        while True:
            # 메시지 수신
            data = await websocket.receive_text()
            message = json.loads(data)
            
            # 메시지 타입에 따른 처리
            mtype = message.get("type")
            
            if mtype == "init":
                # 초기화 메시지
                user_id = message.get("user_id")
                guest_id = message.get("guest_id")
                nickname = message.get("nickname", "게스트")
                
                # WebSocket 매니저에 사용자 정보 등록
                await websocket_manager.register_user(websocket, session_id, user_id, guest_id, nickname)
                
                # 연결 확인 응답
                await websocket.send_json({
                    "type": "init_response",
                    "status": "connected",
                    "session_id": session_id
                })
                
            elif mtype == "voice_status":
                # 음성 상태 변경
                is_mic_on = message.get("is_mic_on", False)
                is_speaking = message.get("is_speaking", False)
                
                # 다른 참가자들에게 브로드캐스트
                await websocket_manager.broadcast_to_session(session_id, {
                    "type": "voice_status_update",
                    "user_id": message.get("user_id"),
                    "guest_id": message.get("guest_id"),
                    "nickname": message.get("nickname"),
                    "is_mic_on": is_mic_on,
                    "is_speaking": is_speaking
                })
                
            elif mtype == "next_page":
                # 다음 페이지 요청 (방장만 가능)
                user_id = message.get("user_id")
                guest_id = message.get("guest_id")
                
                # 방장 권한 확인
                is_host = await websocket_manager.is_host(session_id, user_id, guest_id)
                if not is_host:
                    await websocket.send_json({
                        "type": "error",
                        "message": "방장만 다음 페이지로 이동할 수 있습니다."
                    })
                    continue
                
                # 모든 참가자에게 next_page 브로드캐스트
                await websocket_manager.broadcast_to_session(session_id, {
                    "type": "next_page"
                })
                
                # 방장에게만 추가 정보 전송
                await websocket.send_json({
                    "type": "info",
                    "message": "다음 페이지로 이동했습니다."
                })
                
            elif mtype == "chat_message":
                # 채팅 메시지
                await websocket_manager.broadcast_to_session(session_id, {
                    "type": "chat_message",
                    "user_id": message.get("user_id"),
                    "guest_id": message.get("guest_id"),
                    "nickname": message.get("nickname"),
                    "message": message.get("message")
                })
                
            else:
                # 알 수 없는 메시지 타입
                await websocket.send_json({
                    "type": "error",
                    "message": f"알 수 없는 메시지 타입: {mtype}"
                })
                
    except WebSocketDisconnect:
        # 연결 해제 처리
        await websocket_manager.disconnect(websocket, session_id)
    except Exception as e:
        # 오류 처리
        print(f"WebSocket 오류: {str(e)}")
        await websocket_manager.disconnect(websocket, session_id) 