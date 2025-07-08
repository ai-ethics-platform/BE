from typing import Any, List, Union
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_

from app import models, schemas
from app.api import deps
from app.services.room_service import room_service
from app.core.deps import get_db

router = APIRouter()


@router.post("/create/public", response_model=schemas.RoomCreateResponse)
async def create_public_room(
    room_data: schemas.RoomCreatePublic,
    db: AsyncSession = Depends(get_db),
    current_user: Union[models.User, dict] = Depends(deps.get_current_user_or_guest)
) -> Any:
    """
    공개 방 생성
    - 공개 방을 새로 생성하며, 랜덤 배정 및 입장 코드 둘 다 사용 가능
    - 생성자가 자동으로 방에 입장됨
    """
    
    try:
        # 사용자 정보 추출
        if isinstance(current_user, models.User):
            creator_id = current_user.id
            creator_nickname = current_user.username
        else:
            # 게스트 사용자
            creator_id = None
            creator_nickname = f"게스트_{current_user.get('guest_id', 'unknown')}"
        
        # 방 생성
        room = await room_service.create_public_room(
            db=db,
            room_data=room_data,
            creator_id=creator_id,
            creator_nickname=creator_nickname
        )
        
        return schemas.RoomCreateResponse(
            room=room,
            message="공개 방이 성공적으로 생성되었습니다."
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"방 생성 중 오류가 발생했습니다: {str(e)}"
        )


@router.get("/public", response_model=List[schemas.RoomSummary])
async def get_public_rooms(
    skip: int = 0,
    limit: int = 20,
    db: AsyncSession = Depends(get_db)
) -> Any:
    """
    공개 방 목록 조회
    - 활성화되고 시작되지 않은 공개 방들을 조회
    - 입장 가능한 방들만 표시 (자리가 남아있는 방)
    """
    try:
        # 입장 가능한 공개 방 목록 조회
        rooms = await room_service.get_available_rooms_for_random_join(db=db)
        
        # 페이지네이션 적용
        start_idx = skip
        end_idx = skip + limit
        paginated_rooms = rooms[start_idx:end_idx]
        
        return paginated_rooms
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"방 목록 조회 중 오류가 발생했습니다: {str(e)}"
        )


@router.get("/code/{room_code}", response_model=schemas.Room)
async def get_room_by_code(
    room_code: str,
    db: AsyncSession = Depends(get_db)
) -> Any:
    """
    방 코드로 방 정보 조회
    """
    room = await room_service.get_room_by_code(db=db, room_code=room_code)
    if not room:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="존재하지 않는 방 코드입니다."
        )
    return room


@router.post("/join/code", response_model=schemas.RoomJoinResponse)
async def join_room_by_code(
    join_data: schemas.RoomJoinByCode,
    db: AsyncSession = Depends(get_db),
    current_user: Union[models.User, dict] = Depends(deps.get_current_user_or_guest)
) -> Any:
    """
    방 코드로 방 입장
    """
    try:
        # 방 코드로 방 찾기
        room = await room_service.get_room_by_code(db=db, room_code=join_data.room_code)
        if not room:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="존재하지 않는 방 코드입니다."
            )
        
        # 사용자 정보 추출
        if isinstance(current_user, models.User):
            user_id = current_user.id
            guest_id = None
        else:
            # 게스트 사용자
            user_id = None
            guest_id = current_user.get('guest_id')
        
        participant = await room_service.join_room(
            db=db,
            room_id=room.id,
            user_id=user_id,
            guest_id=guest_id,
            nickname=join_data.nickname
        )
        
        # 업데이트된 방 정보 조회 (참가자 포함)
        updated_room = await room_service.get_room_by_code(db=db, room_code=join_data.room_code)
        
        return schemas.RoomJoinResponse(
            participant=participant,
            room=updated_room,
            message=f"'{updated_room.title}' 방에 성공적으로 입장했습니다."
        )
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"방 입장 중 오류가 발생했습니다: {str(e)}"
        )


@router.post("/join/{room_id}", response_model=schemas.RoomJoinResponse)
async def join_room_by_id(
    room_id: int,
    join_data: schemas.RoomJoinRequest,
    db: AsyncSession = Depends(get_db),
    current_user: Union[models.User, dict] = Depends(deps.get_current_user_or_guest)
) -> Any:
    """
    방 ID로 방 입장 (공개 방 목록에서 선택하여 입장)
    """
    try:
        # 사용자 정보 추출
        if isinstance(current_user, models.User):
            user_id = current_user.id
            guest_id = None
        else:
            # 게스트 사용자
            user_id = None
            guest_id = current_user.get('guest_id')
        
        participant = await room_service.join_room(
            db=db,
            room_id=room_id,
            user_id=user_id,
            guest_id=guest_id,
            nickname=join_data.nickname
        )
        
        # 방 정보 조회 (참가자 포함)
        room = await db.get(models.Room, room_id)
        room_with_participants = await room_service.get_room_by_code(db=db, room_code=room.room_code)
        
        return schemas.RoomJoinResponse(
            participant=participant,
            room=room_with_participants,
            message=f"'{room_with_participants.title}' 방에 성공적으로 입장했습니다."
        )
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"방 입장 중 오류가 발생했습니다: {str(e)}"
        )


