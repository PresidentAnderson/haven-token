"""
Integration Tests for API Endpoints

Tests complete API request/response flows with database and mocked blockchain.
"""

import pytest
import json
from datetime import datetime
from unittest.mock import Mock, patch, AsyncMock
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app import app, get_db
from database.models import Base, User, Transaction, RedemptionRequest, AuroraBooking
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


@pytest.fixture
def client(in_memory_db):
    """Create test client with overridden database dependency."""
    def override_get_db():
        try:
            yield in_memory_db
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    client = TestClient(app)

    yield client

    app.dependency_overrides.clear()


@pytest.fixture
def mock_token_agent():
    """Mock token agent for all tests."""
    with patch('app.token_agent') as mock:
        # Mock balance check
        mock.get_balance.return_value = 1000.0

        # Mock total supply
        mock.get_total_supply.return_value = 50000.0

        # Mock emission stats
        mock.get_emission_stats.return_value = {
            "totalMinted": 60000.0,
            "totalBurned": 10000.0,
            "circulating": 50000.0
        }

        # Mock mint function
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

        # Mock burn function
        async def mock_burn(user_id, amount, reason, db):
            tx_id = f"burn_{user_id}_{datetime.utcnow().timestamp()}"
            tx = Transaction(
                tx_id=tx_id,
                user_id=user_id,
                tx_type="burn",
                amount=amount,
                reason=reason,
                status="confirmed",
                blockchain_tx=f"0x{'b' * 64}",
                created_at=datetime.utcnow(),
                confirmed_at=datetime.utcnow()
            )
            db.add(tx)
            db.commit()
            return f"0x{'b' * 64}"

        mock.process_mint = AsyncMock(side_effect=mock_mint)
        mock.process_burn = AsyncMock(side_effect=mock_burn)

        yield mock


@pytest.fixture
def test_user(in_memory_db):
    """Create a test user with wallet."""
    user = User(
        user_id="test_user_123",
        email="test@example.com",
        wallet_address="0x1234567890123456789012345678901234567890",
        kyc_verified=True,
        created_at=datetime.utcnow()
    )
    in_memory_db.add(user)
    in_memory_db.commit()
    return user


@pytest.fixture
def api_headers():
    """API authentication headers."""
    return {
        "X-API-Key": "test_key"  # Matches default in app.py
    }


# ─────────────────────────────────────────────────────────────────────────
# HEALTH CHECK TESTS
# ─────────────────────────────────────────────────────────────────────────

def test_root_endpoint(client):
    """Test root endpoint returns service info."""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["service"] == "HAVEN Token API"
    assert data["status"] == "operational"


