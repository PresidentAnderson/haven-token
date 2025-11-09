"""
Integration Tests for Tribe App Integration

Tests end-to-end flow for:
1. Event attendance rewards
2. Community contribution rewards
3. Staking mechanics
4. Coaching milestone rewards
5. Referral rewards
"""

import pytest
from datetime import datetime
from unittest.mock import Mock, AsyncMock
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from database.models import Base, User, TribeEvent, TribeReward, StakingRecord, Transaction
from services.tribe_integration import TribeIntegrationService
from services.token_agent import TokenAgent


# ─────────────────────────────────────────────────────────────────────────
# FIXTURES
# ─────────────────────────────────────────────────────────────────────────

@pytest.fixture
def in_memory_db():
    """Create in-memory SQLite database for testing."""
    engine = create_engine('sqlite:///:memory:', echo=False)
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(bind=engine)
    db = SessionLocal()

    yield db

    db.close()
    Base.metadata.drop_all(engine)


@pytest.fixture
def mock_token_agent():
    """Mock token agent to avoid blockchain calls."""
    agent = Mock(spec=TokenAgent)

    async def mock_mint(tx_id, user_id, amount, reason, db):
        tx = Transaction(
            tx_id=tx_id,
            user_id=user_id,
            tx_type="mint",
            amount=amount,
            reason=reason,
            status="confirmed",
            blockchain_tx=f"0x{'a' * 64}",
            created_at=datetime.utcnow(),
            confirmed_at=datetime.utcnow()
        )
        db.add(tx)
        db.commit()
        return f"0x{'a' * 64}"

    agent.process_mint = AsyncMock(side_effect=mock_mint)
    agent.get_balance = Mock(return_value=100.0)

    return agent


@pytest.fixture
def tribe_service(mock_token_agent):
    """Create Tribe service with mocked dependencies."""
    return TribeIntegrationService(mock_token_agent)


@pytest.fixture
def test_user(in_memory_db):
    """Create a test user."""
    user = User(
        user_id="tribe_user_123",
        email="tribe@example.com",
        wallet_address="0x1234567890123456789012345678901234567890",
        kyc_verified=True,
        created_at=datetime.utcnow()
    )
    in_memory_db.add(user)
    in_memory_db.commit()
    return user


# ─────────────────────────────────────────────────────────────────────────
# EVENT ATTENDANCE TESTS
# ─────────────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_event_attendance_wisdom_circle(tribe_service, in_memory_db, test_user, mock_token_agent):
    """Test attending a wisdom circle event (highest reward tier)."""
    event_data = {
        "id": "event_wisdom_001",
        "attendee_id": "tribe_user_123",
        "name": "Monthly Wisdom Circle",
        "type": "wisdom_circle"
    }

    await tribe_service.on_event_attendance(event_data, in_memory_db)

    # Verify event record created
    event = in_memory_db.query(TribeEvent).filter(
        TribeEvent.event_id == "event_wisdom_001"
    ).first()
    assert event is not None
    assert event.event_name == "Monthly Wisdom Circle"
    assert event.event_type == "wisdom_circle"
    assert event.attended == True
    assert event.tokens_earned == 100.0

    # Verify mint called with correct amount
    mock_token_agent.process_mint.assert_called_once()
    call_args = mock_token_agent.process_mint.call_args
    assert call_args.kwargs['amount'] == 100.0
    assert call_args.kwargs['user_id'] == "tribe_user_123"

    # Verify transaction created
    tx = in_memory_db.query(Transaction).filter(
        Transaction.user_id == "tribe_user_123",
        Transaction.tx_type == "mint"
    ).first()
    assert tx is not None
    assert tx.amount == 100.0


@pytest.mark.asyncio
async def test_event_attendance_workshop(tribe_service, in_memory_db, test_user, mock_token_agent):
    """Test attending a workshop event."""
    event_data = {
        "id": "event_workshop_001",
        "attendee_id": "tribe_user_123",
        "name": "Leadership Workshop",
        "type": "workshop"
    }

    await tribe_service.on_event_attendance(event_data, in_memory_db)

    # Verify correct reward (75 HNV for workshop)
    event = in_memory_db.query(TribeEvent).filter(
        TribeEvent.event_id == "event_workshop_001"
    ).first()
    assert event.tokens_earned == 75.0

    call_args = mock_token_agent.process_mint.call_args
    assert call_args.kwargs['amount'] == 75.0


