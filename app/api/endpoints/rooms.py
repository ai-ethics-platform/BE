from typing import Any, List, Union, Dict, Set, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_

from app import models, schemas
from app.core.deps import (
    get_db,
    get_current_user_or_guest,
    get_current_approved_user,
)
from app.services.room_service import room_service

router = APIRouter()

# 페이지 동기화 상태를 메모리에 저장 (간단한 딕셔너리)
# {room_code: {page_number: set(user_identifiers)}}
page_sync_status: Dict[str, Dict[int, Set[str]]] = {}


@router.post("/create/public", response_model=schemas.RoomCreateResponse)
async def create_public_room(
    room_data: schemas.RoomCreatePublic,
    db: AsyncSession = Depends(get_db),
    current_user: Union[models.User, dict] = Depends(get_current_approved_user)
) -> Any:
    """
    공개 방 생성
    - 공개 방을 새로 생성하며, 랜덤 배정 및 입장 코드 둘 다 사용 가능
    - 생성자가 자동으로 방에 입장됨
    """
    
    try:
        # 사용자 정보 추출
        print(f"[공개방] current_user 타입: {type(current_user)}")
        print(f"[공개방] current_user 값: {current_user}")
        
        if isinstance(current_user, models.User):
            creator_id = current_user.id
            creator_nickname = current_user.username
            print(f"[공개방] 일반 사용자: creator_id={creator_id}, creator_nickname={creator_nickname}")
        elif current_user is not None and isinstance(current_user, dict):  # 게스트 사용자
            creator_id = None
            creator_nickname = f"게스트_{current_user.get('guest_id', 'unknown')}"
            print(f"[공개방] 게스트 사용자: creator_id={creator_id}, creator_nickname={creator_nickname}")
        else:  # None인 경우
            print(f"[공개방] 인증 실패: current_user={current_user}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="인증이 필요합니다."
            )
        
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
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(get_current_approved_user)
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
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(get_current_approved_user)
) -> Any:
    """
    방 코드로 방 정보 조회
    """
    try:
        room = await room_service.get_room_by_code(db=db, room_code=room_code)
        if not room:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="존재하지 않는 방 코드입니다."
            )
        
        # 디버깅: participants의 role_id 값 확인
        print(f"🔍 방 코드 {room_code} 조회 결과:")
        print(f"   - 총 참가자 수: {len(room.participants)}")
        for i, participant in enumerate(room.participants):
            print(f"   - 참가자 {i+1}: {participant.nickname}, role_id={participant.role_id}, is_host={participant.is_host}")
        
        return room
    except HTTPException:
        raise
    except Exception as e:
        print(f"방 조회 중 예상치 못한 오류: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="방 조회 중 오류가 발생했습니다."
        )


