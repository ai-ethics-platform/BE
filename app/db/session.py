from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from app.core.config import settings

# PostgreSQL 연결 문자열을 비동기 형식으로 변환
SQLALCHEMY_DATABASE_URL = str(settings.SQLALCHEMY_DATABASE_URI)
ASYNC_SQLALCHEMY_DATABASE_URL = SQLALCHEMY_DATABASE_URL.replace(
    "postgresql://", "postgresql+asyncpg://"
)

# 비동기 엔진 생성
engine = create_async_engine(
    ASYNC_SQLALCHEMY_DATABASE_URL,
    echo=True,
    future=True,
)

# 비동기 세션 생성
AsyncSessionLocal = sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)


async def get_db() -> AsyncSession:
    """
    의존성 주입을 위한 데이터베이스 세션 제공 함수
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close() 