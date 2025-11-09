# HAVEN Token: Test Implementation Guide

**Technical Reference for Building the Test Suite**
**Version:** 1.0
**Created:** November 2025

---

## Table of Contents

1. [Backend Test Setup](#1-backend-test-setup)
2. [API Endpoint Tests](#2-api-endpoint-tests)
3. [Service Layer Tests](#3-service-layer-tests)
4. [Integration Test Examples](#4-integration-test-examples)
5. [Webhook Testing](#5-webhook-testing)
6. [Load Test Configuration](#6-load-test-configuration)
7. [CI/CD Integration](#7-cicd-integration)

---

## 1. Backend Test Setup

### 1.1 Project Structure

```
backend/
├── app.py
├── database/
│   └── models.py
├── services/
│   ├── token_agent.py
│   ├── aurora_integration.py
│   └── tribe_integration.py
├── requirements.txt
├── requirements-dev.txt           # NEW: Test dependencies
├── tests/
│   ├── __init__.py
│   ├── conftest.py               # NEW: Pytest configuration
│   ├── test_api_endpoints.py     # NEW: API tests
│   ├── test_services.py          # NEW: Service tests
│   ├── test_integration.py       # NEW: Integration tests
│   ├── test_webhooks.py          # NEW: Webhook tests
│   └── fixtures/
│       └── test_data.py          # NEW: Test data factories
└── pytest.ini                     # NEW: Pytest config
```

### 1.2 Install Test Dependencies

**File:** `backend/requirements-dev.txt`

```
# Existing dependencies (from requirements.txt)
fastapi==0.104.0
sqlalchemy==2.0.0
pydantic==2.0.0
web3==6.10.0
python-dotenv==1.0.0

# Testing dependencies
pytest==7.4.0
pytest-asyncio==0.21.0
pytest-cov==4.1.0
pytest-mock==3.11.0
pytest-timeout==2.1.0
httpx==0.24.0
responses==0.23.0
sqlalchemy[postgresql]==2.0.0

# Mocking & Fixtures
factory-boy==3.3.0
faker==19.0.0

# Code Quality
black==23.9.0
pylint==2.17.0
mypy==1.5.0
```

### 1.3 Create pytest Configuration

**File:** `backend/pytest.ini`

```ini
[pytest]
# Test discovery
python_files = test_*.py
python_classes = Test*
python_functions = test_*

# Markers
markers =
    unit: Unit tests (no external dependencies)
    integration: Integration tests (database/blockchain)
    e2e: End-to-end tests (full workflow)
    slow: Slow tests (>1s execution)
    security: Security/authorization tests
    webhook: Webhook handler tests

# Options
asyncio_mode = auto
timeout = 30
timeout_method = thread
addopts =
    --strict-markers
    --tb=short
    --cov=backend
    --cov-report=term-missing
    --cov-report=html:htmlcov
    --cov-fail-under=80

testpaths = tests

# Ignore
norecursedirs = .git venv __pycache__
```

---

## 2. API Endpoint Tests

### 2.1 Test Fixtures & Setup

**File:** `backend/tests/conftest.py`

```python
"""
Shared pytest fixtures for backend tests.
"""

import os
import pytest
import asyncio
from typing import Generator
from unittest.mock import Mock, AsyncMock, patch

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from fastapi.testclient import TestClient

from app import app, get_db
from database.models import Base


# ─────────────────────────────────────────────────────────────────
# DATABASE FIXTURES
# ─────────────────────────────────────────────────────────────────

@pytest.fixture(scope="session")
def test_database_url():
    """Return in-memory SQLite URL for testing."""
    return "sqlite:///./test.db"


@pytest.fixture(scope="session")
def engine(test_database_url):
    """Create test database engine."""
    engine = create_engine(
        test_database_url,
        connect_args={"check_same_thread": False},
        echo=False
    )
    # Create tables
    Base.metadata.create_all(bind=engine)
    yield engine
    # Cleanup
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def db_session(engine) -> Generator[Session, None, None]:
    """Create test database session."""
    connection = engine.connect()
    transaction = connection.begin()
    session = sessionmaker(autocommit=False, autoflush=False, bind=connection)()

    yield session

    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture
def client(db_session: Session):
    """Create FastAPI test client with mocked DB."""
    def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()


# ─────────────────────────────────────────────────────────────────
# MOCKING FIXTURES
# ─────────────────────────────────────────────────────────────────

@pytest.fixture
def mock_token_agent():
    """Mock TokenAgent service."""
    mock = AsyncMock()
    mock.get_balance.return_value = 1000.0
    mock.get_total_supply.return_value = 100000.0
    mock.get_emission_stats.return_value = {
        "totalMinted": 100000.0,
        "totalBurned": 5000.0,
        "circulating": 95000.0
    }
    mock.process_mint = AsyncMock(return_value="0xabc123...")
    mock.process_burn = AsyncMock(return_value="0xdef456...")
    return mock


@pytest.fixture
def mock_aurora_service():
    """Mock AuroraIntegrationService."""
    mock = AsyncMock()
    mock.on_booking_created = AsyncMock()
    mock.on_booking_completed = AsyncMock()
    mock.on_booking_cancelled = AsyncMock()
    mock.on_review_submitted = AsyncMock()
    return mock


@pytest.fixture
def mock_tribe_service():
    """Mock TribeIntegrationService."""
    mock = AsyncMock()
    mock.on_event_attendance = AsyncMock()
    mock.on_contribution = AsyncMock()
    mock.on_staking_started = AsyncMock()
    mock.on_coaching_milestone = AsyncMock()
    mock.on_referral_success = AsyncMock()
    return mock


# ─────────────────────────────────────────────────────────────────
# TEST DATA FIXTURES
# ─────────────────────────────────────────────────────────────────

@pytest.fixture
def test_user(db_session):
    """Create test user."""
    from database.models import User

    user = User(
        user_id="test_user_123",
        email="test@example.com",
        wallet_address="0x742d35Cc6634C0532925a3b844Bc9e7595f10000",
        kyc_verified=True
    )
    db_session.add(user)
    db_session.commit()
    return user


@pytest.fixture
def test_booking(db_session, test_user):
    """Create test Aurora booking."""
    from database.models import AuroraBooking

    booking = AuroraBooking(
        booking_id="booking_123",
        user_id=test_user.user_id,
        booking_total=100.0,
        nights=2,
        reward_tokens=240.0,  # 2 × 100 × 1.2
        status="completed"
    )
    db_session.add(booking)
    db_session.commit()
    return booking


@pytest.fixture
def mock_web3(monkeypatch):
    """Mock Web3 provider."""
    mock_w3 = Mock()
    mock_w3.eth.get_transaction_count.return_value = 42
    mock_w3.eth.send_raw_transaction.return_value = b'\xab\xcd\xef...'
    mock_w3.eth.wait_for_transaction_receipt.return_value = {
        'status': 1,
        'gasUsed': 150000
    }

    monkeypatch.setenv("RPC_URL", "http://localhost:8545")
    monkeypatch.setenv("HAVEN_CONTRACT_ADDRESS", "0x0000000000000000000000000000000000000001")
    monkeypatch.setenv("BACKEND_PRIVATE_KEY", "0x1234...")

    return mock_w3


# ─────────────────────────────────────────────────────────────────
# EVENT LOOP FIXTURE (for async tests)
# ─────────────────────────────────────────────────────────────────

@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async tests."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()
```

### 2.2 API Endpoint Tests

**File:** `backend/tests/test_api_endpoints.py`

```python
"""
Tests for FastAPI endpoints.
"""

import pytest
from fastapi import HTTPException
from unittest.mock import patch, MagicMock
import json
from datetime import datetime


@pytest.mark.unit
class TestHealthEndpoint:
    """Test /health endpoint."""

    def test_health_check_success(self, client, db_session, mock_token_agent):
        """Test successful health check."""
        with patch('app.token_agent', mock_token_agent):
            response = client.get("/health")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["database"] == "connected"
        assert data["blockchain"] == "connected"

    def test_health_check_db_failure(self, client, db_session):
        """Test health check when DB unavailable."""
        # Simulate DB error
        db_session.execute = MagicMock(side_effect=Exception("DB connection failed"))

        response = client.get("/health")

        assert response.status_code == 503
        data = response.json()
        assert data["status"] == "unhealthy"


@pytest.mark.unit
class TestMintTokenEndpoint:
    """Test POST /token/mint endpoint."""

    def test_mint_success_with_idempotency(self, client, test_user, mock_token_agent):
        """Test successful token mint with idempotency."""
        payload = {
            "user_id": test_user.user_id,
            "amount": 100.0,
            "reason": "booking_reward_123",
            "idempotency_key": "mint_key_1"
        }

        with patch('app.token_agent', mock_token_agent):
            # First request
            response1 = client.post(
                "/token/mint",
                json=payload,
                headers={"X-API-Key": "test_key"}
            )

        assert response1.status_code == 200
        data1 = response1.json()
        assert data1["status"] == "queued"
        assert data1["tx_id"] == "mint_key_1"

    def test_mint_duplicate_rejected(self, client, test_user, db_session):
        """Test duplicate mint request is rejected."""
        from database.models import Transaction

        # Create existing transaction
        existing_tx = Transaction(
            tx_id="mint_key_1",
            user_id=test_user.user_id,
            tx_type="mint",
            amount=100.0,
            reason="booking_reward_123",
            status="confirmed",
            blockchain_tx="0xabc123..."
        )
        db_session.add(existing_tx)
        db_session.commit()

        payload = {
            "user_id": test_user.user_id,
            "amount": 100.0,
            "reason": "booking_reward_123",
            "idempotency_key": "mint_key_1"
        }

        response = client.post(
            "/token/mint",
            json=payload,
            headers={"X-API-Key": "test_key"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "duplicate"

    def test_mint_missing_api_key(self, client, test_user):
        """Test mint without API key is rejected."""
        payload = {
            "user_id": test_user.user_id,
            "amount": 100.0,
            "reason": "test"
        }

        response = client.post("/token/mint", json=payload)

        assert response.status_code == 403

    def test_mint_user_not_found(self, client):
        """Test mint for non-existent user."""
        payload = {
            "user_id": "nonexistent_user",
            "amount": 100.0,
            "reason": "test"
        }

        response = client.post(
            "/token/mint",
            json=payload,
            headers={"X-API-Key": "test_key"}
        )

        # Background task will fail, but endpoint returns 200 (queued)
        assert response.status_code == 200


@pytest.mark.unit
class TestRedeemTokenEndpoint:
    """Test POST /token/redeem endpoint."""

    def test_redeem_success(self, client, test_user, mock_token_agent):
        """Test successful token redemption."""
        payload = {
            "user_id": test_user.user_id,
            "amount": 500.0,
            "withdrawal_method": "bank_transfer",
            "idempotency_key": "redeem_key_1"
        }

        with patch('app.token_agent', mock_token_agent):
            response = client.post(
                "/token/redeem",
                json=payload,
                headers={"X-API-Key": "test_key"}
            )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "queued"
        assert data["burn_amount"] == 500.0
        assert data["payout_amount"] == 490.0  # 2% burn fee

    def test_redeem_insufficient_balance(self, client, test_user, mock_token_agent):
        """Test redeem with insufficient balance."""
        mock_token_agent.get_balance.return_value = 100.0  # Not enough

        payload = {
            "user_id": test_user.user_id,
            "amount": 500.0,
            "withdrawal_method": "bank_transfer",
            "idempotency_key": "redeem_key_2"
        }

        with patch('app.token_agent', mock_token_agent):
            response = client.post(
                "/token/redeem",
                json=payload,
                headers={"X-API-Key": "test_key"}
            )

        assert response.status_code == 400
        data = response.json()
        assert "Insufficient balance" in data["detail"]

    def test_redeem_duplicate_rejected(self, client, test_user, db_session, mock_token_agent):
        """Test duplicate redemption request."""
        from database.models import RedemptionRequest

        # Create existing redemption
        existing = RedemptionRequest(
            request_id="redeem_key_1",
            user_id=test_user.user_id,
            amount=500.0,
            withdrawal_method="bank_transfer",
            status="pending"
        )
        db_session.add(existing)
        db_session.commit()

        payload = {
            "user_id": test_user.user_id,
            "amount": 500.0,
            "withdrawal_method": "bank_transfer",
            "idempotency_key": "redeem_key_1"
        }

        with patch('app.token_agent', mock_token_agent):
            response = client.post(
                "/token/redeem",
                json=payload,
                headers={"X-API-Key": "test_key"}
            )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "duplicate"


@pytest.mark.unit
class TestBalanceEndpoint:
    """Test GET /token/balance/{user_id} endpoint."""

    def test_get_balance_success(self, client, test_user, mock_token_agent):
        """Test successful balance query."""
        mock_token_agent.get_balance.return_value = 1234.56

        with patch('app.token_agent', mock_token_agent):
            response = client.get(f"/token/balance/{test_user.user_id}")

        assert response.status_code == 200
        data = response.json()
        assert data["user_id"] == test_user.user_id
        assert data["balance"] == 1234.56
        assert data["wallet_address"] == test_user.wallet_address

    def test_get_balance_user_not_found(self, client):
        """Test balance query for non-existent user."""
        response = client.get("/token/balance/nonexistent")

        assert response.status_code == 404
        data = response.json()
        assert "User not found" in data["detail"]


@pytest.mark.unit
class TestAnalyticsEndpoints:
    """Test analytics endpoints."""

    def test_get_token_stats(self, client, mock_token_agent):
        """Test GET /analytics/token-stats."""
        stats_data = {
            "totalMinted": 500000.0,
            "totalBurned": 50000.0,
            "circulating": 450000.0
        }
        mock_token_agent.get_emission_stats.return_value = stats_data

        with patch('app.token_agent', mock_token_agent):
            response = client.get("/analytics/token-stats")

        assert response.status_code == 200
        data = response.json()
        assert data["total_minted"] == 500000.0
        assert data["total_burned"] == 50000.0
        assert data["circulating_supply"] == 450000.0

    def test_get_user_transactions(self, client, test_user, db_session):
        """Test GET /analytics/transactions/{user_id}."""
        from database.models import Transaction

        # Create test transactions
        for i in range(5):
            tx = Transaction(
                tx_id=f"tx_{i}",
                user_id=test_user.user_id,
                tx_type="mint" if i % 2 == 0 else "burn",
                amount=float(i * 100),
                status="confirmed"
            )
            db_session.add(tx)
        db_session.commit()

        response = client.get(f"/analytics/transactions/{test_user.user_id}")

        assert response.status_code == 200
        data = response.json()
        assert data["user_id"] == test_user.user_id
        assert data["count"] == 5
        assert len(data["transactions"]) == 5
```

---

## 3. Service Layer Tests

### 3.1 TokenAgent Service Tests

**File:** `backend/tests/test_services.py` (partial)

```python
"""
Tests for TokenAgent service.
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from datetime import datetime
from web3 import Web3

from services.token_agent import TokenAgent
from database.models import User, Transaction


@pytest.mark.integration
class TestTokenAgent:
    """Test TokenAgent blockchain interactions."""

    @pytest.fixture
    def token_agent(self, monkeypatch):
        """Create TokenAgent instance with mocked Web3."""
        # Mock Web3
        mock_w3 = Mock()
        mock_w3.eth.get_transaction_count.return_value = 42
        mock_w3.eth.account.from_key.return_value = Mock(
            address="0xMinterAddress"
        )

        # Mock contract
        mock_contract = Mock()
        mock_contract.functions.mint.return_value.build_transaction.return_value = {
            'from': '0xMinterAddress',
            'nonce': 42,
            'gas': 150000,
            'value': 0
        }

        with patch('services.token_agent.Web3', return_value=mock_w3):
            with patch.object(TokenAgent, '_load_contract_abi', return_value=[]):
                agent = TokenAgent()
                agent.w3 = mock_w3
                agent.contract = mock_contract

        return agent

    @pytest.mark.asyncio
    async def test_process_mint_success(self, token_agent, test_user, db_session):
        """Test successful token mint."""
        # Mock transaction receipt
        token_agent.w3.eth.send_raw_transaction = Mock(
            return_value=b'\xab\xcd\xef\x00'
        )
        token_agent.w3.eth.wait_for_transaction_receipt = Mock(
            return_value={'status': 1, 'gasUsed': 150000}
        )
        token_agent.w3.eth.account.sign_transaction = Mock(
            return_value=Mock(rawTransaction=b'signed_tx')
        )

        # Execute mint
        tx_hash = await token_agent.process_mint(
            tx_id="test_mint_1",
            user_id=test_user.user_id,
            amount=100.0,
            reason="test_mint",
            db=db_session
        )

        # Assertions
        assert tx_hash is not None

        # Verify transaction was recorded
        tx_record = db_session.query(Transaction).filter(
            Transaction.tx_id == "test_mint_1"
        ).first()
        assert tx_record is not None
        assert tx_record.status == "confirmed"
        assert tx_record.amount == 100.0

    @pytest.mark.asyncio
    async def test_process_mint_user_not_found(self, token_agent, db_session):
        """Test mint fails when user not found."""
        with pytest.raises(ValueError, match="User .* not found"):
            await token_agent.process_mint(
                tx_id="test_mint_2",
                user_id="nonexistent",
                amount=100.0,
                reason="test",
                db=db_session
            )

    @pytest.mark.asyncio
    async def test_process_mint_duplicate(self, token_agent, test_user, db_session):
        """Test mint handles duplicate idempotency."""
        # Create existing transaction
        existing_tx = Transaction(
            tx_id="test_mint_1",
            user_id=test_user.user_id,
            tx_type="mint",
            amount=100.0,
            status="confirmed",
            blockchain_tx="0xexisting..."
        )
        db_session.add(existing_tx)
        db_session.commit()

        # Attempt to mint with same ID
        result = await token_agent.process_mint(
            tx_id="test_mint_1",
            user_id=test_user.user_id,
            amount=100.0,
            reason="duplicate",
            db=db_session
        )

        # Should return existing tx_hash
        assert result == "0xexisting..."

    def test_get_balance(self, token_agent):
        """Test get_balance call."""
        # Mock contract response
        token_agent.contract.functions.balanceOf.return_value.call.return_value = (
            Web3.to_wei(1234.56, 'ether')
        )

        balance = token_agent.get_balance("0xUserWallet")

        assert balance == 1234.56

    def test_get_balance_error_handling(self, token_agent):
        """Test get_balance handles errors gracefully."""
        token_agent.contract.functions.balanceOf.return_value.call.side_effect = (
            Exception("RPC error")
        )

        balance = token_agent.get_balance("0xUserWallet")

        assert balance == 0.0
```

---

## 4. Integration Test Examples

### 4.1 Aurora Webhook Integration

**File:** `backend/tests/test_integration.py` (partial)

```python
"""
Integration tests for end-to-end flows.
"""

import pytest
import json
import hmac
import hashlib
from unittest.mock import patch, AsyncMock
from datetime import datetime

from app import app
from database.models import User, AuroraBooking, Transaction


def create_aurora_signature(payload: dict, secret: str) -> str:
    """Create HMAC-SHA256 signature for webhook."""
    message = json.dumps(payload, sort_keys=True)
    signature = hmac.new(
        secret.encode(),
        message.encode(),
        hashlib.sha256
    ).hexdigest()
    return signature


@pytest.mark.integration
class TestAuroraWebhookIntegration:
    """Test Aurora PMS webhook integration."""

    @pytest.mark.asyncio
    async def test_booking_created_workflow(
        self,
        client,
        db_session,
        mock_token_agent,
        monkeypatch
    ):
        """Test complete booking creation workflow."""
        # Setup
        monkeypatch.setenv("AURORA_WEBHOOK_SECRET", "test_secret")

        booking_payload = {
            "id": "booking_456",
            "guest_id": "new_guest_789",
            "guest_email": "guest@example.com",
            "total_price": 150.0,
            "nights": 2
        }

        signature = create_aurora_signature(booking_payload, "test_secret")

        with patch('app.aurora_service.on_booking_created', new_callable=AsyncMock) as mock_handler:
            with patch('app.token_agent', mock_token_agent):
                response = client.post(
                    "/webhooks/aurora/booking-created",
                    json=booking_payload,
                    headers={"X-Aurora-Signature": signature}
                )

        # Verify webhook accepted
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "accepted"

        # Verify handler was called
        mock_handler.assert_called_once()

    @pytest.mark.asyncio
    async def test_booking_cancelled_reverses_tokens(
        self,
        client,
        db_session,
        test_user,
        test_booking,
        mock_token_agent,
        monkeypatch
    ):
        """Test booking cancellation reverses (burns) tokens."""
        monkeypatch.setenv("AURORA_WEBHOOK_SECRET", "test_secret")

        # Verify booking exists
        booking = db_session.query(AuroraBooking).filter(
            AuroraBooking.booking_id == test_booking.booking_id
        ).first()
        assert booking.status == "completed"
        assert booking.reward_tokens == 240.0

        # Send cancellation webhook
        cancel_payload = {
            "id": test_booking.booking_id,
            "guest_id": test_user.user_id,
            "cancellation_reason": "guest_requested"
        }

        signature = create_aurora_signature(cancel_payload, "test_secret")

        with patch('app.aurora_service.on_booking_cancelled', new_callable=AsyncMock) as mock_handler:
            response = client.post(
                "/webhooks/aurora/booking-cancelled",
                json=cancel_payload,
                headers={"X-Aurora-Signature": signature}
            )

        assert response.status_code == 200
        mock_handler.assert_called_once()

    def test_invalid_webhook_signature_rejected(self, client, monkeypatch):
        """Test invalid webhook signature is rejected."""
        monkeypatch.setenv("AURORA_WEBHOOK_SECRET", "real_secret")

        payload = {"id": "booking_123", "guest_id": "guest_456"}
        bad_signature = "invalid_signature_xyz"

        response = client.post(
            "/webhooks/aurora/booking-created",
            json=payload,
            headers={"X-Aurora-Signature": bad_signature}
        )

        assert response.status_code == 401
        data = response.json()
        assert "Invalid signature" in data["detail"]


@pytest.mark.integration
class TestE2EUserJourney:
    """Test complete user journey from signup to redemption."""

    @pytest.mark.asyncio
    async def test_guest_lifecycle(self, client, db_session, mock_token_agent, monkeypatch):
        """Test complete guest lifecycle (booking → event → redemption)."""
        monkeypatch.setenv("AURORA_WEBHOOK_SECRET", "test_secret")

        # Step 1: Guest books stay (via webhook)
        booking_payload = {
            "id": "booking_journey_1",
            "guest_id": "journey_guest_1",
            "guest_email": "journey@example.com",
            "total_price": 100.0,
            "nights": 2
        }

        signature = create_aurora_signature(booking_payload, "test_secret")

        with patch('app.aurora_service.on_booking_created', new_callable=AsyncMock):
            response = client.post(
                "/webhooks/aurora/booking-created",
                json=booking_payload,
                headers={"X-Aurora-Signature": signature}
            )

        assert response.status_code == 200

        # Step 2: Guest attends event (via webhook)
        event_payload = {
            "id": "event_123",
            "attendee_id": "journey_guest_1",
            "name": "Wisdom Circle",
            "type": "wisdom_circle"
        }

        with patch('app.tribe_service.on_event_attendance', new_callable=AsyncMock):
            response = client.post(
                "/webhooks/tribe/event-attendance",
                json=event_payload
            )

        assert response.status_code == 200

        # Step 3: Guest requests balance
        mock_token_agent.get_balance.return_value = 340.0  # 240 (booking) + 100 (event)

        with patch('app.token_agent', mock_token_agent):
            response = client.get(
                "/token/balance/journey_guest_1"
            )

        assert response.status_code == 200
        data = response.json()
        assert data["balance"] == 340.0

        # Step 4: Guest requests redemption
        redeem_payload = {
            "user_id": "journey_guest_1",
            "amount": 200.0,
            "withdrawal_method": "bank_transfer",
            "idempotency_key": "redeem_journey_1"
        }

        mock_token_agent.get_balance.return_value = 340.0  # Still have 340

        with patch('app.token_agent', mock_token_agent):
            response = client.post(
                "/token/redeem",
                json=redeem_payload,
                headers={"X-API-Key": "test_key"}
            )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "queued"
        assert data["burn_amount"] == 200.0
        assert data["payout_amount"] == 196.0  # 2% burn fee
```

---

## 5. Webhook Testing

### 5.1 Signature Verification Tests

**File:** `backend/tests/test_webhooks.py`

```python
"""
Tests for webhook signature verification and handling.
"""

import pytest
import hmac
import hashlib
import json
from unittest.mock import patch, AsyncMock


def test_aurora_webhook_signature_validation():
    """Test Aurora webhook signature validation."""
    secret = "aurora_secret_key"
    payload = {
        "id": "booking_123",
        "guest_id": "guest_456",
        "total_price": 100.0
    }

    # Create valid signature
    message = json.dumps(payload, sort_keys=True)
    valid_signature = hmac.new(
        secret.encode(),
        message.encode(),
        hashlib.sha256
    ).hexdigest()

    # Test valid signature
    from app import verify_webhook_signature
    assert verify_webhook_signature(valid_signature, payload, secret) is True

    # Test invalid signature
    invalid_signature = "invalid_xyz_abc_123"
    assert verify_webhook_signature(invalid_signature, payload, secret) is False

    # Test tampered payload
    tampered_payload = {
        "id": "booking_123",
        "guest_id": "guest_456",
        "total_price": 200.0  # Changed!
    }
    assert verify_webhook_signature(valid_signature, tampered_payload, secret) is False


@pytest.mark.asyncio
async def test_webhook_concurrent_delivery():
    """Test handling of concurrent webhook deliveries."""
    # Simulate two bookings for same guest arriving simultaneously
    from concurrent.futures import ThreadPoolExecutor

    booking_1 = {"id": "booking_1", "guest_id": "guest_same"}
    booking_2 = {"id": "booking_2", "guest_id": "guest_same"}

    # Both should be processed independently
    # No data corruption or race conditions

    # This would be tested with actual concurrent HTTP requests
    # to the webhook endpoint


@pytest.mark.asyncio
async def test_webhook_retry_logic():
    """Test webhook handler retry logic on failure."""
    # Mock a failing handler
    attempt_count = 0

    async def failing_handler():
        nonlocal attempt_count
        attempt_count += 1
        if attempt_count < 3:
            raise Exception("Temporary failure")
        return "success"

    # Simulate exponential backoff retry
    # 1st attempt: immediate, fails
    # 2nd attempt: 1 second delay, fails
    # 3rd attempt: 5 second delay, succeeds

    # Assert all retries executed
    # Assert final state is success
```

---

## 6. Load Test Configuration

### 6.1 JMeter Load Test Plan

**File:** `load-tests/jmeter_api_load_test.jmx` (XML format)

```xml
<?xml version="1.0" encoding="UTF-8"?>
<jmeterTestPlan version="1.2">
  <hashTree>
    <TestPlan guiclass="TestPlanGui" testname="HAVEN API Load Test">
      <elementProp name="TestPlan.user_defined_variables"/>
      <boolProp name="TestPlan.functional_mode">false</boolProp>
      <boolProp name="TestPlan.serialize_threadgroups">false</boolProp>
      <elementProp name="TestPlan.user_defined_variables" elementType="Arguments"/>
    </TestPlan>

    <hashTree>
      <!-- Thread Group: Simulate Users -->
      <ThreadGroup guiclass="ThreadGroupGui" testname="API Users">
        <stringProp name="ThreadGroup.num_threads">100</stringProp>
        <stringProp name="ThreadGroup.ramp_time">300</stringProp>
        <elementProp name="ThreadGroup.main_controller" elementType="LoopController">
          <boolProp name="LoopController.continue_forever">true</boolProp>
          <stringProp name="LoopController.loops">10</stringProp>
        </elementProp>
        <boolProp name="ThreadGroup.scheduler">true</boolProp>
        <stringProp name="ThreadGroup.duration">300</stringProp>
      </ThreadGroup>

      <hashTree>
        <!-- HTTP Config -->
        <ConfigTestElement guiclass="HttpConfigGui" testname="HTTP Request Defaults">
          <elementProp name="HTTPsampler.Arguments" elementType="Arguments"/>
          <stringProp name="HTTPSampler.domain">localhost</stringProp>
          <stringProp name="HTTPSampler.port">8000</stringProp>
          <stringProp name="HTTPSampler.protocol">http</stringProp>
          <stringProp name="HTTPSampler.path">/</stringProp>
        </ConfigTestElement>

        <!-- Health Check -->
        <HTTPSamplerProxy guiclass="HttpTestSampleGui" testname="GET /health">
          <stringProp name="HTTPSampler.path">/health</stringProp>
          <stringProp name="HTTPSampler.method">GET</stringProp>
        </HTTPSamplerProxy>

        <!-- Balance Query -->
        <HTTPSamplerProxy guiclass="HttpTestSampleGui" testname="GET /token/balance">
          <stringProp name="HTTPSampler.path">/token/balance/user_${__threadNum}</stringProp>
          <stringProp name="HTTPSampler.method">GET</stringProp>
        </HTTPSamplerProxy>

        <!-- Assertions -->
        <ResponseAssertion guiclass="AssertionGui" testname="Response Assertion">
          <elementProp name="TestElements" elementType="HTTPSampler">
            <boolProp name="Assertion.test_type">6</boolProp>
            <stringProp name="Assertion.test_field">Assertion.response_data</stringProp>
            <stringProp name="Assertion.assume_success">false</stringProp>
            <intProp name="Assertion.test_type">1</intProp>
            <stringProp name="Assertion.test_string">200</stringProp>
          </elementProp>
        </ResponseAssertion>

        <!-- Results Listener -->
        <ResultCollector guiclass="TableVisualizer" testname="View Results Table">
          <boolProp name="ResultCollector.error_logging">true</boolProp>
          <objProp>
            <name>filename</name>
            <value>/tmp/jmeter_results.csv</value>
          </objProp>
        </ResultCollector>
      </hashTree>
    </hashTree>
  </hashTree>
</jmeterTestPlan>
```

### 6.2 Locust Load Test Script

**File:** `load-tests/locustfile.py`

```python
"""
Locust load test for HAVEN Token API.
"""

from locust import HttpUser, TaskSet, task, between
import json
import random


class APITaskSet(TaskSet):
    """Define tasks for load test."""

    @task(40)
    def health_check(self):
        """Health check endpoint (40% of traffic)."""
        self.client.get("/health")

    @task(30)
    def get_balance(self):
        """Get user balance (30% of traffic)."""
        user_id = f"user_{random.randint(1, 1000)}"
        self.client.get(f"/token/balance/{user_id}")

    @task(20)
    def mint_token(self):
        """Mint tokens (20% of traffic)."""
        payload = {
            "user_id": f"user_{random.randint(1, 1000)}",
            "amount": random.uniform(10, 1000),
            "reason": "load_test",
            "idempotency_key": f"mint_{random.randint(1, 100000)}"
        }
        headers = {"X-API-Key": "test_key"}
        self.client.post(
            "/token/mint",
            json=payload,
            headers=headers,
            name="/token/mint"
        )

    @task(10)
    def get_stats(self):
        """Get token stats (10% of traffic)."""
        self.client.get("/analytics/token-stats")


class APIUser(HttpUser):
    """User class for load testing."""
    tasks = [APITaskSet]
    wait_time = between(1, 3)


# Run with:
# locust -f load-tests/locustfile.py --headless -u 1000 -r 50 -t 5m
```

---

## 7. CI/CD Integration

### 7.1 GitHub Actions Workflow

**File:** `.github/workflows/backend-ci.yml`

```yaml
name: Backend CI/CD

on:
  push:
    branches: [ main, develop ]
    paths: [ 'backend/**', '.github/workflows/backend-ci.yml' ]
  pull_request:
    branches: [ main, develop ]
    paths: [ 'backend/**' ]

jobs:
  test:
    runs-on: ubuntu-latest

    services:
      postgres:
        image: postgres:15
        env:
          POSTGRES_PASSWORD: postgres
          POSTGRES_DB: haven_test
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
        ports:
          - 5432:5432

    steps:
      - uses: actions/checkout@v3

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: 3.11
          cache: 'pip'

      - name: Install dependencies
        run: |
          cd backend
          pip install -r requirements.txt
          pip install -r requirements-dev.txt

      - name: Lint with pylint
        run: |
          cd backend
          pylint app.py services/ database/ tests/

      - name: Format check with black
        run: |
          cd backend
          black --check app.py services/ database/ tests/

      - name: Type check with mypy
        run: |
          cd backend
          mypy app.py services/ database/

      - name: Run unit tests
        env:
          DATABASE_URL: postgresql://postgres:postgres@localhost:5432/haven_test
          RPC_URL: http://localhost:8545
          HAVEN_CONTRACT_ADDRESS: 0x1234567890123456789012345678901234567890
          BACKEND_PRIVATE_KEY: 0x1234567890123456789012345678901234567890123456789012345678901234
          API_KEY: test_key
        run: |
          cd backend
          pytest tests/ -m "unit" -v --cov=. --cov-report=xml

      - name: Upload coverage
        uses: codecov/codecov-action@v3
        with:
          files: ./backend/coverage.xml
          fail_ci_if_error: true

      - name: Run integration tests
        env:
          DATABASE_URL: postgresql://postgres:postgres@localhost:5432/haven_test
        run: |
          cd backend
          pytest tests/ -m "integration" -v --timeout=30

      - name: Publish test results
        if: always()
        uses: EnricoMi/publish-unit-test-result-action@v2
        with:
          files: backend/test-results.xml

  security:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Run Bandit security scan
        run: |
          cd backend
          pip install bandit
          bandit -r . -f json -o bandit-report.json || true

      - name: Upload security report
        uses: actions/upload-artifact@v3
        with:
          name: security-report
          path: backend/bandit-report.json
```

---

## Quick Start Guide

### Setup Local Testing Environment

```bash
# 1. Install dependencies
cd backend
pip install -r requirements-dev.txt

# 2. Create test database
createdb haven_test

# 3. Run tests
pytest tests/ -v --cov

# 4. Run specific test
pytest tests/test_api_endpoints.py::TestMintTokenEndpoint -v

# 5. Run with coverage report
pytest tests/ --cov=backend --cov-report=html
# Open htmlcov/index.html in browser

# 6. Run load tests
locust -f ../load-tests/locustfile.py --headless -u 500 -r 50
```

---

**End of Test Implementation Guide**
