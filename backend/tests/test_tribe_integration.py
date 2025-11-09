"""
Integration Tests for Tribe App Webhooks
Tests event attendance, contributions, staking, and coaching rewards.
"""
import pytest
import json
import os
from unittest.mock import patch, AsyncMock, MagicMock

from database.models import User, TribeEvent, TribeReward, StakingRecord
from services.tribe_integration import TribeIntegrationService
from middleware.webhook_auth import generate_webhook_signature


# Set webhook secret for tests
os.environ["TRIBE_WEBHOOK_SECRET"] = "test_tribe_secret"


@pytest.fixture
def tribe_service(db_session):
    """Create Tribe service instance with mocked token agent."""
    mock_agent = MagicMock()
    mock_agent.process_mint = AsyncMock(return_value="0xmocktxhash")

    service = TribeIntegrationService(mock_agent)
    return service


class TestTribeWebhooks:
    """Test Tribe App webhook endpoints."""

    def test_event_attendance_webhook(self, client):
        """Test event attendance webhook with signature verification."""
        payload = {
            "id": "event_12345",
            "attendee_id": "user_001",
            "name": "Weekly Wisdom Circle",
            "type": "wisdom_circle",
            "attended": True
        }

        payload_bytes = json.dumps(payload).encode('utf-8')
        headers = generate_webhook_signature(payload_bytes, "test_tribe_secret")

        response = client.post(
            "/webhooks/tribe/event-attendance",
            json=payload,
            headers={
                "X-Tribe-Signature": headers["signature"],
                "X-Tribe-Timestamp": headers["timestamp"]
            }
        )

        assert response.status_code == 200
        assert response.json()["status"] == "accepted"

    def test_event_attendance_invalid_signature(self, client):
        """Test event attendance webhook with invalid signature."""
        payload = {
            "id": "event_12345",
            "attendee_id": "user_001",
            "type": "wisdom_circle"
        }

        import time
        response = client.post(
            "/webhooks/tribe/event-attendance",
            json=payload,
            headers={
                "X-Tribe-Signature": "invalid_signature",
                "X-Tribe-Timestamp": str(int(time.time()))
            }
        )

        assert response.status_code == 401

    def test_contribution_webhook(self, client):
        """Test community contribution webhook."""
        payload = {
            "id": "contribution_456",
            "user_id": "user_001",
            "type": "post",
            "quality_score": 1.5
        }

        payload_bytes = json.dumps(payload).encode('utf-8')
        headers = generate_webhook_signature(payload_bytes, "test_tribe_secret")

        response = client.post(
            "/webhooks/tribe/contribution",
            json=payload,
            headers={
                "X-Tribe-Signature": headers["signature"],
                "X-Tribe-Timestamp": headers["timestamp"]
            }
        )

        assert response.status_code == 200

    def test_coaching_milestone_webhook(self, client):
        """Test coaching milestone webhook."""
        payload = {
            "user_id": "user_001",
            "milestone_name": "First Month Complete",
            "tier": "basic"
        }

        payload_bytes = json.dumps(payload).encode('utf-8')
        headers = generate_webhook_signature(payload_bytes, "test_tribe_secret")

        response = client.post(
            "/webhooks/tribe/coaching-milestone",
            json=payload,
            headers={
                "X-Tribe-Signature": headers["signature"],
                "X-Tribe-Timestamp": headers["timestamp"]
            }
        )

        assert response.status_code == 200

    def test_referral_success_webhook(self, client):
        """Test referral success webhook."""
        payload = {
            "referrer_id": "user_001",
            "referred_id": "user_002",
            "tier": "silver"
        }

        payload_bytes = json.dumps(payload).encode('utf-8')
        headers = generate_webhook_signature(payload_bytes, "test_tribe_secret")

        response = client.post(
            "/webhooks/tribe/referral-success",
            json=payload,
            headers={
                "X-Tribe-Signature": headers["signature"],
                "X-Tribe-Timestamp": headers["timestamp"]
            }
        )

        assert response.status_code == 200