@router.post("/create/private", response_model=schemas.RoomCreateResponse)
async def create_private_room(
    room_data: schemas.RoomCreatePrivate,
    db: AsyncSession = Depends(get_db),
    current_user: Union[models.User, dict] = Depends(deps.get_current_user_or_guest)
) -> Any:
    """
    비공개 방 생성
    - 비공개 방을 새로 생성하며, 입장 코드 직접 생성 / 랜덤 생성 둘 다 사용 가능
    - 생성자가 자동으로 방에 입장됨
    """
    
    try:
        # 사용자 정보 추출
        if isinstance(current_user, models.User):
            creator_id = current_user.id
            creator_nickname = current_user.username
        else:
            # 게스트 사용자
            creator_id = None
            creator_nickname = f"게스트_{current_user.get('guest_id', 'unknown')}"
        
        # 방 생성
        room = await room_service.create_private_room(
            db=db,
            room_data=room_data,
            creator_id=creator_id,
            creator_nickname=creator_nickname
        )
        
        return schemas.RoomCreateResponse(
            room=room,
            message="비공개 방이 성공적으로 생성되었습니다."
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"방 생성 중 오류가 발생했습니다: {str(e)}"
        )


@router.get("/private", response_model=List[schemas.RoomSummary])
async def get_private_rooms(
    skip: int = 0,
    limit: int = 20,
    db: AsyncSession = Depends(get_db),
    current_user: Union[models.User, dict] = Depends(deps.get_current_user_or_guest)
) -> Any:
    """
    비공개 방 목록 조회
    - 본인이 생성한 비공개 방들만 조회 가능
    - 게스트 사용자는 조회 불가
    """
    try:
        # 사용자 정보 추출
        if isinstance(current_user, models.User):
            user_id = current_user.id
        else:
            # 게스트는 비공개 방 목록 조회 불가
            return []
        
        rooms = await room_service.get_private_rooms(db=db, user_id=user_id, skip=skip, limit=limit)
        return rooms
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"방 목록 조회 중 오류가 발생했습니다: {str(e)}"
        )


@router.post("/ready", response_model=schemas.RoomReadyResponse)
async def toggle_ready_status(
    ready_data: schemas.RoomReadyRequest,
    db: AsyncSession = Depends(get_db),
    current_user: Union[models.User, dict] = Depends(deps.get_current_user_or_guest)
) -> Any:
    """
    준비 상태 토글
    - 사용자의 준비 상태를 변경합니다
    - 3명이 모두 준비되면 3초 후 게임 시작이 예약됩니다
    """
    try:
        # 사용자 정보 추출
        if isinstance(current_user, models.User):
            user_id = current_user.id
            guest_id = None
        else:
            # 게스트 사용자
            user_id = None
            guest_id = current_user.get('guest_id')
        
        participant, room, game_starting, start_time = await room_service.toggle_ready_status(
            db=db,
            room_code=ready_data.room_code,
            user_id=user_id,
            guest_id=guest_id
        )
        
        # 응답 메시지 생성
        if game_starting:
            message = "모든 플레이어가 준비되었습니다! 3초 후 게임이 시작됩니다."
        elif participant.is_ready:
            message = "준비 완료! 다른 플레이어들을 기다리고 있습니다."
        else:
            message = "준비를 취소했습니다."
        
        return schemas.RoomReadyResponse(
            participant=participant,
            room=room,
            game_starting=game_starting,
            start_time=start_time,
            message=message
        )
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"준비 상태 변경 중 오류가 발생했습니다: {str(e)}"
        )


@router.post("/reset", response_model=schemas.RoomResetResponse)
async def reset_room_status(
    reset_data: schemas.RoomResetRequest,
    db: AsyncSession = Depends(get_db)
) -> Any:
    """
    방 상태 초기화 (테스트용)
    - is_started를 false로 변경
    - start_time을 null로 변경
    - 모든 참가자의 is_ready를 false로 변경
    """
    try:
        room = await room_service.reset_room_status(
            db=db,
            room_code=reset_data.room_code
        )
        
        return schemas.RoomResetResponse(
            room=room,
            message="방 상태가 초기화되었습니다. 이제 준비 버튼을 테스트할 수 있습니다!"
        )
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"방 상태 초기화 중 오류가 발생했습니다: {str(e)}"
        )