@pytest.mark.asyncio
async def test_event_attendance_networking(tribe_service, in_memory_db, test_user, mock_token_agent):
    """Test attending a networking event."""
    event_data = {
        "id": "event_network_001",
        "attendee_id": "tribe_user_123",
        "name": "Community Networking",
        "type": "networking"
    }

    await tribe_service.on_event_attendance(event_data, in_memory_db)

    # Verify reward (50 HNV for networking)
    event = in_memory_db.query(TribeEvent).first()
    assert event.tokens_earned == 50.0


@pytest.mark.asyncio
async def test_event_attendance_general(tribe_service, in_memory_db, test_user, mock_token_agent):
    """Test attending a general event (minimum reward)."""
    event_data = {
        "id": "event_general_001",
        "attendee_id": "tribe_user_123",
        "name": "Community Meetup",
        "type": "general"
    }

    await tribe_service.on_event_attendance(event_data, in_memory_db)

    # Verify minimum reward (25 HNV)
    event = in_memory_db.query(TribeEvent).first()
    assert event.tokens_earned == 25.0


# ─────────────────────────────────────────────────────────────────────────
# CONTRIBUTION TESTS
# ─────────────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_contribution_guide(tribe_service, in_memory_db, test_user, mock_token_agent):
    """Test submitting a guide contribution (highest value)."""
    contrib_data = {
        "id": "contrib_guide_001",
        "user_id": "tribe_user_123",
        "type": "guide",
        "quality_score": 1.5  # High quality multiplier
    }

    await tribe_service.on_contribution(contrib_data, in_memory_db)

    # Verify reward: base 25 * quality 1.5 = 37.5 HNV
    reward = in_memory_db.query(TribeReward).filter(
        TribeReward.reward_id == "contrib_guide_001"
    ).first()
    assert reward is not None
    assert reward.reward_type == "contribution"
    assert reward.amount == 37.5
    assert reward.status == "processed"

    # Verify mint called
    call_args = mock_token_agent.process_mint.call_args
    assert call_args.kwargs['amount'] == 37.5


@pytest.mark.asyncio
async def test_contribution_resource(tribe_service, in_memory_db, test_user, mock_token_agent):
    """Test sharing a resource."""
    contrib_data = {
        "id": "contrib_resource_001",
        "user_id": "tribe_user_123",
        "type": "resource",
        "quality_score": 1.0
    }

    await tribe_service.on_contribution(contrib_data, in_memory_db)

    # Verify reward: base 15 * quality 1.0 = 15 HNV
    call_args = mock_token_agent.process_mint.call_args
    assert call_args.kwargs['amount'] == 15.0


@pytest.mark.asyncio
async def test_contribution_post(tribe_service, in_memory_db, test_user, mock_token_agent):
    """Test creating a post."""
    contrib_data = {
        "id": "contrib_post_001",
        "user_id": "tribe_user_123",
        "type": "post",
        "quality_score": 1.0
    }

    await tribe_service.on_contribution(contrib_data, in_memory_db)

    # Verify reward: base 10 * quality 1.0 = 10 HNV
    call_args = mock_token_agent.process_mint.call_args
    assert call_args.kwargs['amount'] == 10.0


@pytest.mark.asyncio
async def test_contribution_comment(tribe_service, in_memory_db, test_user, mock_token_agent):
    """Test posting a comment."""
    contrib_data = {
        "id": "contrib_comment_001",
        "user_id": "tribe_user_123",
        "type": "comment",
        "quality_score": 1.0
    }

    await tribe_service.on_contribution(contrib_data, in_memory_db)

    # Verify reward: base 5 * quality 1.0 = 5 HNV
    call_args = mock_token_agent.process_mint.call_args
    assert call_args.kwargs['amount'] == 5.0


@pytest.mark.asyncio
async def test_contribution_quality_multiplier(tribe_service, in_memory_db, test_user, mock_token_agent):
    """Test quality score multiplier effect."""
    # High quality post
    contrib_data = {
        "id": "contrib_hq_001",
        "user_id": "tribe_user_123",
        "type": "post",
        "quality_score": 2.0  # 2x multiplier
    }

    await tribe_service.on_contribution(contrib_data, in_memory_db)

    # Verify reward: base 10 * quality 2.0 = 20 HNV
    call_args = mock_token_agent.process_mint.call_args
    assert call_args.kwargs['amount'] == 20.0


