"""add hours_per_week and lunch_break_period

Revision ID: 001
Revises: 
Create Date: 2026-03-20 20:30:00.000000

"""
from alembic import op
import sqlalchemy as sa

revision = '001'
down_revision = None
branch_labels = None
depends_on = None

def upgrade() -> None:
    # Adding to Subject
    op.add_column('subjects', sa.Column('hours_per_week', sa.Integer(), server_default='1', nullable=False))
    # Adding to Division
    op.add_column('divisions', sa.Column('lunch_break_period', sa.Integer(), nullable=True))

def downgrade() -> None:
    op.drop_column('subjects', 'hours_per_week')
    op.drop_column('divisions', 'lunch_break_period')
