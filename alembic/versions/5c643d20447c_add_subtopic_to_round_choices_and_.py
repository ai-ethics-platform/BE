"""add_subtopic_to_round_choices_and_consensus_choices

Revision ID: 5c643d20447c
Revises: b2dec9db1111
Create Date: 2025-07-28 00:34:59.135733

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '5c643d20447c'
down_revision: Union[str, None] = 'b2dec9db1111'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Add a new column 'subtopic' to both 'round_choices' and 'consensus_choices' tables
    op.add_column('round_choices', sa.Column('subtopic', sa.String(length=255), nullable=True))
    op.add_column('consensus_choices', sa.Column('subtopic', sa.String(length=255), nullable=True))

def downgrade() -> None:
    """Downgrade schema."""
    # Drop the 'subtopic' column from both 'round_choices' and 'consensus_choices' tables
    op.drop_column('round_choices', 'subtopic')
    op.drop_column('consensus_choices', 'subtopic')