@router.post("/join/code", response_model=schemas.RoomJoinResponse)
async def join_room_by_code(
    join_data: schemas.RoomJoinByCode,
    db: AsyncSession = Depends(get_db),
    current_user: Union[models.User, dict] = Depends(get_current_approved_user)
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
        elif current_user is not None:  # dict인 경우
            user_id = None
            guest_id = current_user.get('guest_id')
        else:  # None인 경우
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="인증이 필요합니다."
            )
        
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
    current_user: Union[models.User, dict] = Depends(get_current_approved_user)
) -> Any:
    """
    방 ID로 방 입장 (공개 방 목록에서 선택하여 입장)
    """
    try:
        # 사용자 정보 추출
        if isinstance(current_user, models.User):
            user_id = current_user.id
            guest_id = None
        elif current_user is not None:  # dict인 경우
            user_id = None
            guest_id = current_user.get('guest_id')
        else:  # None인 경우
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="인증이 필요합니다."
            )
        
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
    current_user: Union[models.User, dict] = Depends(get_current_approved_user)
) -> Any:
    """
    비공개 방 생성
    - 비공개 방을 새로 생성하며, 입장 코드 직접 생성 / 랜덤 생성 둘 다 사용 가능
    - 생성자가 자동으로 방에 입장됨
    """
    
    try:
        # 사용자 정보 추출
        print(f"🔍 [비공개방] current_user 타입: {type(current_user)}")
        print(f"🔍 [비공개방] current_user 값: {current_user}")
        
        if isinstance(current_user, models.User):
            creator_id = current_user.id
            creator_nickname = current_user.username
            print(f"🔍 [비공개방] 일반 사용자: creator_id={creator_id}, creator_nickname={creator_nickname}")
        elif current_user is not None and isinstance(current_user, dict):  # 게스트 사용자
            creator_id = None
            creator_nickname = f"게스트_{current_user.get('guest_id', 'unknown')}"
            print(f"🔍 [비공개방] 게스트 사용자: creator_id={creator_id}, creator_nickname={creator_nickname}")
        else:  # None인 경우
            print(f"🔍 [비공개방] 인증 실패: current_user={current_user}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="인증이 필요합니다."
            )
        
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
    current_user: Union[models.User, dict] = Depends(get_current_approved_user)
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
    current_user: Union[models.User, dict] = Depends(get_current_approved_user)
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
        elif current_user is not None:  # dict인 경우
            user_id = None
            guest_id = current_user.get('guest_id')
        else:  # None인 경우
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="인증이 필요합니다."
            )
        
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
    current_user: Union[models.User, dict] = Depends(get_current_user_or_guest)
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
        elif current_user is not None:  # dict인 경우
            user_id = None
            guest_id = current_user.get('guest_id')
        else:  # None인 경우
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="인증이 필요합니다."
            )
        
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
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(get_current_approved_user)
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


@router.get("/assign-roles/{room_code}", response_model=schemas.RoleAssignmentStatus)
async def get_role_assignment_status(
    room_code: str,
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(get_current_approved_user)
) -> Any:
    """
    방의 역할 배정 상태 조회
    - 모든 참가자에게 역할이 배정되었는지 확인
    - 역할 배정이 완료된 경우 배정 결과 반환
    """
    try:
        # 역할 배정 상태 조회
        status = await room_service.get_role_assignment_status(
            db=db,
            room_code=room_code
        )
        
        return status
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"역할 배정 상태 조회 중 오류가 발생했습니다: {str(e)}"
        )


@router.post("/ai-select", response_model=schemas.AiTypeSelectResponse)
async def set_ai_type(
    req: schemas.AiTypeSelectRequest,
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(get_current_approved_user)
):
    try:
        room = await room_service.set_ai_type(db, req.room_code, req.ai_type)
        return schemas.AiTypeSelectResponse(room_code=room.room_code, ai_type=room.ai_type)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/ai-select", response_model=schemas.AiTypeSelectResponse)
async def get_ai_type(
    room_code: str,
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(get_current_approved_user)
):
    try:
        ai_type = await room_service.get_ai_type(db, room_code)
        return schemas.AiTypeSelectResponse(room_code=room_code, ai_type=ai_type)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/ai-name", response_model=schemas.AiNameResponse)
async def set_ai_name(
    req: schemas.AiNameRequest,
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(get_current_approved_user)
):
    try:
        room = await room_service.set_ai_name(db, req.room_code, req.ai_name)
        return schemas.AiNameResponse(room_code=room.room_code, ai_name=room.ai_name)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/ai-name", response_model=schemas.AiNameResponse)
async def get_ai_name(
    room_code: str,
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(get_current_approved_user)
):
    try:
        ai_name = await room_service.get_ai_name(db, room_code)
        return schemas.AiNameResponse(room_code=room_code, ai_name=ai_name)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) 

# 라운드 선택 관련 API 엔드포인트들

@router.post("/rooms/round/{room_code}/choice", response_model=schemas.ChoiceSubmitResponse)
async def submit_round_choice(
    room_code: str,
    choice_data: schemas.RoundChoiceRequest,
    db: AsyncSession = Depends(get_db),
    current_user: Union[models.User, dict] = Depends(get_current_approved_user)
) -> Any:
    """
    라운드 개인 선택 제출 (round_number는 body로)
    """
    try:
        if isinstance(current_user, models.User):
            user_id = current_user.id
            guest_id = None
        elif current_user is not None:  # dict인 경우
            user_id = None
            guest_id = current_user.get('guest_id')
        else:  # None인 경우
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="인증이 필요합니다."
            )
        round_choice = await room_service.submit_round_choice(
            db=db,
            room_code=room_code,
            round_number=choice_data.round_number,
            choice=choice_data.choice,
            user_id=user_id,
            guest_id=guest_id,
            subtopic=choice_data.subtopic
        )
        return schemas.ChoiceSubmitResponse(
            room_code=room_code,
            round_number=choice_data.round_number,
            choice=choice_data.choice,
            message="개인 선택이 성공적으로 제출되었습니다."
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"선택 제출 중 오류가 발생했습니다: {str(e)}")

