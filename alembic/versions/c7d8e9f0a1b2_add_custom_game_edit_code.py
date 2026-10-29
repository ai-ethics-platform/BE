"""Add private creator edit codes for game preview access.

Revision ID: c7d8e9f0a1b2
Revises: a1b2c3d4e5f6
"""
from alembic import op
import sqlalchemy as sa

revision = 'c7d8e9f0a1b2'
down_revision = 'a1b2c3d4e5f6'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('custom_games', sa.Column('edit_code', sa.String(64), nullable=True))
    op.create_index('ix_custom_games_edit_code', 'custom_games', ['edit_code'], unique=True)


def downgrade():
    op.drop_index('ix_custom_games_edit_code', table_name='custom_games')
    op.drop_column('custom_games', 'edit_code')