# ─────────────────────────────────────────────────────────────────────────
# STAKING TESTS
# ─────────────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_staking_started(tribe_service, in_memory_db, test_user):
    """Test initiating token staking."""
    stake_data = {
        "id": "stake_001",
        "user_id": "tribe_user_123",
        "amount": 1000.0
    }

    await tribe_service.on_staking_started(stake_data, in_memory_db)

    # Verify staking record created
    stake = in_memory_db.query(StakingRecord).filter(
        StakingRecord.stake_id == "stake_001"
    ).first()
    assert stake is not None
    assert stake.user_id == "tribe_user_123"
    assert stake.amount == 1000.0
    assert stake.status == "active"
    assert stake.earned_rewards == 0.0


@pytest.mark.asyncio
async def test_staking_rewards_calculation(tribe_service, in_memory_db, test_user, mock_token_agent):
    """Test weekly staking rewards calculation (10% APY)."""
    # Setup: Create active stakes
    stakes = [
        StakingRecord(
            stake_id="stake_001",
            user_id="tribe_user_123",
            amount=1000.0,
            status="active",
            started_at=datetime.utcnow()
        ),
        StakingRecord(
            stake_id="stake_002",
            user_id="tribe_user_123",
            amount=500.0,
            status="active",
            started_at=datetime.utcnow()
        )
    ]
    for stake in stakes:
        in_memory_db.add(stake)
    in_memory_db.commit()

    # Execute rewards calculation
    await tribe_service.calculate_staking_rewards(in_memory_db)

    # Verify rewards calculated
    # Weekly rate = 10% APY / 52 weeks = 0.192% weekly
    weekly_rate = 0.10 / 52

    stake1 = in_memory_db.query(StakingRecord).filter(
        StakingRecord.stake_id == "stake_001"
    ).first()
    expected_reward_1 = 1000.0 * weekly_rate
    assert abs(stake1.earned_rewards - expected_reward_1) < 0.01

    stake2 = in_memory_db.query(StakingRecord).filter(
        StakingRecord.stake_id == "stake_002"
    ).first()
    expected_reward_2 = 500.0 * weekly_rate
    assert abs(stake2.earned_rewards - expected_reward_2) < 0.01

    # Verify mint called twice (once per stake)
    assert mock_token_agent.process_mint.call_count == 2


@pytest.mark.asyncio
async def test_staking_rewards_skip_unstaked(tribe_service, in_memory_db, test_user, mock_token_agent):
    """Test that unstaked positions don't earn rewards."""
    # Setup: One active, one unstaked
    stake_active = StakingRecord(
        stake_id="stake_active",
        user_id="tribe_user_123",
        amount=1000.0,
        status="active",
        started_at=datetime.utcnow()
    )
    stake_unstaked = StakingRecord(
        stake_id="stake_unstaked",
        user_id="tribe_user_123",
        amount=500.0,
        status="unstaked",
        started_at=datetime.utcnow(),
        unstaked_at=datetime.utcnow()
    )
    in_memory_db.add(stake_active)
    in_memory_db.add(stake_unstaked)
    in_memory_db.commit()

    await tribe_service.calculate_staking_rewards(in_memory_db)

    # Verify only active stake earned rewards
    active = in_memory_db.query(StakingRecord).filter(
        StakingRecord.stake_id == "stake_active"
    ).first()
    assert active.earned_rewards > 0

    unstaked = in_memory_db.query(StakingRecord).filter(
        StakingRecord.stake_id == "stake_unstaked"
    ).first()
    assert unstaked.earned_rewards == 0

    # Verify mint called only once
    assert mock_token_agent.process_mint.call_count == 1


# ─────────────────────────────────────────────────────────────────────────
# COACHING MILESTONE TESTS
# ─────────────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_coaching_milestone_basic(tribe_service, in_memory_db, test_user, mock_token_agent):
    """Test basic tier coaching milestone."""
    milestone_data = {
        "user_id": "tribe_user_123",
        "milestone_name": "First Session Complete",
        "tier": "basic"
    }

    await tribe_service.on_coaching_milestone(milestone_data, in_memory_db)

    # Verify reward (100 HNV for basic)
    call_args = mock_token_agent.process_mint.call_args
    assert call_args.kwargs['amount'] == 100.0

    # Verify reward record
    reward = in_memory_db.query(TribeReward).filter(
        TribeReward.reward_type == "coaching"
    ).first()
    assert reward is not None
    assert reward.amount == 100.0
    assert reward.status == "processed"


