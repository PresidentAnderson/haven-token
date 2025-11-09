# HAVEN Token: Security Fixes Implementation Guide

**Status:** Implementation Guide
**Priority:** CRITICAL - Must Complete Before Mainnet

This document provides step-by-step implementation instructions for all 6 critical security fixes identified by the security audit.

---

## ✅ Fix #1: Webhook Signature Verification (COMPLETED)

**Status:** ✅ DONE

**Files Created:**
- `backend/middleware/webhook_auth.py` - HMAC-SHA256 verification
- `backend/middleware/__init__.py` - Package init

**Features:**
- HMAC-SHA256 signature verification
- Timestamp validation (5-min expiry)
- Replay attack prevention
- Constant-time comparison

**Next Step:** Apply to all webhook endpoints in app.py (see instructions below)

---

## 🔧 Fix #2: Rate Limiting

**Status:** 🟡 IN PROGRESS

### Implementation Steps:

#### Step 1: Install Dependencies ✅
Already added to `requirements.txt`:
- `slowapi==0.1.9`
- `redis==5.0.1` (already present)

#### Step 2: Create Rate Limiting Configuration

Create `backend/middleware/rate_limit.py`:

```python
"""
Rate Limiting Middleware
Uses SlowAPI with Redis backend for distributed rate limiting
"""
from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from fastapi import Request, Response
from fastapi.responses import JSONResponse
import os
import logging

logger = logging.getLogger(__name__)

# Initialize rate limiter
limiter = Limiter(
    key_func=get_remote_address,
    storage_uri=os.getenv("REDIS_URL", "redis://localhost:6379"),
    strategy="fixed-window",  # Can also use "moving-window"
    default_limits=["1000/hour"]  # Default global limit
)

# Custom rate limit exceeded handler
async def rate_limit_exceeded_handler(request: Request, exc: RateLimitExceeded) -> Response:
    """
    Custom handler for rate limit errors
    """
    logger.warning(
        f"Rate limit exceeded for {request.client.host} on {request.url.path}"
    )

    return JSONResponse(
        status_code=429,
        content={
            "error": "rate_limit_exceeded",
            "message": "Too many requests. Please try again later.",
            "retry_after": exc.detail
        },
        headers={"Retry-After": str(exc.detail)}
    )
```

#### Step 3: Update app.py

Add rate limiting to FastAPI app:

```python
# At top of app.py, add imports:
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from middleware.rate_limit import limiter, rate_limit_exceeded_handler

# After creating app instance, add:
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, rate_limit_exceeded_handler)

# Then apply rate limits to endpoints:

# Token Operations (strict limits)
@app.post("/token/mint")
@limiter.limit("10/minute")  # Max 10 mints per minute
async def mint_tokens(...):
    ...

@app.post("/token/redeem")
@limiter.limit("5/minute")  # Max 5 redemptions per minute
async def redeem_tokens(...):
    ...

# Balance Queries (generous limits)
@app.get("/token/balance/{user_id}")
@limiter.limit("100/minute")  # Max 100 balance checks per minute
async def get_balance(...):
    ...

# Webhooks (moderate limits to handle bursts)
@app.post("/webhooks/aurora/booking-created")
@limiter.limit("100/minute")
async def aurora_booking_created(...):
    ...

# Analytics (moderate limits)
@app.get("/analytics/user/{user_id}")
@limiter.limit("60/minute")
async def get_user_analytics(...):
    ...
```

#### Step 4: Start Redis

```bash
# Option 1: Docker (recommended)
docker run --name haven-redis -p 6379:6379 -d redis:7

# Option 2: Local install
# macOS
brew install redis
brew services start redis

# Linux
sudo apt-get install redis-server
sudo systemctl start redis
```

#### Step 5: Test Rate Limiting

```python
# Test script: test_rate_limit.py
import requests
import time

url = "http://localhost:8000/token/balance/test_user"

print("Testing rate limit (100 req/min)...")
for i in range(105):
    response = requests.get(url)
    if response.status_code == 429:
        print(f"✅ Rate limit triggered at request {i+1}")
        print(f"Response: {response.json()}")
        break
    print(f"Request {i+1}: {response.status_code}")
    time.sleep(0.1)
```

---

## 🔧 Fix #3: API Key Hardening

**Status:** 🟡 READY TO IMPLEMENT

### Current Issue:
```python
# backend/app.py line 125
def verify_api_key(x_api_key: str = Header(...)):
    expected_key = os.getenv("API_KEY", "test_key")  # ⚠️ BAD: Default fallback!
    if x_api_key != expected_key:
        raise HTTPException(status_code=401, detail="Invalid API key")
```

### Fix:

