from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime

from app.api.api import api_router
from app.core.config import settings
from app.core.database import create_tables
from fastapi.staticfiles import StaticFiles

app = FastAPI(
    title=settings.PROJECT_NAME,
    description="AI 윤리게임 백엔드 API",
    version="0.1.0",
    openapi_url=f"/openapi.json"
)

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "https://www.dilemmai-idl.com",
        "http://localhost:3000",
        "http://localhost:8000",
        "https://dilemmai.org"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router)
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.on_event("startup")
async def startup_event():
    # 데이터베이스 테이블 생성
    await create_tables()

@app.get("/")
async def root():
    return {"message": "AI 윤리게임에 오신 것을 환영합니다!"}

@app.get("/health")
async def health_check():
    """헬스 체크 엔드포인트"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "service": "ai-ethics-game-backend",
        "message": "AI Ethics Game Backend is running"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True) 