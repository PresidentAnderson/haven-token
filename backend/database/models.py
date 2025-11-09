"""
Database models for HAVEN Token system
"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, ForeignKey, Text, Index
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()


class User(Base):
    """User account with wallet address"""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String(100), unique=True, index=True, nullable=False)
    email = Column(String(255), unique=True, index=True)
    wallet_address = Column(String(42), unique=True, index=True)
    kyc_verified = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    transactions = relationship("Transaction", back_populates="user")
    aurora_bookings = relationship("AuroraBooking", back_populates="user")
    tribe_events = relationship("TribeEvent", back_populates="user")
    staking_records = relationship("StakingRecord", back_populates="user")


class Transaction(Base):
    """Token transaction history"""
    __tablename__ = "transactions"

    id = Column(Integer, primary_key=True, index=True)
    tx_id = Column(String(100), unique=True, index=True, nullable=False)
    user_id = Column(String(100), ForeignKey("users.user_id"), index=True)
    tx_type = Column(String(20), index=True)  # "mint", "burn", "transfer"
    amount = Column(Float, nullable=False)
    reason = Column(Text)
    status = Column(String(20), default="pending", index=True)  # "pending", "confirmed", "failed"
    blockchain_tx = Column(String(66), unique=True, nullable=True, index=True)
    gas_used = Column(Integer, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    confirmed_at = Column(DateTime, nullable=True)

    # Relationships
    user = relationship("User", back_populates="transactions")

    # Indexes for query optimization
    __table_args__ = (
        Index('idx_user_status', 'user_id', 'status'),
        Index('idx_type_created', 'tx_type', 'created_at'),
    )


class AuroraBooking(Base):
    """Aurora PMS booking records"""
    __tablename__ = "aurora_bookings"

    id = Column(Integer, primary_key=True, index=True)
    booking_id = Column(String(100), unique=True, index=True, nullable=False)
    user_id = Column(String(100), ForeignKey("users.user_id"), index=True)
    booking_total = Column(Float, nullable=False)
    nights = Column(Integer, nullable=False)
    reward_tokens = Column(Float, nullable=False)
    status = Column(String(20), default="active", index=True)  # "active", "completed", "cancelled"
    completed_at = Column(DateTime, nullable=True)
    cancelled_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)

    # Relationships
    user = relationship("User", back_populates="aurora_bookings")


class TribeEvent(Base):
    """Tribe app event participation"""
    __tablename__ = "tribe_events"

    id = Column(Integer, primary_key=True, index=True)
    event_id = Column(String(100), unique=True, index=True, nullable=False)
    user_id = Column(String(100), ForeignKey("users.user_id"), index=True)
    event_name = Column(String(255), nullable=False)
    event_type = Column(String(50))  # "attendance", "contribution", "coaching"
    attended = Column(Boolean, default=False)
    tokens_earned = Column(Float, default=0)
    attended_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)

    # Relationships
    user = relationship("User", back_populates="tribe_events")


class TribeReward(Base):
    """Tribe community contribution rewards"""
    __tablename__ = "tribe_rewards"

    id = Column(Integer, primary_key=True, index=True)
    reward_id = Column(String(100), unique=True, index=True, nullable=False)
    user_id = Column(String(100), ForeignKey("users.user_id"), index=True)
    reward_type = Column(String(50), index=True)  # "contribution", "coaching", "staking"
    amount = Column(Float, nullable=False)
    description = Column(Text)
    status = Column(String(20), default="pending")
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    processed_at = Column(DateTime, nullable=True)

    # Relationships
    user = relationship("User")


class StakingRecord(Base):
    """Token staking records"""
    __tablename__ = "staking_records"

    id = Column(Integer, primary_key=True, index=True)
    stake_id = Column(String(100), unique=True, index=True, nullable=False)
    user_id = Column(String(100), ForeignKey("users.user_id"), index=True)
    amount = Column(Float, nullable=False)
    earned_rewards = Column(Float, default=0)
    status = Column(String(20), default="active", index=True)  # "active", "unstaked"
    started_at = Column(DateTime, default=datetime.utcnow, index=True)
    unstaked_at = Column(DateTime, nullable=True)

    # Relationships
    user = relationship("User", back_populates="staking_records")


class RedemptionRequest(Base):
    """Token redemption/payout requests"""
    __tablename__ = "redemption_requests"

    id = Column(Integer, primary_key=True, index=True)
    request_id = Column(String(100), unique=True, index=True, nullable=False)
    user_id = Column(String(100), ForeignKey("users.user_id"), index=True)
    amount = Column(Float, nullable=False)
    withdrawal_method = Column(String(50))  # "bank_transfer", "paypal", "crypto"
    withdrawal_address = Column(String(255))
    status = Column(String(20), default="pending", index=True)  # "pending", "processing", "completed", "failed"
    burn_tx_id = Column(String(66), nullable=True)
    payout_reference = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    processed_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)

    # Relationships
    user = relationship("User")

    # Indexes
    __table_args__ = (
        Index('idx_user_status_redemption', 'user_id', 'status'),
    )


class SystemMetrics(Base):
    """System-wide metrics and analytics"""
    __tablename__ = "system_metrics"

    id = Column(Integer, primary_key=True, index=True)
    metric_name = Column(String(100), index=True, nullable=False)
    metric_value = Column(Float, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    metadata = Column(Text, nullable=True)  # JSON metadata

    __table_args__ = (
        Index('idx_metric_timestamp', 'metric_name', 'timestamp'),
    )