@router.post("/rooms/round/{room_code}/choice/confidence", response_model=schemas.ConfidenceSubmitResponse)
async def submit_individual_confidence(
    room_code: str,
    confidence_data: schemas.IndividualConfidenceRequest,
    db: AsyncSession = Depends(get_db),
    current_user: Union[models.User, dict] = Depends(get_current_approved_user)
) -> Any:
    """
    개별 확신도 제출 (round_number는 body로)
    """
    try:
        if isinstance(current_user, models.User):
            user_id = current_user.id
            guest_id = None
        elif current_user is not None:  # dict인 경우
            user_id = None
            guest_id = current_user.get('guest_id')
        else:  # None인 경우
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="인증이 필요합니다."
            )
        round_choice = await room_service.submit_individual_confidence(
            db=db,
            room_code=room_code,
            round_number=confidence_data.round_number,
            confidence=confidence_data.confidence,
            user_id=user_id,
            guest_id=guest_id,
            subtopic=confidence_data.subtopic
        )
        return schemas.ConfidenceSubmitResponse(
            room_code=room_code,
            round_number=confidence_data.round_number,
            confidence=confidence_data.confidence,
            message="개별 확신도가 성공적으로 제출되었습니다."
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"확신도 제출 중 오류가 발생했습니다: {str(e)}")

@router.post("/rooms/round/{room_code}/consensus", response_model=schemas.ConsensusSubmitResponse)
async def submit_consensus_choice(
    room_code: str,
    choice_data: schemas.ConsensusChoiceRequest,
    db: AsyncSession = Depends(get_db),
    current_user: Union[models.User, dict] = Depends(get_current_approved_user)
) -> Any:
    # 합의 선택 제출 (round_number는 body로)
    try:
        if isinstance(current_user, models.User):
            user_id = current_user.id
            guest_id = None
        elif current_user is not None: # dict 인 경우
            user_id = None
            guest_id = current_user.get('guest_id')
        else: # None인 경우
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="인증이 필요합니다."
            )
        consensus_choice = await room_service.submit_consensus_choice(
            db=db,
            room_code=room_code,
            round_number=choice_data.round_number,
            choice=choice_data.choice,
            user_id=user_id,
            guest_id=guest_id,
            subtopic=choice_data.subtopic
        )
        return schemas.ConsensusSubmitResponse(
            room_code=room_code,
            round_number=choice_data.round_number,
            choice=choice_data.choice,
            message="합의 선택이 성공적으로 제출되었습니다."
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"합의 선택 제출 중 오류가 발생했습니다: {str(e)}")

@router.post("/rooms/round/{room_code}/consensus/confidence", response_model=schemas.ConfidenceSubmitResponse)
async def submit_consensus_confidence(
    room_code: str,
    confidence_data: schemas.ConsensusConfidenceRequest,
    db: AsyncSession = Depends(get_db),
    current_user: Union[models.User, dict] = Depends(get_current_approved_user)
) -> Any:
    """
    합의 선택에 대한 확신도 제출 (round_number는 body로)
    """
    try:
        if isinstance(current_user, models.User):
            user_id = current_user.id
            guest_id = None
        elif current_user is not None:  # dict인 경우
            user_id = None
            guest_id = current_user.get('guest_id')
        else:  # None인 경우
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="인증이 필요합니다."
            )
        consensus_choice = await room_service.submit_consensus_confidence(
            db=db,
            room_code=room_code,
            round_number=confidence_data.round_number,
            confidence=confidence_data.confidence,
            user_id=user_id,
            guest_id=guest_id,
            subtopic=confidence_data.subtopic
        )
        return schemas.ConfidenceSubmitResponse(
            room_code=room_code,
            round_number=confidence_data.round_number,
            confidence=confidence_data.confidence,
            message="합의 선택에 대한 확신도가 성공적으로 제출되었습니다."
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"확신도 제출 중 오류가 발생했습니다: {str(e)}")


