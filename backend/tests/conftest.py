"""
pytest Configuration and Fixtures
Provides shared test fixtures for all test modules
"""
import pytest
import os
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

# Set test environment
os.environ["ENVIRONMENT"] = "test"
os.environ["API_KEY"] = "test_api_key_12345"

# Import after setting environment
from app import app
from database.models import Base

# Test database URL (in-memory SQLite for speed)
SQLALCHEMY_TEST_DATABASE_URL = "sqlite:///:memory:"

@pytest.fixture(scope="function")
def db_engine():
    """
    Create a fresh database engine for each test

    Uses in-memory SQLite for fast, isolated tests
    """
    engine = create_engine(
        SQLALCHEMY_TEST_DATABASE_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    yield engine
    Base.metadata.drop_all(bind=engine)
    engine.dispose()


@pytest.fixture(scope="function")
def db_session(db_engine):
    """
    Create a database session for a test

    Automatically rolls back after test to ensure isolation
    """
    TestingSessionLocal = sessionmaker(
        autocommit=False,
        autoflush=False,
        bind=db_engine
    )

    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.rollback()
        session.close()


@pytest.fixture(scope="function")
def client(db_session):
    """
    Create FastAPI test client with database session override
    """
    from app import get_db

    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()


@pytest.fixture
def auth_headers():
    """
    Headers with valid API key for authenticated requests
    """
    return {"X-API-Key": "test_api_key_12345"}


@pytest.fixture
def mock_web3():
    """
    Mock Web3 provider for blockchain interactions

    Returns a MagicMock configured to simulate Web3 behavior
    """
    from unittest.mock import MagicMock, AsyncMock
    from web3 import Web3

    mock = MagicMock()
    mock.eth = MagicMock()
    mock.eth.get_balance = MagicMock(return_value=Web3.to_wei(1, 'ether'))
    mock.eth.get_transaction_count = MagicMock(return_value=0)
    mock.eth.gas_price = Web3.to_wei(1, 'gwei')
    mock.eth.chain_id = 84532  # Base Sepolia

    # Mock contract
    mock_contract = MagicMock()
    mock_contract.functions = MagicMock()

    # Mock mint function
    mock_mint = MagicMock()
    mock_mint.build_transaction = MagicMock(return_value={
        "to": "0x" + "0" * 40,
        "data": "0x",
        "gas": 100000,
        "gasPrice": Web3.to_wei(1, 'gwei'),
        "nonce": 0,
        "chainId": 84532
    })
    mock_contract.functions.mint = MagicMock(return_value=mock_mint)

    # Mock balanceOf
    mock_balance = MagicMock()
    mock_balance.call = MagicMock(return_value=Web3.to_wei(100, 'ether'))
    mock_contract.functions.balanceOf = MagicMock(return_value=mock_balance)

    mock.eth.contract = MagicMock(return_value=mock_contract)

    return mock


@pytest.fixture
def sample_user(db_session):
    """
    Create a sample user for testing
    """
    from database.models import User

    user = User(
        user_id="test_user_001",
        email="test@example.com",
        wallet_address="0x" + "1" * 40,
        kyc_verified=False
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)

    return user


@pytest.fixture
def sample_transaction(db_session, sample_user):
    """
    Create a sample transaction for testing
    """
    from database.models import Transaction

    tx = Transaction(
        tx_id="mint_test_user_001_123456",
        user_id=sample_user.user_id,
        tx_type="mint",
        amount=100.0,
        reason="test_mint",
        status="completed",
        blockchain_tx="0x" + "a" * 64,
        gas_used=50000
    )
    db_session.add(tx)
    db_session.commit()
    db_session.refresh(tx)

    return tx


@pytest.fixture
def aurora_webhook_payload():
    """
    Sample Aurora PMS webhook payload
    """
    return {
        "id": "booking_12345",
        "guest_id": "guest_001",
        "guest_email": "guest@example.com",
        "total_price": 200.0,
        "nights": 2,
        "status": "confirmed",
        "created_at": "2025-11-08T10:00:00Z"
    }


@pytest.fixture
def tribe_webhook_payload():
    """
    Sample Tribe App webhook payload
    """
    return {
        "event_id": "event_12345",
        "user_id": "tribe_user_001",
        "event_type": "wisdom_circle",
        "attended": True,
        "timestamp": "2025-11-08T19:00:00Z"
    }


@pytest.fixture
def mock_aurora_signature(aurora_webhook_payload):
    """
    Generate valid HMAC signature for Aurora webhook
    """
    import hmac
    import hashlib
    import json
    import time

    secret = os.getenv("AURORA_WEBHOOK_SECRET", "test_aurora_secret")
    payload_bytes = json.dumps(aurora_webhook_payload).encode('utf-8')
    signature = hmac.new(secret.encode(), payload_bytes, hashlib.sha256).hexdigest()

    return {
        "X-Aurora-Signature": signature,
        "X-Aurora-Timestamp": str(int(time.time()))
    }


@pytest.fixture
def mock_tribe_signature(tribe_webhook_payload):
    """
    Generate valid HMAC signature for Tribe webhook
    """
    import hmac
    import hashlib
    import json
    import time

    secret = os.getenv("TRIBE_WEBHOOK_SECRET", "test_tribe_secret")
    payload_bytes = json.dumps(tribe_webhook_payload).encode('utf-8')
    signature = hmac.new(secret.encode(), payload_bytes, hashlib.sha256).hexdigest()

    return {
        "X-Tribe-Signature": signature,
        "X-Tribe-Timestamp": str(int(time.time()))
    }


# Async test helpers
pytest_plugins = ('pytest_asyncio',)


@pytest.fixture
def anyio_backend():
    """Use asyncio as the async backend"""
    return 'asyncio'
