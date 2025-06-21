from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from app.core.config import settings

# MySQL 연결 URL 생성
SQLALCHEMY_DATABASE_URL = settings.SQLALCHEMY_DATABASE_URI

# Base 클래스 생성
Base = declarative_base()

# 엔진 생성
engine = create_async_engine(
    SQLALCHEMY_DATABASE_URL,
    pool_pre_ping=True,  # 연결 상태 확인
    pool_recycle=3600,   # 1시간마다 연결 재사용
    echo=True
)

# 세션 생성
async_session = sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)

# DB 세션 의존성
async def get_db() -> AsyncSession:
    async with async_session() as session:
        try:
            yield session
        finally:
            await session.close()

# 데이터베이스 테이블 생성
async def create_tables():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all) 