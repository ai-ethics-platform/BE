"""update_chat_session_default_step_to_opening

Revision ID: a1b2c3d4e5f6
Revises: chat_session_001
Create Date: 2025-01-27 15:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, None] = 'chat_session_001'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # chat_sessions 테이블의 current_step 컬럼 기본값을 'opening'으로 변경
    # 기존 'topic' 값을 가진 레코드들도 'opening'으로 업데이트
    connection = op.get_bind()
    
    # 기존 데이터 업데이트 (topic -> opening)
    connection.execute(
        sa.text("UPDATE chat_sessions SET current_step = 'opening' WHERE current_step = 'topic'")
    )
    
    # 컬럼의 기본값 변경 (MySQL의 경우 ALTER TABLE 사용)
    op.alter_column('chat_sessions', 'current_step',
                    existing_type=sa.String(length=50),
                    server_default='opening',
                    nullable=False)


def downgrade() -> None:
    """Downgrade schema."""
    # 기본값을 'topic'으로 되돌림
    connection = op.get_bind()
    
    # 기존 데이터 업데이트 (opening -> topic)
    connection.execute(
        sa.text("UPDATE chat_sessions SET current_step = 'topic' WHERE current_step = 'opening'")
    )
    
    # 컬럼의 기본값 변경
    op.alter_column('chat_sessions', 'current_step',
                    existing_type=sa.String(length=50),
                    server_default='topic',
                    nullable=False)