@router.post("/out", response_model=schemas.RoomLeaveResponse)
async def leave_room(
    leave_data: schemas.RoomLeaveRequest,
    db: AsyncSession = Depends(get_db),
    current_user: Union[models.User, dict] = Depends(deps.get_current_user_or_guest)
) -> Any:
    """
    방 나가기
    - 사용자가 방에서 나감
    - 방 참가자 수 감소
    - 마지막 사람이 나가면 방 비활성화
    """
    try:
        # 사용자 정보 추출
        if isinstance(current_user, models.User):
            user_id = current_user.id
            guest_id = None
        else:
            # 게스트 사용자
            user_id = None
            guest_id = current_user.get('guest_id')
        
        room_code, remaining_players, room_deleted, new_host_info, game_started = await room_service.leave_room(
            db=db,
            room_code=leave_data.room_code,
            user_id=user_id,
            guest_id=guest_id
        )
        
        # 응답 메시지 및 리다이렉트 여부 결정
        requires_lobby_redirect = False
        
        if room_deleted:
            if game_started:
                message = "모든 플레이어가 퇴장했습니다. 게임이 중단됩니다."
                requires_lobby_redirect = True
            else:
                message = "방에서 나갔습니다. 방에 아무도 없어서 방이 비활성화되었습니다."
        elif new_host_info:
            message = f"방에서 나갔습니다. {new_host_info['nickname']}님이 새로운 방장이 되었습니다."
        else:
            message = f"방에서 나갔습니다. 남은 플레이어: {remaining_players}명"
            
            # TODO: remaining_players == 1이고 game_started인 경우
            # WebSocket으로 남은 1명에게 "혼자 남았다" 알림 전송
            # 예시: if remaining_players == 1 and game_started:
            #     await websocket_manager.broadcast_to_room(room_code, {
            #         "type": "game_interrupted", 
            #         "message": "모든 플레이어가 퇴장했습니다. 게임이 중단됩니다.",
            #         "requires_lobby_redirect": true
            #     })
        
        return schemas.RoomLeaveResponse(
            room_code=room_code,
            player_count=remaining_players,
            room_deleted=room_deleted,
            new_host=new_host_info,
            game_started=game_started,
            requires_lobby_redirect=requires_lobby_redirect,
            message=message
        )
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"방 나가기 중 오류가 발생했습니다: {str(e)}"
        )


@router.post("/assign-roles/{room_code}", response_model=schemas.RoleAssignmentResult)
async def assign_roles(
    room_code: str,
    db: AsyncSession = Depends(get_db)
) -> Any:
    """
    역할 랜덤 배정
    - 방의 모든 참가자에게 역할을 랜덤하게 배정
    - 3명의 참가자가 모두 있어야 함
    - 역할 ID: 1(요양보호사), 2(가족), 3(AI 개발자) : 이건 바뀔 수도 있음
    """
    try:
        # 역할 배정 실행
        assignments = await room_service.assign_roles(
            db=db,
            room_code=room_code
        )
        
        return schemas.RoleAssignmentResult(
            assignments=assignments,
            message="역할이 성공적으로 배정되었습니다."
        )
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"역할 배정 중 오류가 발생했습니다: {str(e)}"
        )


@router.post("/ai-select", response_model=schemas.AiTypeSelectResponse)
async def set_ai_type(
    req: schemas.AiTypeSelectRequest,
    db: AsyncSession = Depends(get_db)
):
    try:
        room = await room_service.set_ai_type(db, req.room_code, req.ai_type)
        return schemas.AiTypeSelectResponse(room_code=room.room_code, ai_type=room.ai_type)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/ai-select", response_model=schemas.AiTypeSelectResponse)
async def get_ai_type(
    room_code: str,
    db: AsyncSession = Depends(get_db)
):
    try:
        ai_type = await room_service.get_ai_type(db, room_code)
        return schemas.AiTypeSelectResponse(room_code=room_code, ai_type=ai_type)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/ai-name", response_model=schemas.AiNameResponse)
async def set_ai_name(
    req: schemas.AiNameRequest,
    db: AsyncSession = Depends(get_db)
):
    try:
        room = await room_service.set_ai_name(db, req.room_code, req.ai_name)
        return schemas.AiNameResponse(room_code=room.room_code, ai_name=room.ai_name)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/ai-name", response_model=schemas.AiNameResponse)
async def get_ai_name(
    room_code: str,
    db: AsyncSession = Depends(get_db)
):
    try:
        ai_name = await room_service.get_ai_name(db, room_code)
        return schemas.AiNameResponse(room_code=room_code, ai_name=ai_name)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) 
