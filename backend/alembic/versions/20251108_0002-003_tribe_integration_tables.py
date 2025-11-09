"""Tribe integration tables

Revision ID: 003
Revises: 002
Create Date: 2025-11-08 00:02:00.000000

"""
from alembic import op
import sqlalchemy as sa
from datetime import datetime


# revision identifiers, used by Alembic.
revision = '003'
down_revision = '002'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create tribe_events table
    op.create_table(
        'tribe_events',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('event_id', sa.String(length=100), nullable=False),
        sa.Column('user_id', sa.String(length=100), nullable=True),
        sa.Column('event_name', sa.String(length=255), nullable=False),
        sa.Column('event_type', sa.String(length=50), nullable=True),
        sa.Column('attended', sa.Boolean(), nullable=True, default=False),
        sa.Column('tokens_earned', sa.Float(), nullable=True, default=0),
        sa.Column('attended_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True, default=datetime.utcnow),
        sa.ForeignKeyConstraint(['user_id'], ['users.user_id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_tribe_events_event_id'), 'tribe_events', ['event_id'], unique=True)
    op.create_index(op.f('ix_tribe_events_user_id'), 'tribe_events', ['user_id'], unique=False)
    op.create_index(op.f('ix_tribe_events_created_at'), 'tribe_events', ['created_at'], unique=False)

    # Create tribe_rewards table
    op.create_table(
        'tribe_rewards',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('reward_id', sa.String(length=100), nullable=False),
        sa.Column('user_id', sa.String(length=100), nullable=True),
        sa.Column('reward_type', sa.String(length=50), nullable=True),
        sa.Column('amount', sa.Float(), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('status', sa.String(length=20), nullable=True, default='pending'),
        sa.Column('created_at', sa.DateTime(), nullable=True, default=datetime.utcnow),
        sa.Column('processed_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.user_id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_tribe_rewards_reward_id'), 'tribe_rewards', ['reward_id'], unique=True)
    op.create_index(op.f('ix_tribe_rewards_user_id'), 'tribe_rewards', ['user_id'], unique=False)
    op.create_index(op.f('ix_tribe_rewards_reward_type'), 'tribe_rewards', ['reward_type'], unique=False)
    op.create_index(op.f('ix_tribe_rewards_created_at'), 'tribe_rewards', ['created_at'], unique=False)

    # Create staking_records table
    op.create_table(
        'staking_records',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('stake_id', sa.String(length=100), nullable=False),
        sa.Column('user_id', sa.String(length=100), nullable=True),
        sa.Column('amount', sa.Float(), nullable=False),
        sa.Column('earned_rewards', sa.Float(), nullable=True, default=0),
        sa.Column('status', sa.String(length=20), nullable=True, default='active'),
        sa.Column('started_at', sa.DateTime(), nullable=True, default=datetime.utcnow),
        sa.Column('unstaked_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.user_id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_staking_records_stake_id'), 'staking_records', ['stake_id'], unique=True)
    op.create_index(op.f('ix_staking_records_user_id'), 'staking_records', ['user_id'], unique=False)
    op.create_index(op.f('ix_staking_records_status'), 'staking_records', ['status'], unique=False)
    op.create_index(op.f('ix_staking_records_started_at'), 'staking_records', ['started_at'], unique=False)


def downgrade() -> None:
    op.drop_table('staking_records')
    op.drop_table('tribe_rewards')
    op.drop_table('tribe_events')