```python
# backend/app.py
def verify_api_key(x_api_key: str = Header(...)):
    """
    Verify API key from header

    Raises:
        HTTPException: If API key is invalid or not configured
    """
    expected_key = os.getenv("API_KEY")

    # Fail fast if API_KEY not configured
    if not expected_key:
        logger.error("API_KEY environment variable not set")
        raise HTTPException(
            status_code=500,
            detail="API authentication not configured. Contact administrator."
        )

    # Constant-time comparison to prevent timing attacks
    import hmac
    if not hmac.compare_digest(x_api_key, expected_key):
        logger.warning(f"Invalid API key attempt from {request.client.host if hasattr(request, 'client') else 'unknown'}")
        raise HTTPException(
            status_code=401,
            detail="Invalid API key"
        )

    return True
```

### Additional: Add Startup Validation

```python
# backend/app.py - add to startup event
@app.on_event("startup")
async def startup_validation():
    """
    Validate required environment variables on startup
    """
    required_vars = [
        "API_KEY",
        "DATABASE_URL",
        "RPC_URL",
        "HAVEN_CONTRACT_ADDRESS",
        "BACKEND_PRIVATE_KEY"
    ]

    missing = [var for var in required_vars if not os.getenv(var)]

    if missing:
        logger.error(f"Missing required environment variables: {', '.join(missing)}")
        raise RuntimeError(
            f"Missing required environment variables: {', '.join(missing)}. "
            f"Check .env file and environment configuration."
        )

    logger.info("✅ All required environment variables configured")
```

---

## 🔧 Fix #4: Wallet Creation Security

**Status:** 🟡 READY TO IMPLEMENT

### Current Issue:
```python
# backend/services/aurora_integration.py
async def _ensure_user_wallet(aurora_user_id, email, db):
    # Generates wallet but DOESN'T STORE private key!
    account = Account.create()
    # Private key is lost! ⚠️
```

### Solution: Encrypted Wallet Storage

#### Step 1: Create Encrypted Wallets Table

```python
# backend/database/models.py - add new model

from sqlalchemy import Column, String, LargeBinary, DateTime, ForeignKey
from cryptography.fernet import Fernet

class EncryptedWallet(Base):
    __tablename__ = "encrypted_wallets"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, ForeignKey("users.user_id"), unique=True, nullable=False, index=True)
    wallet_address = Column(String, unique=True, nullable=False, index=True)
    encrypted_private_key = Column(LargeBinary, nullable=False)  # Fernet encrypted
    created_at = Column(DateTime, server_default=func.now())

    # Relationship
    user = relationship("User", back_populates="wallet")

# Update User model to add relationship:
# In User class, add:
wallet = relationship("EncryptedWallet", back_populates="user", uselist=False)
```

#### Step 2: Create Wallet Encryption Service

```python
# backend/services/wallet_encryption.py

import os
from cryptography.fernet import Fernet
from eth_account import Account
import logging

logger = logging.getLogger(__name__)

class WalletEncryptionService:
    """
    Handles encryption/decryption of wallet private keys

    Uses Fernet symmetric encryption with key from environment.
    TODO: Migrate to AWS KMS or HashiCorp Vault for production
    """

    def __init__(self):
        # Get encryption key from environment
        key = os.getenv("WALLET_ENCRYPTION_KEY")

        if not key:
            logger.warning("WALLET_ENCRYPTION_KEY not set, generating temporary key")
            logger.warning("⚠️  THIS IS INSECURE FOR PRODUCTION! Set WALLET_ENCRYPTION_KEY in .env")
            # Generate and print key for .env (development only)
            key = Fernet.generate_key().decode()
            logger.warning(f"Add to .env: WALLET_ENCRYPTION_KEY={key}")

        self.fernet = Fernet(key.encode() if isinstance(key, str) else key)

    def create_encrypted_wallet(self) -> tuple[str, bytes]:
        """
        Generate new wallet and encrypt private key

        Returns:
            tuple: (wallet_address, encrypted_private_key_bytes)
        """
        # Generate new account
        account = Account.create()

        # Encrypt private key
        private_key_hex = account.key.hex()
        encrypted_key = self.fernet.encrypt(private_key_hex.encode())

        logger.info(f"Created encrypted wallet: {account.address}")

        return account.address, encrypted_key

    def decrypt_private_key(self, encrypted_key: bytes) -> str:
        """
        Decrypt private key

        Args:
            encrypted_key: Encrypted private key bytes

        Returns:
            str: Private key hex string (with 0x prefix)
        """
        decrypted = self.fernet.decrypt(encrypted_key)
        return decrypted.decode()

    def get_account(self, encrypted_key: bytes):
        """
        Get Web3 Account instance from encrypted key

        Args:
            encrypted_key: Encrypted private key bytes

        Returns:
            Account: eth_account Account instance
        """
        private_key = self.decrypt_private_key(encrypted_key)
        return Account.from_key(private_key)


# Singleton instance
wallet_service = WalletEncryptionService()
```

