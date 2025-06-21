from fastapi import APIRouter

from app.api.endpoints import auth, users, rooms

api_router = APIRouter()

# 인증 관련 엔드포인트
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(users.router, prefix="/users", tags=["사용자"])
api_router.include_router(rooms.router, prefix="/room", tags=["방"]) 