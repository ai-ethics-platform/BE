"""update_existing_room_codes_to_6_digits

Revision ID: f661ecf3115a
Revises: 60268bb6ca91
Create Date: 2025-07-12 15:30:51.079571

"""
from typing import Sequence, Union
import random

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'f661ecf3115a'
down_revision: Union[str, None] = '60268bb6ca91'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def generate_6_digit_code() -> str:
    """6자리 숫자 코드 생성"""
    return ''.join(random.choice('0123456789') for _ in range(6))


def upgrade() -> None:
    """Upgrade schema."""
    # 기존 방 코드들을 6자리 숫자로 변환
    connection = op.get_bind()
    
    # 모든 방 조회
    rooms = connection.execute(sa.text("SELECT id, room_code FROM rooms")).fetchall()
    
    # 사용된 코드들을 추적
    used_codes = set()
    
    for room in rooms:
        room_id, old_code = room
        
        # 이미 6자리 숫자인지 확인
        if old_code.isdigit() and len(old_code) == 6:
            used_codes.add(old_code)
            continue
        
        # 새로운 6자리 숫자 코드 생성 (중복 방지)
        while True:
            new_code = generate_6_digit_code()
            if new_code not in used_codes:
                used_codes.add(new_code)
                break
        
        # 방 코드 업데이트
        connection.execute(
            sa.text("UPDATE rooms SET room_code = :new_code WHERE id = :room_id"),
            {"new_code": new_code, "room_id": room_id}
        )
        
        print(f"Room {room_id}: {old_code} -> {new_code}")


def downgrade() -> None:
    """Downgrade schema."""
    # 다운그레이드 시에는 원래 코드로 복원할 수 없으므로 pass
    pass
