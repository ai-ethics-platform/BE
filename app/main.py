from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime
import os

from app.api.api import api_router
from app.core.config import settings
from app.core.database import create_tables
from app.core.error_tracking import capture_exception, shutdown_error_tracking
from app.core.game_diagnostics import record_request, flush_game_diagnostics
from fastapi.staticfiles import StaticFiles

app = FastAPI(
    title=settings.PROJECT_NAME,
    description="AI 윤리게임 백엔드 API",
    version="0.1.0",
    openapi_url=f"/openapi.json"
)


@app.exception_handler(Exception)
async def report_unhandled_exception(request: Request, exc: Exception):
    route = request.scope.get("route")
    endpoint = getattr(route, "path", "unmatched")
    capture_exception(exc, endpoint, request.headers.get("x-posthog-session-id"))
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"},
    )

@app.middleware('http')
async def record_game_request_context(request: Request, call_next):
    status = 500
    try:
        response = await call_next(request)
        status = response.status_code
        return response
    finally:
        try:
            record_request(request, status)
        except Exception:
            pass  # Diagnostics must not change API behavior.

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://localhost:3000",
        "http://localhost:8000",
        "https://dilemmai.org",
        "https://www.dilemmai.org",
        "https://fe-git-feature-env-refactoring-dldbstjs-projects.vercel.app",
    ],
    allow_origin_regex=r"^https://fe-tfc6-[a-z0-9-]+-idl-lab\.vercel\.app$",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router)

# 정적 파일 디렉토리 생성 (존재하지 않을 경우)
os.makedirs("app/static", exist_ok=True)
os.makedirs("recordings", exist_ok=True)

# 정적 파일 마운트
app.mount("/static", StaticFiles(directory="app/static"), name="static")
app.mount("/recordings", StaticFiles(directory="recordings"), name="recordings")

@app.on_event("startup")
async def startup_event():
    # 데이터베이스 테이블 생성
    await create_tables()


@app.on_event("shutdown")
async def shutdown_event():
    await flush_game_diagnostics()
    shutdown_error_tracking()

@app.get("/")
async def root():
    return {"message": "AI 윤리게임에 오신 것을 환영합니다!"}

@app.get("/health")
async def health_check():
    """헬스 체크"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "service": "ai-ethics-game-backend",
        "message": "AI Ethics Game Backend is running"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
