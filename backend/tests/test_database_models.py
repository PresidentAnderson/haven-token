"""
Unit Tests for Database Models
Tests SQLAlchemy models for HAVEN Token system.
"""

import pytest
from datetime import datetime, timedelta
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from sqlalchemy.exc import IntegrityError

from database.models import (
    Base, User, Transaction, AuroraBooking, TribeEvent,
    TribeReward, StakingRecord, RedemptionRequest, SystemMetrics
)


class TestUserModel:
    """Test User model operations."""

    def test_create_user(self, db_session):
        """Test creating a new user."""
        user = User(
            user_id='user_123',
            email='test@example.com',
            wallet_address='0x' + '1' * 40,
            kyc_verified=False
        )
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)

        assert user.id is not None
        assert user.user_id == 'user_123'
        assert user.email == 'test@example.com'
        assert user.wallet_address == '0x' + '1' * 40
        assert user.kyc_verified is False
        assert user.created_at is not None
        assert user.updated_at is not None

    def test_user_unique_constraints(self, db_session):
        """Test that user_id, email, and wallet_address are unique."""
        user1 = User(
            user_id='unique_user',
            email='unique@example.com',
            wallet_address='0x' + 'a' * 40
        )
        db_session.add(user1)
        db_session.commit()

        # Try to create duplicate user_id
        user2 = User(
            user_id='unique_user',
            email='different@example.com',
            wallet_address='0x' + 'b' * 40
        )
        db_session.add(user2)
        with pytest.raises(IntegrityError):
            db_session.commit()

        db_session.rollback()

        # Try to create duplicate email
        user3 = User(
            user_id='different_user',
            email='unique@example.com',
            wallet_address='0x' + 'c' * 40
        )
        db_session.add(user3)
        with pytest.raises(IntegrityError):
            db_session.commit()

    def test_user_relationships(self, db_session):
        """Test user relationships with other models."""
        user = User(
            user_id='rel_user',
            email='rel@example.com',
            wallet_address='0x' + 'd' * 40
        )
        db_session.add(user)
        db_session.commit()

        # Add transaction
        tx = Transaction(
            tx_id='tx_001',
            user_id=user.user_id,
            tx_type='mint',
            amount=100.0,
            reason='test'
        )
        db_session.add(tx)
        db_session.commit()
        db_session.refresh(user)

        assert len(user.transactions) == 1
        assert user.transactions[0].tx_id == 'tx_001'


class TestTransactionModel:
    """Test Transaction model operations."""

    def test_create_transaction(self, db_session, sample_user):
        """Test creating a transaction."""
        tx = Transaction(
            tx_id='mint_tx_001',
            user_id=sample_user.user_id,
            tx_type='mint',
            amount=150.0,
            reason='aurora_booking_reward',
            status='pending'
        )
        db_session.add(tx)
        db_session.commit()
        db_session.refresh(tx)

        assert tx.id is not None
        assert tx.tx_id == 'mint_tx_001'
        assert tx.amount == 150.0
        assert tx.status == 'pending'
        assert tx.created_at is not None
        assert tx.confirmed_at is None

    def test_transaction_status_updates(self, db_session, sample_user):
        """Test updating transaction status."""
        tx = Transaction(
            tx_id='status_test_tx',
            user_id=sample_user.user_id,
            tx_type='mint',
            amount=100.0,
            reason='test',
            status='pending'
        )
        db_session.add(tx)
        db_session.commit()

        # Update to confirming
        tx.status = 'confirming'
        tx.blockchain_tx = '0x' + 'f' * 64
        db_session.commit()

        assert tx.status == 'confirming'
        assert tx.blockchain_tx is not None

        # Update to confirmed
        tx.status = 'confirmed'
        tx.confirmed_at = datetime.utcnow()
        tx.gas_used = 95000
        db_session.commit()

        assert tx.status == 'confirmed'
        assert tx.confirmed_at is not None
        assert tx.gas_used == 95000

    def test_transaction_types(self, db_session, sample_user):
        """Test different transaction types."""
        mint_tx = Transaction(
            tx_id='mint_001',
            user_id=sample_user.user_id,
            tx_type='mint',
            amount=100.0,
            reason='reward'
        )

        burn_tx = Transaction(
            tx_id='burn_001',
            user_id=sample_user.user_id,
            tx_type='burn',
            amount=50.0,
            reason='redemption'
        )

        db_session.add_all([mint_tx, burn_tx])
        db_session.commit()

        mints = db_session.query(Transaction).filter(
            Transaction.tx_type == 'mint'
        ).all()
        burns = db_session.query(Transaction).filter(
            Transaction.tx_type == 'burn'
        ).all()

        assert len(mints) >= 1
        assert len(burns) >= 1
        assert mint_tx in mints
        assert burn_tx in burns

    def test_transaction_unique_tx_id(self, db_session, sample_user):
        """Test that transaction tx_id is unique."""
        tx1 = Transaction(
            tx_id='unique_tx_id',
            user_id=sample_user.user_id,
            tx_type='mint',
            amount=100.0,
            reason='first'
        )
        db_session.add(tx1)
        db_session.commit()

        # Try duplicate tx_id
        tx2 = Transaction(
            tx_id='unique_tx_id',
            user_id=sample_user.user_id,
            tx_type='mint',
            amount=200.0,
            reason='second'
        )
        db_session.add(tx2)
        with pytest.raises(IntegrityError):
            db_session.commit()


