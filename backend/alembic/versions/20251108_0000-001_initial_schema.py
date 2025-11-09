"""Initial schema

Revision ID: 001
Revises:
Create Date: 2025-11-08 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from datetime import datetime


# revision identifiers, used by Alembic.
revision = '001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create users table
    op.create_table(
        'users',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.String(length=100), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=True),
        sa.Column('wallet_address', sa.String(length=42), nullable=True),
        sa.Column('kyc_verified', sa.Boolean(), nullable=True, default=False),
        sa.Column('created_at', sa.DateTime(), nullable=True, default=datetime.utcnow),
        sa.Column('updated_at', sa.DateTime(), nullable=True, default=datetime.utcnow),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_users_user_id'), 'users', ['user_id'], unique=True)
    op.create_index(op.f('ix_users_email'), 'users', ['email'], unique=True)
    op.create_index(op.f('ix_users_wallet_address'), 'users', ['wallet_address'], unique=True)

    # Create transactions table
    op.create_table(
        'transactions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('tx_id', sa.String(length=100), nullable=False),
        sa.Column('user_id', sa.String(length=100), nullable=True),
        sa.Column('tx_type', sa.String(length=20), nullable=True),
        sa.Column('amount', sa.Float(), nullable=False),
        sa.Column('reason', sa.Text(), nullable=True),
        sa.Column('status', sa.String(length=20), nullable=True, default='pending'),
        sa.Column('blockchain_tx', sa.String(length=66), nullable=True),
        sa.Column('gas_used', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True, default=datetime.utcnow),
        sa.Column('confirmed_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.user_id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_transactions_tx_id'), 'transactions', ['tx_id'], unique=True)
    op.create_index(op.f('ix_transactions_user_id'), 'transactions', ['user_id'], unique=False)
    op.create_index(op.f('ix_transactions_tx_type'), 'transactions', ['tx_type'], unique=False)
    op.create_index(op.f('ix_transactions_status'), 'transactions', ['status'], unique=False)
    op.create_index(op.f('ix_transactions_blockchain_tx'), 'transactions', ['blockchain_tx'], unique=True)
    op.create_index(op.f('ix_transactions_created_at'), 'transactions', ['created_at'], unique=False)
    op.create_index('idx_user_status', 'transactions', ['user_id', 'status'])
    op.create_index('idx_type_created', 'transactions', ['tx_type', 'created_at'])

    # Create redemption_requests table
    op.create_table(
        'redemption_requests',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('request_id', sa.String(length=100), nullable=False),
        sa.Column('user_id', sa.String(length=100), nullable=True),
        sa.Column('amount', sa.Float(), nullable=False),
        sa.Column('withdrawal_method', sa.String(length=50), nullable=True),
        sa.Column('withdrawal_address', sa.String(length=255), nullable=True),
        sa.Column('status', sa.String(length=20), nullable=True, default='pending'),
        sa.Column('burn_tx_id', sa.String(length=66), nullable=True),
        sa.Column('payout_reference', sa.String(length=255), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True, default=datetime.utcnow),
        sa.Column('processed_at', sa.DateTime(), nullable=True),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.user_id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_redemption_requests_request_id'), 'redemption_requests', ['request_id'], unique=True)
    op.create_index(op.f('ix_redemption_requests_user_id'), 'redemption_requests', ['user_id'], unique=False)
    op.create_index(op.f('ix_redemption_requests_status'), 'redemption_requests', ['status'], unique=False)
    op.create_index(op.f('ix_redemption_requests_created_at'), 'redemption_requests', ['created_at'], unique=False)
    op.create_index('idx_user_status_redemption', 'redemption_requests', ['user_id', 'status'])

    # Create system_metrics table
    op.create_table(
        'system_metrics',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('metric_name', sa.String(length=100), nullable=False),
        sa.Column('metric_value', sa.Float(), nullable=False),
        sa.Column('timestamp', sa.DateTime(), nullable=True, default=datetime.utcnow),
        sa.Column('metadata', sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_system_metrics_metric_name'), 'system_metrics', ['metric_name'], unique=False)
    op.create_index(op.f('ix_system_metrics_timestamp'), 'system_metrics', ['timestamp'], unique=False)
    op.create_index('idx_metric_timestamp', 'system_metrics', ['metric_name', 'timestamp'])


def downgrade() -> None:
    op.drop_table('system_metrics')
    op.drop_table('redemption_requests')
    op.drop_table('transactions')
    op.drop_table('users')