@router.get("/{room_code}/rounds/{round_number}/status", response_model=schemas.ChoiceStatusResponse)
async def get_choice_status(
    room_code: str,
    round_number: int,
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(get_current_approved_user)
) -> Any:
    """
    라운드별 선택 상태 조회
    - 각 참가자의 선택 완료 현황과 합의 선택 완료 여부를 조회
    - 실시간으로 상태를 확인할 수 있음
    """
    try:
        status = await room_service.get_choice_status(
            db=db,
            room_code=room_code,
            round_number=round_number
        )
        return status
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"선택 현황 조회 중 오류가 발생했습니다: {str(e)}"
        ) 

@router.get("/websocket/stats")
async def get_websocket_stats():
    """WebSocket 연결 상태 통계 조회"""
    from app.core.websocket_manager import websocket_manager
    
    stats = websocket_manager.get_all_stats()
    total_sessions = len(stats)
    total_connections = sum(session_stats["current_connections"] for session_stats in stats.values())
    
    return {
        "total_sessions": total_sessions,
        "total_connections": total_connections,
        "sessions": stats
    }

@router.get("/websocket/stats/{session_id}")
async def get_session_websocket_stats(session_id: str):
    """특정 세션의 WebSocket 연결 상태 조회"""
    from app.core.websocket_manager import websocket_manager
    
    stats = websocket_manager.get_connection_stats(session_id)
    if not stats:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="해당 세션을 찾을 수 없습니다."
        )
    
    return stats 

@router.get("/websocket/health/{session_id}")
async def get_websocket_health(session_id: str):
    """특정 세션의 WebSocket 연결 상태 상세 조회"""
    from app.core.websocket_manager import websocket_manager
    
    stats = websocket_manager.get_connection_stats(session_id)
    health = websocket_manager.get_connection_health(session_id)
    
    if not stats:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="해당 세션을 찾을 수 없습니다."
        )
    
    return {
        "session_id": session_id,
        "stats": stats,
        "health": health,
        "active_connections": len(websocket_manager.get_session_participants(session_id))
    }

@router.post("/websocket/ping/{session_id}")
async def ping_websocket_connections(session_id: str):
    """특정 세션의 WebSocket 연결 상태 확인"""
    from app.core.websocket_manager import websocket_manager
    
    await websocket_manager.ping_connections(session_id)
    
    return {
        "message": f"세션 {session_id}의 연결 상태 확인 완료",
        "active_connections": len(websocket_manager.get_session_participants(session_id))
    } 

# 페이지 동기화 관련 새로운 엔드포인트들
@router.post("/page-arrival", response_model=schemas.room.PageArrivalResponse)
async def record_page_arrival(
    arrival_data: schemas.room.PageArrivalRequest,
    db: AsyncSession = Depends(get_db),
    current_user: Union[models.User, dict] = Depends(get_current_approved_user)
) -> Any:
    """
    사용자가 특정 페이지에 도착했음을 기록
    - 프론트엔드에서 페이지 전환 시 호출
    - 3명 모두 도착하면 all_arrived = True 반환
    """
    try:
        # 사용자 식별자 (요청에서 받음)
        user_identifier = arrival_data.user_identifier
        
        # 방 정보 조회하여 총 사용자 수 확인
        room = await room_service.get_room_by_code(db=db, room_code=arrival_data.room_code)
        if not room:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="존재하지 않는 방 코드입니다."
            )
        
        total_users = room.current_players
        
        # 메모리에 페이지 도착 기록
        if arrival_data.room_code not in page_sync_status:
            page_sync_status[arrival_data.room_code] = {}
        
        if arrival_data.page_number not in page_sync_status[arrival_data.room_code]:
            page_sync_status[arrival_data.room_code][arrival_data.page_number] = set()
        
        page_sync_status[arrival_data.room_code][arrival_data.page_number].add(user_identifier)
        arrived_count = len(page_sync_status[arrival_data.room_code][arrival_data.page_number])
        
        # 모든 사용자가 도착했는지 확인
        all_arrived = arrived_count >= total_users
        
        return schemas.room.PageArrivalResponse(
            room_code=arrival_data.room_code,
            page_number=arrival_data.page_number,
            arrived_users=arrived_count,
            total_required=total_users,
            all_arrived=all_arrived,
            message=f"페이지 {arrival_data.page_number}에 도착이 기록되었습니다. ({arrived_count}/{total_users})"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"페이지 도착 기록 중 오류가 발생했습니다: {str(e)}"
        )