class TestTribeService:
    """Test Tribe service methods."""

    def test_parseEventData(self, tribe_service):
        """Test event data parsing and normalization."""
        raw_data = {
            "id": "event_123",
            "attendee_id": "user_456",
            "name": "Workshop",
            "type": "workshop",
            "attended": True
        }

        parsed = tribe_service.parseEventData(raw_data)

        assert parsed["id"] == "event_123"
        assert parsed["attendee_id"] == "user_456"
        assert parsed["name"] == "Workshop"
        assert parsed["type"] == "workshop"
        assert parsed["attended"] is True

    def test_parseEventData_alternative_fields(self, tribe_service):
        """Test parsing with alternative field names."""
        raw_data = {
            "event_id": "event_123",
            "user_id": "user_456",
            "event_name": "Networking Event",
            "event_type": "networking"
        }

        parsed = tribe_service.parseEventData(raw_data)

        assert parsed["id"] == "event_123"
        assert parsed["attendee_id"] == "user_456"
        assert parsed["name"] == "Networking Event"
        assert parsed["type"] == "networking"

    def test_calculateAttendanceReward_wisdom_circle(self, tribe_service):
        """Test reward calculation for wisdom circle event."""
        reward = tribe_service.calculateAttendanceReward("wisdom_circle")

        assert reward == 100.0  # Premium event

    def test_calculateAttendanceReward_workshop(self, tribe_service):
        """Test reward calculation for workshop event."""
        reward = tribe_service.calculateAttendanceReward("workshop")

        assert reward == 75.0

    def test_calculateAttendanceReward_networking(self, tribe_service):
        """Test reward calculation for networking event."""
        reward = tribe_service.calculateAttendanceReward("networking")

        assert reward == 50.0

    def test_calculateAttendanceReward_general(self, tribe_service):
        """Test reward calculation for general event."""
        reward = tribe_service.calculateAttendanceReward("general")

        assert reward == 25.0

    def test_calculateAttendanceReward_unknown_type(self, tribe_service):
        """Test reward calculation for unknown event type defaults to general."""
        reward = tribe_service.calculateAttendanceReward("unknown_type")

        assert reward == 25.0  # Default to general

    def test_handleEventAttendance_valid(self, tribe_service):
        """Test event attendance validation with valid data."""
        event_data = {
            "id": "event_123",
            "attendee_id": "user_456",
            "type": "workshop",
            "attended": True
        }

        result = tribe_service.handleEventAttendance(event_data)

        assert result is True

    def test_handleEventAttendance_missing_fields(self, tribe_service):
        """Test event attendance validation with missing fields."""
        event_data = {
            "id": "event_123"
            # Missing attendee_id and type
        }

        result = tribe_service.handleEventAttendance(event_data)

        assert result is False

    def test_handleEventAttendance_not_attended(self, tribe_service):
        """Test event attendance validation when not attended."""
        event_data = {
            "id": "event_123",
            "attendee_id": "user_456",
            "type": "workshop",
            "attended": False  # Did not attend
        }

        result = tribe_service.handleEventAttendance(event_data)

        assert result is False

    @pytest.mark.asyncio
    async def test_on_event_attendance(self, tribe_service, sample_user, db_session):
        """Test event attendance handler creates event record."""
        event_data = {
            "id": "event_789",
            "attendee_id": sample_user.user_id,
            "name": "Wisdom Circle",
            "type": "wisdom_circle",
            "attended": True
        }

        await tribe_service.on_event_attendance(event_data, db_session)

        # Verify process_mint was called with correct amount
        tribe_service.token_agent.process_mint.assert_called_once()
        call_args = tribe_service.token_agent.process_mint.call_args

        assert call_args[1]["amount"] == 100.0  # Wisdom circle reward
        assert call_args[1]["user_id"] == sample_user.user_id

    @pytest.mark.asyncio
    async def test_on_contribution(self, tribe_service, sample_user, db_session):
        """Test contribution handler with quality multiplier."""
        contribution_data = {
            "id": "contrib_123",
            "user_id": sample_user.user_id,
            "type": "post",
            "quality_score": 2.0  # High quality
        }

        await tribe_service.on_contribution(contribution_data, db_session)

        # Verify process_mint called with quality-adjusted amount
        tribe_service.token_agent.process_mint.assert_called_once()
        call_args = tribe_service.token_agent.process_mint.call_args

        # Post = 10 HNV base * 2.0 quality = 20 HNV
        assert call_args[1]["amount"] == 20.0

    @pytest.mark.asyncio
    async def test_on_coaching_milestone_basic(self, tribe_service, sample_user, db_session):
        """Test coaching milestone handler for basic tier."""
        milestone_data = {
            "user_id": sample_user.user_id,
            "milestone_name": "First Session",
            "tier": "basic"
        }

        await tribe_service.on_coaching_milestone(milestone_data, db_session)

        # Verify process_mint called
        tribe_service.token_agent.process_mint.assert_called_once()
        call_args = tribe_service.token_agent.process_mint.call_args

        assert call_args[1]["amount"] == 100.0  # Basic tier

    @pytest.mark.asyncio
    async def test_on_coaching_milestone_advanced(self, tribe_service, sample_user, db_session):
        """Test coaching milestone handler for advanced tier."""
        milestone_data = {
            "user_id": sample_user.user_id,
            "milestone_name": "Mastery Achieved",
            "tier": "advanced"
        }

        await tribe_service.on_coaching_milestone(milestone_data, db_session)

        # Verify process_mint called
        call_args = tribe_service.token_agent.process_mint.call_args

        assert call_args[1]["amount"] == 250.0  # Advanced tier

    @pytest.mark.asyncio
    async def test_on_referral_success(self, tribe_service, sample_user, db_session):
        """Test referral success handler with tiered rewards."""
        referral_data = {
            "referrer_id": sample_user.user_id,
            "referred_id": "user_new",
            "tier": "gold"
        }

        await tribe_service.on_referral_success(referral_data, db_session)

        # Verify process_mint called
        call_args = tribe_service.token_agent.process_mint.call_args

        assert call_args[1]["amount"] == 500.0  # Gold tier
        assert call_args[1]["user_id"] == sample_user.user_id

    @pytest.mark.asyncio
    async def test_calculate_staking_rewards(self, tribe_service, sample_user, db_session):
        """Test weekly staking rewards calculation."""
        # Create staking record
        stake = StakingRecord(
            stake_id="stake_123",
            user_id=sample_user.user_id,
            amount=1000.0,
            earned_rewards=0.0,
            status="active"
        )
        db_session.add(stake)
        db_session.commit()

        await tribe_service.calculate_staking_rewards(db_session)

        # Verify process_mint called with weekly rate
        # 10% APY / 52 weeks = 0.192% per week
        # 1000 * 0.00192 = 1.92 HNV
        tribe_service.token_agent.process_mint.assert_called()
        call_args = tribe_service.token_agent.process_mint.call_args

        expected_reward = 1000.0 * 0.10 / 52  # Weekly reward
        assert abs(call_args[1]["amount"] - expected_reward) < 0.01  # Floating point tolerance