@pytest.mark.asyncio
async def test_coaching_milestone_intermediate(tribe_service, in_memory_db, test_user, mock_token_agent):
    """Test intermediate tier coaching milestone."""
    milestone_data = {
        "user_id": "tribe_user_123",
        "milestone_name": "Goal Achievement",
        "tier": "intermediate"
    }

    await tribe_service.on_coaching_milestone(milestone_data, in_memory_db)

    # Verify reward (175 HNV for intermediate)
    call_args = mock_token_agent.process_mint.call_args
    assert call_args.kwargs['amount'] == 175.0


@pytest.mark.asyncio
async def test_coaching_milestone_advanced(tribe_service, in_memory_db, test_user, mock_token_agent):
    """Test advanced tier coaching milestone."""
    milestone_data = {
        "user_id": "tribe_user_123",
        "milestone_name": "Program Graduation",
        "tier": "advanced"
    }

    await tribe_service.on_coaching_milestone(milestone_data, in_memory_db)

    # Verify reward (250 HNV for advanced)
    call_args = mock_token_agent.process_mint.call_args
    assert call_args.kwargs['amount'] == 250.0


# ─────────────────────────────────────────────────────────────────────────
# REFERRAL TESTS
# ─────────────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_referral_basic_tier(tribe_service, in_memory_db, test_user, mock_token_agent):
    """Test basic tier referral reward."""
    referral_data = {
        "referrer_id": "tribe_user_123",
        "referred_id": "new_user_456",
        "tier": "basic"
    }

    await tribe_service.on_referral_success(referral_data, in_memory_db)

    # Verify reward (100 HNV for basic)
    call_args = mock_token_agent.process_mint.call_args
    assert call_args.kwargs['amount'] == 100.0
    assert call_args.kwargs['user_id'] == "tribe_user_123"


@pytest.mark.asyncio
async def test_referral_silver_tier(tribe_service, in_memory_db, test_user, mock_token_agent):
    """Test silver tier referral reward."""
    referral_data = {
        "referrer_id": "tribe_user_123",
        "referred_id": "new_user_456",
        "tier": "silver"
    }

    await tribe_service.on_referral_success(referral_data, in_memory_db)

    # Verify reward (250 HNV for silver)
    call_args = mock_token_agent.process_mint.call_args
    assert call_args.kwargs['amount'] == 250.0


@pytest.mark.asyncio
async def test_referral_gold_tier(tribe_service, in_memory_db, test_user, mock_token_agent):
    """Test gold tier referral reward (highest)."""
    referral_data = {
        "referrer_id": "tribe_user_123",
        "referred_id": "new_user_456",
        "tier": "gold"
    }

    await tribe_service.on_referral_success(referral_data, in_memory_db)

    # Verify reward (500 HNV for gold)
    call_args = mock_token_agent.process_mint.call_args
    assert call_args.kwargs['amount'] == 500.0


# ─────────────────────────────────────────────────────────────────────────
# ERROR HANDLING TESTS
# ─────────────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_event_attendance_nonexistent_user(tribe_service, in_memory_db, mock_token_agent):
    """Test event attendance for non-existent user."""
    event_data = {
        "id": "event_001",
        "attendee_id": "nonexistent_user",
        "name": "Test Event",
        "type": "general"
    }

    # Should not raise error, just log and return
    await tribe_service.on_event_attendance(event_data, in_memory_db)

    # Verify no mint called
    mock_token_agent.process_mint.assert_not_called()


@pytest.mark.asyncio
async def test_contribution_nonexistent_user(tribe_service, in_memory_db, mock_token_agent):
    """Test contribution for non-existent user."""
    contrib_data = {
        "id": "contrib_001",
        "user_id": "nonexistent_user",
        "type": "post",
        "quality_score": 1.0
    }

    await tribe_service.on_contribution(contrib_data, in_memory_db)

    # Should not process
    mock_token_agent.process_mint.assert_not_called()
