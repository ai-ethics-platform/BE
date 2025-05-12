from fastapi import APIRouter

from app.api.endpoints import auth, users, game, audio, ai

api_router = APIRouter()
api_router.include_router(auth.router, prefix="/auth", tags=["인증"])
api_router.include_router(users.router, prefix="/users", tags=["사용자"])
api_router.include_router(game.router, prefix="/game", tags=["게임"])
api_router.include_router(audio.router, prefix="/audio", tags=["음성"])
api_router.include_router(ai.router, prefix="/ai", tags=["AI"]) 