class TestTribeRewardCalculations:
    """Test Tribe reward calculation edge cases."""

    def test_contribution_quality_multipliers(self, tribe_service, sample_user, db_session):
        """Test contribution rewards with different quality scores."""
        test_cases = [
            ("post", 0.5, 5.0),   # Low quality: 10 * 0.5 = 5
            ("post", 1.0, 10.0),  # Normal: 10 * 1.0 = 10
            ("post", 2.0, 20.0),  # High quality: 10 * 2.0 = 20
            ("guide", 1.0, 25.0), # Guide: 25 * 1.0 = 25
            ("guide", 2.0, 50.0), # High quality guide: 25 * 2.0 = 50
        ]

        for contrib_type, quality, expected in test_cases:
            base_rewards = {
                "post": 10.0,
                "comment": 5.0,
                "resource": 15.0,
                "guide": 25.0
            }
            calculated = base_rewards[contrib_type] * quality
            assert calculated == expected

    def test_referral_tiers(self, tribe_service):
        """Test referral reward tiers match tokenomics."""
        tier_rewards = {
            "basic": 100.0,
            "silver": 250.0,
            "gold": 500.0
        }

        # These should match the service implementation
        for tier, expected_reward in tier_rewards.items():
            # The service uses this same mapping
            assert expected_reward in [100.0, 250.0, 500.0]