@router.get("/page-sync-status/{room_code}/{page_number}", response_model=schemas.room.PageSyncStatus)
async def get_page_sync_status(
    room_code: str,
    page_number: int,
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(get_current_approved_user)
) -> Any:
    """
    특정 방과 페이지의 동기화 상태 조회
    - 프론트엔드에서 현재 동기화 상태를 확인할 때 사용
    """
    try:
        # 방 정보 조회
        room = await room_service.get_room_by_code(db=db, room_code=room_code)
        if not room:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="존재하지 않는 방 코드입니다."
            )
        
        # 메모리에서 동기화 상태 조회
        if room_code not in page_sync_status or page_number not in page_sync_status[room_code]:
            # 아직 아무도 도착하지 않음
            return schemas.room.PageSyncStatus(
                room_code=room_code,
                page_number=page_number,
                arrived_users=0,
                total_required=room.current_players,
                all_arrived=False,
                can_proceed=False,
                arrived_user_list=[]
            )
        
        arrived_users = len(page_sync_status[room_code][page_number])
        total_users = room.current_players
        all_arrived = arrived_users >= total_users
        
        return schemas.room.PageSyncStatus(
            room_code=room_code,
            page_number=page_number,
            arrived_users=arrived_users,
            total_required=total_users,
            all_arrived=all_arrived,
            can_proceed=all_arrived,
            arrived_user_list=list(page_sync_status[room_code][page_number])
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"페이지 동기화 상태 조회 중 오류가 발생했습니다: {str(e)}"
        )


@router.post("/page-sync-reset/{room_code}/{page_number}", response_model=schemas.room.PageSyncResponse)
async def reset_page_sync_status(
    room_code: str,
    page_number: int,
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(get_current_approved_user)
) -> Any:
    """
    특정 방과 페이지의 동기화 상태 초기화
    - 새로운 페이지로 이동하기 전에 이전 페이지 상태를 초기화할 때 사용
    """
    try:
        # 방 존재 여부 확인
        room = await room_service.get_room_by_code(db=db, room_code=room_code)
        if not room:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="존재하지 않는 방 코드입니다."
            )
        
        # 메모리에서 동기화 상태 초기화
        if room_code in page_sync_status and page_number in page_sync_status[room_code]:
            del page_sync_status[room_code][page_number]
            print(f"🔄 페이지 동기화 상태 초기화: 방 {room_code}, 페이지 {page_number}")
        
        return schemas.room.PageSyncResponse(
            room_code=room_code,
            page_number=page_number,
            sync_signal="reset",
            message=f"페이지 {page_number}의 동기화 상태가 초기화되었습니다."
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"페이지 동기화 상태 초기화 중 오류가 발생했습니다: {str(e)}"
        )


@router.post("/page-sync-manual/{room_code}/{page_number}", response_model=schemas.room.PageSyncResponse)
async def manual_page_sync_signal(
    room_code: str,
    page_number: int,
    signal_type: str = "three_next",
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(get_current_approved_user)
) -> Any:
    """
    수동으로 페이지 동기화 신호 전송
    - 프론트엔드에서 강제로 동기화 신호를 보내고 싶을 때 사용
    """
    try:
        # 방 존재 여부 확인
        room = await room_service.get_room_by_code(db=db, room_code=room_code)
        if not room:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="존재하지 않는 방 코드입니다."
            )
        
        # 메모리 기반으로 단순 응답만 반환 (WebSocket 신호 전송 없음)
        print(f"📡 수동 페이지 동기화 신호: 방 {room_code}, 페이지 {page_number}, 신호: {signal_type}")
        
        return schemas.room.PageSyncResponse(
            room_code=room_code,
            page_number=page_number,
            sync_signal=signal_type,
            message=f"페이지 {page_number}에 {signal_type} 신호가 수동으로 전송되었습니다."
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"수동 동기화 신호 전송 중 오류가 발생했습니다: {str(e)}"
        ) 