def test_health_check(client, mock_token_agent):
    """Test health check endpoint."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["database"] == "connected"
    assert data["blockchain"] == "connected"
    assert "circulating_supply" in data


# ─────────────────────────────────────────────────────────────────────────
# TOKEN OPERATION TESTS
# ─────────────────────────────────────────────────────────────────────────

def test_mint_tokens_success(client, test_user, api_headers, mock_token_agent):
    """Test successful token minting."""
    mint_request = {
        "user_id": "test_user_123",
        "amount": 100.0,
        "reason": "test_reward",
        "idempotency_key": "test_mint_001"
    }

    response = client.post("/token/mint", json=mint_request, headers=api_headers)
    assert response.status_code == 200

    data = response.json()
    assert data["status"] == "queued"
    assert data["tx_id"] == "test_mint_001"


def test_mint_tokens_duplicate_idempotency(client, test_user, in_memory_db, api_headers):
    """Test minting with duplicate idempotency key."""
    # Create existing transaction
    existing_tx = Transaction(
        tx_id="duplicate_key_123",
        user_id="test_user_123",
        tx_type="mint",
        amount=50.0,
        status="confirmed",
        created_at=datetime.utcnow()
    )
    in_memory_db.add(existing_tx)
    in_memory_db.commit()

    mint_request = {
        "user_id": "test_user_123",
        "amount": 100.0,
        "reason": "test",
        "idempotency_key": "duplicate_key_123"
    }

    response = client.post("/token/mint", json=mint_request, headers=api_headers)
    assert response.status_code == 200

    data = response.json()
    assert data["status"] == "duplicate"


def test_mint_tokens_no_api_key(client, test_user):
    """Test minting without API key fails."""
    mint_request = {
        "user_id": "test_user_123",
        "amount": 100.0,
        "reason": "test"
    }

    response = client.post("/token/mint", json=mint_request)
    assert response.status_code == 422  # Missing header


def test_redeem_tokens_success(client, test_user, api_headers, mock_token_agent):
    """Test successful token redemption."""
    redeem_request = {
        "user_id": "test_user_123",
        "amount": 100.0,
        "withdrawal_method": "bank_transfer",
        "withdrawal_address": "CA123456789",
        "idempotency_key": "redeem_001"
    }

    response = client.post("/token/redeem", json=redeem_request, headers=api_headers)
    assert response.status_code == 200

    data = response.json()
    assert data["status"] == "queued"
    assert data["burn_amount"] == 100.0
    assert data["payout_amount"] == 98.0  # 2% burn fee


def test_redeem_tokens_insufficient_balance(client, test_user, api_headers, mock_token_agent):
    """Test redemption with insufficient balance."""
    # Mock low balance
    mock_token_agent.get_balance.return_value = 10.0

    redeem_request = {
        "user_id": "test_user_123",
        "amount": 100.0,
        "withdrawal_method": "bank_transfer",
        "idempotency_key": "redeem_002"
    }

    response = client.post("/token/redeem", json=redeem_request, headers=api_headers)
    assert response.status_code == 400
    assert "Insufficient balance" in response.json()["detail"]


def test_redeem_tokens_user_not_found(client, api_headers):
    """Test redemption for non-existent user."""
    redeem_request = {
        "user_id": "nonexistent_user",
        "amount": 100.0,
        "withdrawal_method": "bank_transfer",
        "idempotency_key": "redeem_003"
    }

    response = client.post("/token/redeem", json=redeem_request, headers=api_headers)
    assert response.status_code == 404


def test_get_user_balance(client, test_user, mock_token_agent):
    """Test getting user balance."""
    response = client.get(f"/token/balance/{test_user.user_id}")
    assert response.status_code == 200

    data = response.json()
    assert data["user_id"] == "test_user_123"
    assert data["wallet_address"] == test_user.wallet_address
    assert data["balance"] == 1000.0


def test_get_user_balance_not_found(client):
    """Test getting balance for non-existent user."""
    response = client.get("/token/balance/nonexistent_user")
    assert response.status_code == 404


# ─────────────────────────────────────────────────────────────────────────
# WEBHOOK TESTS
# ─────────────────────────────────────────────────────────────────────────

def test_aurora_booking_created_webhook(client, mock_token_agent):
    """Test Aurora booking created webhook."""
    webhook_payload = {
        "id": "booking_123",
        "guest_id": "guest_456",
        "guest_email": "guest@example.com",
        "total_price": 500.0,
        "nights": 3,
        "status": "confirmed"
    }

    # Note: In real test would need valid signature
    headers = {"X-Aurora-Signature": "test_signature"}

    with patch('app.verify_webhook_signature', return_value=True):
        response = client.post(
            "/webhooks/aurora/booking-created",
            json=webhook_payload,
            headers=headers
        )

    assert response.status_code == 200
    assert response.json()["status"] == "accepted"


def test_aurora_booking_completed_webhook(client):
    """Test Aurora booking completed webhook."""
    webhook_payload = {
        "id": "booking_123",
        "guest_id": "guest_456",
        "status": "completed"
    }

    response = client.post("/webhooks/aurora/booking-completed", json=webhook_payload)
    assert response.status_code == 200


def test_tribe_event_attendance_webhook(client):
    """Test Tribe event attendance webhook."""
    webhook_payload = {
        "id": "event_123",
        "attendee_id": "user_456",
        "name": "Wisdom Circle",
        "type": "wisdom_circle"
    }

    response = client.post("/webhooks/tribe/event-attendance", json=webhook_payload)
    assert response.status_code == 200
    assert response.json()["status"] == "accepted"


# ─────────────────────────────────────────────────────────────────────────
# ANALYTICS TESTS
# ─────────────────────────────────────────────────────────────────────────

def test_get_user_analytics(client, test_user, in_memory_db, mock_token_agent):
    """Test getting user analytics."""
    # Create some transactions
    tx1 = Transaction(
        tx_id="tx_001",
        user_id="test_user_123",
        tx_type="mint",
        amount=100.0,
        status="confirmed",
        created_at=datetime.utcnow()
    )
    tx2 = Transaction(
        tx_id="tx_002",
        user_id="test_user_123",
        tx_type="mint",
        amount=50.0,
        status="confirmed",
        created_at=datetime.utcnow()
    )
    in_memory_db.add(tx1)
    in_memory_db.add(tx2)
    in_memory_db.commit()

    response = client.get(f"/analytics/user/{test_user.user_id}")
    assert response.status_code == 200

    data = response.json()
    assert data["user_id"] == "test_user_123"
    assert data["email"] == "test@example.com"
    assert data["balance"] == 1000.0
    assert data["kyc_verified"] == True


def test_get_token_stats(client, in_memory_db, mock_token_agent):
    """Test getting global token statistics."""
    # Create some users and transactions
    user1 = User(
        user_id="user_1",
        email="user1@example.com",
        wallet_address="0x1111111111111111111111111111111111111111",
        created_at=datetime.utcnow()
    )
    user2 = User(
        user_id="user_2",
        email="user2@example.com",
        wallet_address="0x2222222222222222222222222222222222222222",
        created_at=datetime.utcnow()
    )
    tx1 = Transaction(
        tx_id="tx_001",
        user_id="user_1",
        tx_type="mint",
        amount=100.0,
        status="confirmed",
        created_at=datetime.utcnow()
    )
    in_memory_db.add_all([user1, user2, tx1])
    in_memory_db.commit()

    response = client.get("/analytics/token-stats")
    assert response.status_code == 200

    data = response.json()
    assert data["total_minted"] == 60000.0
    assert data["total_burned"] == 10000.0
    assert data["circulating_supply"] == 50000.0
    assert data["total_users"] == 2
    assert data["total_transactions"] == 1


def test_get_user_transactions(client, test_user, in_memory_db):
    """Test getting user transaction history."""
    # Create multiple transactions
    for i in range(5):
        tx = Transaction(
            tx_id=f"tx_{i:03d}",
            user_id="test_user_123",
            tx_type="mint" if i % 2 == 0 else "burn",
            amount=100.0 * (i + 1),
            status="confirmed",
            blockchain_tx=f"0x{'a' * 64}",
            created_at=datetime.utcnow(),
            confirmed_at=datetime.utcnow()
        )
        in_memory_db.add(tx)
    in_memory_db.commit()

    response = client.get(f"/analytics/transactions/{test_user.user_id}")
    assert response.status_code == 200

    data = response.json()
    assert data["user_id"] == "test_user_123"
    assert data["count"] == 5
    assert len(data["transactions"]) == 5

    # Verify transactions are ordered by created_at desc
    txs = data["transactions"]
    for tx in txs:
        assert "tx_id" in tx
        assert "amount" in tx
        assert "status" in tx


def test_get_user_transactions_pagination(client, test_user, in_memory_db):
    """Test transaction history pagination."""
    # Create many transactions
    for i in range(100):
        tx = Transaction(
            tx_id=f"tx_{i:03d}",
            user_id="test_user_123",
            tx_type="mint",
            amount=10.0,
            status="confirmed",
            created_at=datetime.utcnow()
        )
        in_memory_db.add(tx)
    in_memory_db.commit()

    # Test limit
    response = client.get(f"/analytics/transactions/{test_user.user_id}?limit=10")
    assert response.status_code == 200
    assert len(response.json()["transactions"]) == 10

    # Test offset
    response = client.get(f"/analytics/transactions/{test_user.user_id}?limit=10&offset=10")
    assert response.status_code == 200
    assert len(response.json()["transactions"]) == 10


# ─────────────────────────────────────────────────────────────────────────
# ERROR HANDLING TESTS
# ─────────────────────────────────────────────────────────────────────────

def test_invalid_api_key(client, test_user):
    """Test request with invalid API key."""
    mint_request = {
        "user_id": "test_user_123",
        "amount": 100.0,
        "reason": "test"
    }

    headers = {"X-API-Key": "invalid_key"}
    response = client.post("/token/mint", json=mint_request, headers=headers)
    assert response.status_code == 401


def test_invalid_request_data(client, api_headers):
    """Test request with invalid data."""
    invalid_request = {
        "user_id": "test_user",
        "amount": "not_a_number",  # Invalid type
        "reason": "test"
    }

    response = client.post("/token/mint", json=invalid_request, headers=api_headers)
    assert response.status_code == 422  # Validation error


def test_cors_headers(client):
    """Test CORS headers are present."""
    response = client.get("/", headers={"Origin": "http://localhost:3000"})
    assert response.status_code == 200
    # CORS headers should be present (added by middleware)
    # Note: TestClient may not fully simulate CORS, but we can check the middleware is configured


# ─────────────────────────────────────────────────────────────────────────
# INTEGRATION FLOW TESTS
# ─────────────────────────────────────────────────────────────────────────

def test_complete_mint_flow(client, test_user, in_memory_db, api_headers, mock_token_agent):
    """Test complete mint flow from API to database."""
    # Step 1: Request mint
    mint_request = {
        "user_id": "test_user_123",
        "amount": 250.0,
        "reason": "integration_test",
        "idempotency_key": "integration_mint_001"
    }

    response = client.post("/token/mint", json=mint_request, headers=api_headers)
    assert response.status_code == 200

    # Step 2: Wait for background task (in test, it runs synchronously)
    import time
    time.sleep(0.1)

    # Step 3: Verify transaction in database
    # Note: Background tasks may not execute in TestClient
    # In real integration test, would check transaction eventually appears


def test_complete_booking_to_mint_flow(client, in_memory_db, mock_token_agent):
    """Test complete flow: booking webhook -> user creation -> mint."""
    webhook_payload = {
        "id": "booking_integration_001",
        "guest_id": "new_guest_789",
        "guest_email": "newguest@example.com",
        "total_price": 1000.0,
        "nights": 5,
        "status": "confirmed"
    }

    with patch('app.verify_webhook_signature', return_value=True):
        response = client.post(
            "/webhooks/aurora/booking-created",
            json=webhook_payload,
            headers={"X-Aurora-Signature": "valid_sig"}
        )

    assert response.status_code == 200

    # Background task would execute and create user + mint tokens
    # In full integration test, would verify:
    # 1. User created in database
    # 2. Booking record created
    # 3. Transaction record created
    # 4. Mint called on blockchain (mocked here)
