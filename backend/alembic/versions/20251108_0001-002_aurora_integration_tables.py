"""Aurora integration tables

Revision ID: 002
Revises: 001
Create Date: 2025-11-08 00:01:00.000000

"""
from alembic import op
import sqlalchemy as sa
from datetime import datetime


# revision identifiers, used by Alembic.
revision = '002'
down_revision = '001'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create aurora_bookings table
    op.create_table(
        'aurora_bookings',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('booking_id', sa.String(length=100), nullable=False),
        sa.Column('user_id', sa.String(length=100), nullable=True),
        sa.Column('booking_total', sa.Float(), nullable=False),
        sa.Column('nights', sa.Integer(), nullable=False),
        sa.Column('reward_tokens', sa.Float(), nullable=False),
        sa.Column('status', sa.String(length=20), nullable=True, default='active'),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        sa.Column('cancelled_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True, default=datetime.utcnow),
        sa.ForeignKeyConstraint(['user_id'], ['users.user_id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_aurora_bookings_booking_id'), 'aurora_bookings', ['booking_id'], unique=True)
    op.create_index(op.f('ix_aurora_bookings_user_id'), 'aurora_bookings', ['user_id'], unique=False)
    op.create_index(op.f('ix_aurora_bookings_status'), 'aurora_bookings', ['status'], unique=False)
    op.create_index(op.f('ix_aurora_bookings_created_at'), 'aurora_bookings', ['created_at'], unique=False)


def downgrade() -> None:
    op.drop_table('aurora_bookings')