@router.get("/rooms/statistics", response_model=schemas.StatisticsResponse)
async def get_statistics(
    exclude_dummy: bool = Query(True, description="더미 데이터 제외 여부"),
    from_dt: Optional[str] = Query(None, description="시작 시각(ISO-8601)"),
    to_dt: Optional[str] = Query(None, description="종료 시각(ISO-8601)"),
    ai_type: Optional[int] = Query(None, description="AI 타입(1|2|3)"),
    is_public: Optional[bool] = Query(None, description="공개 여부"),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """
    모든 서브토픽에 대한 통계 조회
    - 각 서브토픽별 choice 1, 2의 비율을 반환
    - exclude_dummy=True면 더미 데이터 제외, False면 모든 데이터 포함
    """
    try:
        from datetime import datetime
        parse = lambda s: datetime.fromisoformat(s.replace("Z", "+00:00")) if s else None
        result = await room_service.get_statistics(
            db=db,
            exclude_dummy=exclude_dummy,
            from_dt=parse(from_dt),
            to_dt=parse(to_dt),
            ai_type=ai_type,
            is_public=is_public,
        )
        
        return schemas.StatisticsResponse(
            statistics=result["statistics"],
            total_rooms=result["total_rooms"],
            total_participants=result["total_participants"],
            message="통계 조회 성공"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"통계 조회 중 오류가 발생했습니다: {str(e)}"
        ) 

@router.get("/rooms/statistics/subtopic/{subtopic}")
async def get_statistics_by_subtopic(
    subtopic: str,
    exclude_dummy: bool = Query(True, description="더미 데이터 제외 여부"),
    from_dt: Optional[str] = Query(None, description="시작 시각(ISO-8601)"),
    to_dt: Optional[str] = Query(None, description="종료 시각(ISO-8601)"),
    ai_type: Optional[int] = Query(None, description="AI 타입(1|2|3)"),
    is_public: Optional[bool] = Query(None, description="공개 여부"),
    db: AsyncSession = Depends(get_db)
) -> Any:
    try:
        from datetime import datetime
        parse = lambda s: datetime.fromisoformat(s.replace("Z", "+00:00")) if s else None
        stat = await room_service.get_statistics_for_subtopic(
            db=db,
            subtopic=subtopic,
            exclude_dummy=exclude_dummy,
            from_dt=parse(from_dt),
            to_dt=parse(to_dt),
            ai_type=ai_type,
            is_public=is_public,
        )
        return stat
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"통계 조회 중 오류가 발생했습니다: {str(e)}"
        )

@router.get("/rooms/statistics/subtopics")
async def list_statistics_subtopics(
    exclude_dummy: bool = Query(True, description="더미 데이터 제외 여부"),
    from_dt: Optional[str] = Query(None, description="시작 시각(ISO-8601)"),
    to_dt: Optional[str] = Query(None, description="종료 시각(ISO-8601)"),
    ai_type: Optional[int] = Query(None, description="AI 타입(1|2|3)"),
    is_public: Optional[bool] = Query(None, description="공개 여부"),
    db: AsyncSession = Depends(get_db)
) -> Any:
    try:
        from datetime import datetime
        parse = lambda s: datetime.fromisoformat(s.replace("Z", "+00:00")) if s else None
        items = await room_service.list_subtopics(
            db=db,
            exclude_dummy=exclude_dummy,
            from_dt=parse(from_dt),
            to_dt=parse(to_dt),
            ai_type=ai_type,
            is_public=is_public,
        )
        return {"subtopics": items, "count": len(items)}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"통계 서브토픽 조회 중 오류가 발생했습니다: {str(e)}"
        )
