# app/api/api.py
from fastapi import APIRouter

from app.api.endpoints import auth, users, rooms, voice
from app.api import voice_ws

api_router = APIRouter()

# 인증 관련 엔드포인트
api_router.include_router(auth.router, prefix="/auth", tags=["authentication"])
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(rooms.router, prefix="/rooms", tags=["rooms"])
api_router.include_router(voice.router, prefix="/voice", tags=["voice"])
api_router.include_router(voice_ws.router, prefix="/ws", tags=["voice_ws"])