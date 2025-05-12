from typing import Any, List, Optional

from fastapi import APIRouter, Depends, HTTPException, status, WebSocket, WebSocketDisconnect
from sqlalchemy.ext.asyncio import AsyncSession

from app import models, schemas
from app.api import deps
from app.services import game_service, room_service
from app.core.websocket import ConnectionManager

router = APIRouter()
manager = ConnectionManager()


@router.post("/rooms", response_model=schemas.Room)
async def create_room(
    room_in: schemas.RoomCreate,
    current_user: models.User = Depends(deps.get_current_user),
) -> Any:
    """
    새로운 게임 방 생성
    """
    room = await room_service.create_room(
        creator_id=current_user.id,
        room_in=room_in
    )
    return room


@router.get("/rooms", response_model=List[schemas.Room])
async def list_rooms(
    skip: int = 0,
    limit: int = 100,
    current_user: models.User = Depends(deps.get_current_user),
) -> Any:
    """
    공개 방 목록 조회
    """
    rooms = await room_service.get_public_rooms(skip=skip, limit=limit)
    return rooms


@router.post("/rooms/join", response_model=schemas.Room)
async def join_room(
    join_data: schemas.RoomJoin,
    current_user: models.User = Depends(deps.get_current_user),
) -> Any:
    """
    방 입장 코드로 방 입장
    """
    room = await room_service.join_room(
        user_id=current_user.id,
        room_code=join_data.room_code
    )
    if not room:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="방을 찾을 수 없거나 입장할 수 없습니다",
        )
    return room


@router.post("/rooms/random", response_model=schemas.Room)
async def join_random_room(
    current_user: models.User = Depends(deps.get_current_user),
) -> Any:
    """
    랜덤 공개 방 입장
    """
    room = await room_service.join_random_room(user_id=current_user.id)
    if not room:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="입장 가능한 방이 없습니다",
        )
    return room


@router.get("/maps", response_model=List[schemas.Map])
async def list_maps(
    current_user: models.User = Depends(deps.get_current_user),
) -> Any:
    """
    사용 가능한 맵 목록 조회
    """
    maps = await game_service.get_available_maps(user_id=current_user.id)
    return maps


@router.post("/ready", response_model=schemas.GameReady)
async def set_ready_status(
    ready_data: schemas.GameReady,
    current_user: models.User = Depends(deps.get_current_user),
) -> Any:
    """
    게임 준비 상태 설정
    """
    status = await game_service.set_player_ready(
        user_id=current_user.id,
        room_id=ready_data.room_id,
        is_ready=ready_data.is_ready
    )
    return status


@router.websocket("/ws/{room_id}")
async def websocket_endpoint(
    websocket: WebSocket,
    room_id: int,
    token: str = None,
):
    """
    게임 실시간 통신 웹소켓
    """
    user = await deps.get_current_user_ws(token)
    if not user:
        await websocket.close(code=1008)
        return
    
    await manager.connect(websocket, room_id, user.id)
    try:
        while True:
            data = await websocket.receive_json()
            await manager.broadcast(room_id, data)
    except WebSocketDisconnect:
        manager.disconnect(websocket, room_id, user.id)
        await manager.broadcast(
            room_id,
            {"type": "player_disconnect", "user_id": user.id}
        ) 