#### Step 3: Update Aurora Integration

```python
# backend/services/aurora_integration.py

from services.wallet_encryption import wallet_service
from database.models import EncryptedWallet

async def _ensure_user_wallet(aurora_user_id: str, email: str, db):
    """
    Ensure user has a wallet, create if needed

    SECURITY: Wallets are encrypted and stored in database
    """
    # Check if user exists
    user = db.query(User).filter(User.user_id == aurora_user_id).first()

    if not user:
        # Create user and wallet
        user = User(
            user_id=aurora_user_id,
            email=email,
            kyc_verified=False
        )
        db.add(user)
        db.flush()  # Get user ID

        # Create encrypted wallet
        wallet_address, encrypted_key = wallet_service.create_encrypted_wallet()

        encrypted_wallet = EncryptedWallet(
            user_id=user.user_id,
            wallet_address=wallet_address,
            encrypted_private_key=encrypted_key
        )

        # Update user with wallet address
        user.wallet_address = wallet_address

        db.add(encrypted_wallet)
        db.commit()

        logger.info(f"Created user {aurora_user_id} with wallet {wallet_address}")

    elif not user.wallet_address:
        # User exists but no wallet - create one
        wallet_address, encrypted_key = wallet_service.create_encrypted_wallet()

        encrypted_wallet = EncryptedWallet(
            user_id=user.user_id,
            wallet_address=wallet_address,
            encrypted_private_key=encrypted_key
        )

        user.wallet_address = wallet_address

        db.add(encrypted_wallet)
        db.commit()

        logger.info(f"Added wallet {wallet_address} to existing user {aurora_user_id}")

    return user.wallet_address
```

#### Step 4: Generate Encryption Key

```bash
# Generate encryption key for .env
python3 -c "from cryptography.fernet import Fernet; print(f'WALLET_ENCRYPTION_KEY={Fernet.generate_key().decode()}')"

# Add output to backend/.env
```

#### Step 5: Run Migration

```bash
cd backend
alembic revision --autogenerate -m "Add encrypted_wallets table"
alembic upgrade head
```

---

## 🔧 Fix #5: Input Validation

**Status:** 🟡 READY TO IMPLEMENT

### Current Issue:
No min/max validation on token amounts - could mint/redeem absurd values.

### Fix: Add Pydantic Field Constraints

```python
# backend/app.py - update request models

from pydantic import BaseModel, Field, EmailStr

class MintRequest(BaseModel):
    """Request to mint tokens"""
    user_id: str = Field(..., min_length=1, max_length=100, description="User identifier")
    amount: float = Field(..., gt=0, le=10000, description="Amount to mint (0-10,000 HNV)")
    reason: str = Field(..., min_length=1, max_length=200, description="Reason for minting")

    class Config:
        json_schema_extra = {
            "example": {
                "user_id": "user_12345",
                "amount": 100.0,
                "reason": "booking_reward"
            }
        }


class RedeemRequest(BaseModel):
    """Request to redeem tokens"""
    user_id: str = Field(..., min_length=1, max_length=100)
    amount: float = Field(..., gt=0, le=100000, description="Amount to redeem (0-100,000 HNV)")
    withdrawal_method: str = Field(..., pattern="^(bank_transfer|paypal|stripe)$")
    withdrawal_address: str = Field(..., min_length=5, max_length=500)
    idempotency_key: str = Field(..., min_length=1, max_length=100)

    class Config:
        json_schema_extra = {
            "example": {
                "user_id": "user_12345",
                "amount": 500.0,
                "withdrawal_method": "bank_transfer",
                "withdrawal_address": "Account: 1234567890",
                "idempotency_key": "unique_redemption_key_123"
            }
        }


class BatchMintRequest(BaseModel):
    """Request to batch mint tokens"""
    recipients: list[str] = Field(..., min_items=1, max_items=100, description="List of user IDs")
    amounts: list[float] = Field(..., min_items=1, max_items=100, description="Amounts for each recipient")
    reason: str = Field(..., min_length=1, max_length=200)

    @validator('amounts')
    def validate_amounts(cls, v):
        """Ensure all amounts are positive and reasonable"""
        for amount in v:
            if amount <= 0 or amount > 10000:
                raise ValueError(f"Amount {amount} must be between 0 and 10,000 HNV")
        return v

    @validator('recipients', 'amounts')
    def validate_list_lengths(cls, v, values, field):
        """Ensure recipients and amounts have same length"""
        if field.name == 'amounts' and 'recipients' in values:
            if len(v) != len(values['recipients']):
                raise ValueError("recipients and amounts must have same length")
        return v
```

