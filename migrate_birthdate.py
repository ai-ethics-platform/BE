#!/usr/bin/env python3
"""
birthdate 필드 마이그레이션 스크립트
YYYY/MM/DD 형식에서 YYYY/MM 형식으로 변경
"""

import asyncio
import re
from sqlalchemy import text
from app.core.database import engine, async_session
from app.core.config import settings


async def migrate_birthdate():
    """birthdate 필드를 YYYY/MM 형식으로 마이그레이션"""
    
    async with async_session() as session:
        try:
            # 1. 기존 데이터 확인
            result = await session.execute(text("SELECT id, birthdate FROM users"))
            users = result.fetchall()
            
            print(f"총 {len(users)}명의 사용자 데이터를 확인합니다.")
            
            # 2. 각 사용자의 birthdate를 YYYY/MM 형식으로 변환
            for user in users:
                user_id, birthdate = user
                
                if birthdate:
                    # YYYY/MM/DD 형식인지 확인
                    if re.match(r'^\d{4}/\d{2}/\d{2}$', birthdate):
                        # YYYY/MM 형식으로 변환
                        new_birthdate = birthdate[:7]  # YYYY/MM 부분만 추출
                        print(f"사용자 ID {user_id}: {birthdate} -> {new_birthdate}")
                        
                        # 데이터베이스 업데이트
                        await session.execute(
                            text("UPDATE users SET birthdate = :birthdate WHERE id = :user_id"),
                            {"birthdate": new_birthdate, "user_id": user_id}
                        )
                    else:
                        print(f"사용자 ID {user_id}: 이미 올바른 형식이거나 다른 형식 - {birthdate}")
            
            # 3. 변경사항 커밋
            await session.commit()
            print("마이그레이션이 완료되었습니다.")
            
        except Exception as e:
            await session.rollback()
            print(f"마이그레이션 중 오류 발생: {e}")
            raise


async def create_tables_with_new_schema():
    """새로운 스키마로 테이블 재생성"""
    
    async with engine.begin() as conn:
        # 기존 테이블 삭제 (주의: 모든 데이터가 삭제됩니다!)
        print("기존 테이블을 삭제합니다...")
        await conn.run_sync(lambda sync_conn: sync_conn.execute(text("DROP TABLE IF EXISTS room_participants CASCADE")))
        await conn.run_sync(lambda sync_conn: sync_conn.execute(text("DROP TABLE IF EXISTS rooms CASCADE")))
        await conn.run_sync(lambda sync_conn: sync_conn.execute(text("DROP TABLE IF EXISTS users CASCADE")))
        
        # 새로운 스키마로 테이블 생성
        print("새로운 스키마로 테이블을 생성합니다...")
        from app.db.base import Base
        await conn.run_sync(Base.metadata.create_all)
        
        print("테이블 재생성이 완료되었습니다.")


async def main():
    """메인 실행 함수"""
    print("=== birthdate 필드 마이그레이션 시작 ===")
    
    choice = input("""
마이그레이션 방법을 선택하세요:
1. 기존 데이터를 보존하면서 마이그레이션 (권장)
2. 테이블을 완전히 재생성 (모든 데이터 삭제)

선택 (1 또는 2): """)
    
    if choice == "1":
        print("\n기존 데이터를 보존하면서 마이그레이션을 진행합니다...")
        await migrate_birthdate()
    elif choice == "2":
        confirm = input("\n⚠️  모든 데이터가 삭제됩니다. 정말 진행하시겠습니까? (yes/no): ")
        if confirm.lower() == "yes":
            print("\n테이블을 재생성합니다...")
            await create_tables_with_new_schema()
        else:
            print("마이그레이션이 취소되었습니다.")
    else:
        print("잘못된 선택입니다.")


if __name__ == "__main__":
    asyncio.run(main()) 