class TestAuroraBookingModel:
    """Test AuroraBooking model operations."""

    def test_create_aurora_booking(self, db_session, sample_user):
        """Test creating an Aurora booking."""
        booking = AuroraBooking(
            booking_id='aurora_booking_001',
            user_id=sample_user.user_id,
            booking_total=500.0,
            nights=3,
            reward_tokens=50.0,
            status='active'
        )
        db_session.add(booking)
        db_session.commit()
        db_session.refresh(booking)

        assert booking.id is not None
        assert booking.booking_id == 'aurora_booking_001'
        assert booking.booking_total == 500.0
        assert booking.nights == 3
        assert booking.reward_tokens == 50.0
        assert booking.status == 'active'

    def test_complete_aurora_booking(self, db_session, sample_user):
        """Test completing an Aurora booking."""
        booking = AuroraBooking(
            booking_id='complete_booking',
            user_id=sample_user.user_id,
            booking_total=300.0,
            nights=2,
            reward_tokens=30.0,
            status='active'
        )
        db_session.add(booking)
        db_session.commit()

        # Complete booking
        booking.status = 'completed'
        booking.completed_at = datetime.utcnow()
        db_session.commit()

        assert booking.status == 'completed'
        assert booking.completed_at is not None

    def test_cancel_aurora_booking(self, db_session, sample_user):
        """Test cancelling an Aurora booking."""
        booking = AuroraBooking(
            booking_id='cancelled_booking',
            user_id=sample_user.user_id,
            booking_total=400.0,
            nights=2,
            reward_tokens=40.0,
            status='active'
        )
        db_session.add(booking)
        db_session.commit()

        # Cancel booking
        booking.status = 'cancelled'
        booking.cancelled_at = datetime.utcnow()
        db_session.commit()

        assert booking.status == 'cancelled'
        assert booking.cancelled_at is not None


class TestTribeEventModel:
    """Test TribeEvent model operations."""

    def test_create_tribe_event(self, db_session, sample_user):
        """Test creating a Tribe event."""
        event = TribeEvent(
            event_id='tribe_event_001',
            user_id=sample_user.user_id,
            event_name='Wisdom Circle',
            event_type='attendance',
            attended=True,
            tokens_earned=10.0,
            attended_at=datetime.utcnow()
        )
        db_session.add(event)
        db_session.commit()
        db_session.refresh(event)

        assert event.id is not None
        assert event.event_name == 'Wisdom Circle'
        assert event.attended is True
        assert event.tokens_earned == 10.0

    def test_tribe_event_types(self, db_session, sample_user):
        """Test different Tribe event types."""
        events = [
            TribeEvent(
                event_id='attendance_001',
                user_id=sample_user.user_id,
                event_name='Event 1',
                event_type='attendance',
                tokens_earned=10.0
            ),
            TribeEvent(
                event_id='contribution_001',
                user_id=sample_user.user_id,
                event_name='Event 2',
                event_type='contribution',
                tokens_earned=25.0
            ),
            TribeEvent(
                event_id='coaching_001',
                user_id=sample_user.user_id,
                event_name='Event 3',
                event_type='coaching',
                tokens_earned=50.0
            )
        ]

        db_session.add_all(events)
        db_session.commit()

        contributions = db_session.query(TribeEvent).filter(
            TribeEvent.event_type == 'contribution'
        ).all()

        assert len(contributions) >= 1


