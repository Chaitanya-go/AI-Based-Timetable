"""add periods_per_session

Revision ID: 002
Revises: 001
Create Date: 2026-03-20 21:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

revision = '002'
down_revision = '001'
branch_labels = None
depends_on = None

def upgrade() -> None:
    op.add_column('subjects', sa.Column('periods_per_session', sa.Integer(), server_default='1', nullable=False))

def downgrade() -> None:
    op.drop_column('subjects', 'periods_per_session')
