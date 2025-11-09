"""Audit log table

Revision ID: 004
Revises: 003
Create Date: 2025-11-08 00:03:00.000000

"""
from alembic import op
import sqlalchemy as sa
from datetime import datetime


# revision identifiers, used by Alembic.
revision = '004'
down_revision = '003'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create audit_log table for security and compliance tracking
    op.create_table(
        'audit_log',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('log_id', sa.String(length=100), nullable=False),
        sa.Column('user_id', sa.String(length=100), nullable=True),
        sa.Column('action', sa.String(length=100), nullable=False),
        sa.Column('resource_type', sa.String(length=50), nullable=True),
        sa.Column('resource_id', sa.String(length=100), nullable=True),
        sa.Column('ip_address', sa.String(length=45), nullable=True),
        sa.Column('user_agent', sa.Text(), nullable=True),
        sa.Column('request_data', sa.Text(), nullable=True),  # JSON
        sa.Column('response_status', sa.Integer(), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('timestamp', sa.DateTime(), nullable=False, default=datetime.utcnow),
        sa.ForeignKeyConstraint(['user_id'], ['users.user_id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_audit_log_log_id'), 'audit_log', ['log_id'], unique=True)
    op.create_index(op.f('ix_audit_log_user_id'), 'audit_log', ['user_id'], unique=False)
    op.create_index(op.f('ix_audit_log_action'), 'audit_log', ['action'], unique=False)
    op.create_index(op.f('ix_audit_log_timestamp'), 'audit_log', ['timestamp'], unique=False)
    op.create_index('idx_user_action_timestamp', 'audit_log', ['user_id', 'action', 'timestamp'])


def downgrade() -> None:
    op.drop_table('audit_log')