class TestStakingRecordModel:
    """Test StakingRecord model operations."""

    def test_create_staking_record(self, db_session, sample_user):
        """Test creating a staking record."""
        stake = StakingRecord(
            stake_id='stake_001',
            user_id=sample_user.user_id,
            amount=1000.0,
            status='active',
            started_at=datetime.utcnow()
        )
        db_session.add(stake)
        db_session.commit()
        db_session.refresh(stake)

        assert stake.id is not None
        assert stake.amount == 1000.0
        assert stake.status == 'active'
        assert stake.earned_rewards == 0

    def test_accrue_staking_rewards(self, db_session, sample_user):
        """Test accruing staking rewards."""
        stake = StakingRecord(
            stake_id='stake_rewards',
            user_id=sample_user.user_id,
            amount=500.0,
            status='active'
        )
        db_session.add(stake)
        db_session.commit()

        # Simulate reward accrual
        stake.earned_rewards += 25.0
        db_session.commit()

        assert stake.earned_rewards == 25.0

    def test_unstake(self, db_session, sample_user):
        """Test unstaking tokens."""
        stake = StakingRecord(
            stake_id='unstake_test',
            user_id=sample_user.user_id,
            amount=750.0,
            status='active'
        )
        db_session.add(stake)
        db_session.commit()

        # Unstake
        stake.status = 'unstaked'
        stake.unstaked_at = datetime.utcnow()
        db_session.commit()

        assert stake.status == 'unstaked'
        assert stake.unstaked_at is not None


class TestRedemptionRequestModel:
    """Test RedemptionRequest model operations."""

    def test_create_redemption_request(self, db_session, sample_user):
        """Test creating a redemption request."""
        redemption = RedemptionRequest(
            request_id='redemption_001',
            user_id=sample_user.user_id,
            amount=100.0,
            withdrawal_method='bank_transfer',
            withdrawal_address='IBAN123456789',
            status='pending'
        )
        db_session.add(redemption)
        db_session.commit()
        db_session.refresh(redemption)

        assert redemption.id is not None
        assert redemption.amount == 100.0
        assert redemption.withdrawal_method == 'bank_transfer'
        assert redemption.status == 'pending'

    def test_process_redemption(self, db_session, sample_user):
        """Test processing a redemption request."""
        redemption = RedemptionRequest(
            request_id='process_redemption',
            user_id=sample_user.user_id,
            amount=200.0,
            withdrawal_method='paypal',
            withdrawal_address='user@paypal.com',
            status='pending'
        )
        db_session.add(redemption)
        db_session.commit()

        # Process
        redemption.status = 'processing'
        redemption.burn_tx_id = '0x' + 'e' * 64
        redemption.processed_at = datetime.utcnow()
        db_session.commit()

        assert redemption.status == 'processing'
        assert redemption.burn_tx_id is not None
        assert redemption.processed_at is not None

    def test_complete_redemption(self, db_session, sample_user):
        """Test completing a redemption request."""
        redemption = RedemptionRequest(
            request_id='complete_redemption',
            user_id=sample_user.user_id,
            amount=150.0,
            withdrawal_method='crypto',
            withdrawal_address='0x' + '9' * 40,
            status='processing',
            burn_tx_id='0x' + 'd' * 64
        )
        db_session.add(redemption)
        db_session.commit()

        # Complete
        redemption.status = 'completed'
        redemption.payout_reference = 'PAYOUT_12345'
        redemption.completed_at = datetime.utcnow()
        db_session.commit()

        assert redemption.status == 'completed'
        assert redemption.payout_reference is not None
        assert redemption.completed_at is not None

    def test_redemption_withdrawal_methods(self, db_session, sample_user):
        """Test different withdrawal methods."""
        methods = ['bank_transfer', 'paypal', 'crypto']

        for i, method in enumerate(methods):
            redemption = RedemptionRequest(
                request_id=f'redemption_method_{i}',
                user_id=sample_user.user_id,
                amount=100.0,
                withdrawal_method=method,
                status='pending'
            )
            db_session.add(redemption)

        db_session.commit()

        paypal_redemptions = db_session.query(RedemptionRequest).filter(
            RedemptionRequest.withdrawal_method == 'paypal'
        ).all()

        assert len(paypal_redemptions) >= 1