### Additional Validation: Wallet Addresses

```python
from eth_utils import is_address

class TransferRequest(BaseModel):
    """Request to transfer tokens"""
    from_user: str = Field(..., min_length=1, max_length=100)
    to_address: str = Field(..., description="Ethereum address (0x...)")
    amount: float = Field(..., gt=0, le=100000)

    @validator('to_address')
    def validate_eth_address(cls, v):
        """Validate Ethereum address format"""
        if not is_address(v):
            raise ValueError(f"Invalid Ethereum address: {v}")
        return v.lower()  # Normalize to lowercase
```

---

## 🔧 Fix #6: Make Backend Tests Mandatory in CI/CD

**Status:** 🟡 READY TO IMPLEMENT

### Current Issue:
```yaml
# .github/workflows/backend-ci.yml line 86
- name: Run tests
  run: pytest tests/ -v --cov=. --cov-report=xml || echo "Tests completed with warnings"
  continue-on-error: true  # ⚠️ BAD: Failures ignored!
```

### Fix:

```yaml
# .github/workflows/backend-ci.yml

    - name: Run tests
      working-directory: backend
      run: |
        pytest tests/ -v \
          --cov=. \
          --cov-report=xml \
          --cov-report=term \
          --cov-fail-under=60
      # NO continue-on-error! Tests must pass.

    - name: Upload coverage to Codecov
      if: success()  # Only if tests passed
      uses: codecov/codecov-action@v3
      with:
        file: ./backend/coverage.xml
        flags: backend
        fail_ci_if_error: true

    - name: Check coverage threshold
      working-directory: backend
      run: |
        COVERAGE=$(python -c "import xml.etree.ElementTree as ET; tree = ET.parse('coverage.xml'); print(tree.getroot().attrib['line-rate'])")
        COVERAGE_PCT=$(python -c "print(float($COVERAGE) * 100)")
        echo "Coverage: ${COVERAGE_PCT}%"

        if (( $(echo "$COVERAGE_PCT < 60" | bc -l) )); then
          echo "❌ Coverage ${COVERAGE_PCT}% is below 60% threshold"
          exit 1
        fi

        echo "✅ Coverage threshold met: ${COVERAGE_PCT}%"
```

### Also Fix: Database Migrations

```yaml
# .github/workflows/backend-ci.yml line 80
    - name: Run database migrations
      working-directory: backend
      run: alembic upgrade head
      # Remove: continue-on-error: true
      env:
        DATABASE_URL: ${{ env.DATABASE_URL }}
```

### And: Linting

```yaml
    - name: Lint with flake8
      working-directory: backend
      run: |
        flake8 . --count --select=E9,F63,F7,F82 --show-source --statistics
        flake8 . --count --exit-zero --max-complexity=10 --max-line-length=127 --statistics
      # Remove: continue-on-error: true
```

---

## ✅ Implementation Checklist

### Security Fixes
- [x] Fix #1: Webhook signatures - DONE ✅
- [ ] Fix #2: Rate limiting - Implement in app.py
- [ ] Fix #3: API key hardening - Update verify_api_key()
- [ ] Fix #4: Wallet encryption - Create encryption service + migration
- [ ] Fix #5: Input validation - Add Field constraints to models
- [ ] Fix #6: CI/CD tests - Remove continue-on-error

### Testing
- [ ] Test rate limiting with load script
- [ ] Test API key validation fails without env var
- [ ] Test wallet creation stores encrypted keys
- [ ] Test input validation rejects invalid amounts
- [ ] Test CI/CD fails on test failures

### Documentation
- [ ] Update .env.example with new variables
- [ ] Document wallet encryption key generation
- [ ] Update API documentation with new validation
- [ ] Add rate limiting info to README

---

## 🎯 Success Criteria

After implementing all fixes:

1. ✅ All webhook endpoints verify signatures
2. ✅ Rate limits prevent abuse (tested with 100+ rapid requests)
3. ✅ API key validation fails fast if not configured
4. ✅ Wallet private keys encrypted in database
5. ✅ Invalid input rejected with clear error messages
6. ✅ CI/CD pipeline fails if tests fail
7. ✅ Security score improved from 7.5/10 to 9/10

---

## 📞 Next Steps

1. **Implement fixes** using code above
2. **Test each fix** individually
3. **Run full test suite**
4. **Deploy to testnet** and validate
5. **Proceed with backend testing** (area #3)

---

**Estimated Time:** 2-3 days for all fixes
**Priority:** CRITICAL - Complete before any mainnet deployment
