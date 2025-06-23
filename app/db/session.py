from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from app.core.config import settings

# MySQL 연결 문자열을 비동기 형식으로 변환
SQLALCHEMY_DATABASE_URL = str(settings.SQLALCHEMY_DATABASE_URI)
ASYNC_SQLALCHEMY_DATABASE_URL = SQLALCHEMY_DATABASE_URL.replace(
    "mysql://", "mysql+aiomysql://"
)

# 비동기 엔진 생성
engine = create_async_engine(
    ASYNC_SQLALCHEMY_DATABASE_URL,
    pool_pre_ping=True,
    echo=True
)

# 비동기 세션 생성
SessionLocal = sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False
)


async def get_db() -> AsyncSession:
    """
    의존성 주입을 위한 데이터베이스 세션 제공 함수
    """
    async with SessionLocal() as session:
        try:
            yield session
        finally:
            await session.close() 