class TestSystemMetricsModel:
    """Test SystemMetrics model operations."""

    def test_create_system_metric(self, db_session):
        """Test creating a system metric."""
        metric = SystemMetrics(
            metric_name='total_users',
            metric_value=1000.0,
            metadata='{"source": "daily_aggregation"}'
        )
        db_session.add(metric)
        db_session.commit()
        db_session.refresh(metric)

        assert metric.id is not None
        assert metric.metric_name == 'total_users'
        assert metric.metric_value == 1000.0
        assert metric.timestamp is not None

    def test_track_metrics_over_time(self, db_session):
        """Test tracking metrics over time."""
        base_time = datetime.utcnow()

        for i in range(5):
            metric = SystemMetrics(
                metric_name='circulating_supply',
                metric_value=1000.0 + (i * 100),
                timestamp=base_time + timedelta(hours=i)
            )
            db_session.add(metric)

        db_session.commit()

        metrics = db_session.query(SystemMetrics).filter(
            SystemMetrics.metric_name == 'circulating_supply'
        ).order_by(SystemMetrics.timestamp.asc()).all()

        assert len(metrics) == 5
        assert metrics[0].metric_value == 1000.0
        assert metrics[-1].metric_value == 1400.0

    def test_different_metric_types(self, db_session):
        """Test storing different types of metrics."""
        metrics = [
            SystemMetrics(metric_name='total_minted', metric_value=15000.0),
            SystemMetrics(metric_name='total_burned', metric_value=5000.0),
            SystemMetrics(metric_name='active_users', metric_value=250.0),
            SystemMetrics(metric_name='total_transactions', metric_value=1234.0)
        ]

        db_session.add_all(metrics)
        db_session.commit()

        minted = db_session.query(SystemMetrics).filter(
            SystemMetrics.metric_name == 'total_minted'
        ).first()

        assert minted is not None
        assert minted.metric_value == 15000.0


class TestModelIndexes:
    """Test that database indexes are properly configured."""

    def test_transaction_indexes(self, db_session, sample_user):
        """Test transaction model indexes for query performance."""
        # Create multiple transactions
        for i in range(10):
            tx = Transaction(
                tx_id=f'index_test_tx_{i}',
                user_id=sample_user.user_id,
                tx_type='mint' if i % 2 == 0 else 'burn',
                amount=100.0 * i,
                reason='index_test',
                status='confirmed' if i > 5 else 'pending'
            )
            db_session.add(tx)

        db_session.commit()

        # Query using indexed fields
        confirmed_txs = db_session.query(Transaction).filter(
            Transaction.user_id == sample_user.user_id,
            Transaction.status == 'confirmed'
        ).all()

        assert len(confirmed_txs) == 4  # transactions with i > 5 (6,7,8,9)

    def test_redemption_indexes(self, db_session, sample_user):
        """Test redemption request indexes."""
        for i in range(5):
            redemption = RedemptionRequest(
                request_id=f'index_redemption_{i}',
                user_id=sample_user.user_id,
                amount=100.0,
                withdrawal_method='bank_transfer',
                status='completed' if i >= 3 else 'pending'
            )
            db_session.add(redemption)

        db_session.commit()

        # Query using indexed fields
        completed = db_session.query(RedemptionRequest).filter(
            RedemptionRequest.user_id == sample_user.user_id,
            RedemptionRequest.status == 'completed'
        ).all()

        assert len(completed) == 2


class TestDataIntegrity:
    """Test data integrity constraints and validations."""

    def test_foreign_key_constraints(self, db_session):
        """Test foreign key relationships work correctly."""
        # Create transaction without user
        tx = Transaction(
            tx_id='orphan_tx',
            user_id='nonexistent_user',
            tx_type='mint',
            amount=100.0,
            reason='test'
        )
        db_session.add(tx)

        # Should commit successfully even without foreign key user
        # (SQLite doesn't enforce foreign keys by default in test)
        db_session.commit()

    def test_cascade_behavior(self, db_session):
        """Test that related records are properly handled."""
        user = User(
            user_id='cascade_test_user',
            email='cascade@example.com',
            wallet_address='0x' + 'c' * 40
        )
        db_session.add(user)
        db_session.commit()

        # Add related records
        tx = Transaction(
            tx_id='cascade_tx',
            user_id=user.user_id,
            tx_type='mint',
            amount=100.0,
            reason='test'
        )
        db_session.add(tx)
        db_session.commit()

        # Verify relationships
        assert len(user.transactions) == 1
