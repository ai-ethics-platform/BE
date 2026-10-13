"""Bind rooms to their custom game.

Revision ID: 7c02822b96af
Revises: 33c5c4bdb54e
"""
from alembic import op
import sqlalchemy as sa

revision = '7c02822b96af'
down_revision = '33c5c4bdb54e'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column('rooms', sa.Column('custom_game_code', sa.String(20), nullable=True))


def downgrade() -> None:
    op.drop_column('rooms', 'custom_game_code')
