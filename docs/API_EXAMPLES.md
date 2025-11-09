# HAVEN Token API Examples

Complete guide to using the HAVEN Token API with real-world examples.

## Table of Contents

- [Authentication](#authentication)
- [Token Operations](#token-operations)
- [Aurora Webhooks](#aurora-webhooks)
- [Tribe Webhooks](#tribe-webhooks)
- [Analytics](#analytics)
- [Rate Limits](#rate-limits)
- [Error Handling](#error-handling)
- [Idempotency](#idempotency)

---

## Authentication

All protected endpoints require API key authentication via the `X-API-Key` header.

### Example: Authenticated Request

```bash
curl -X POST https://api.haventoken.com/token/mint \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your_api_key_here" \
  -d '{
    "user_id": "user_12345",
    "amount": 100.0,
    "reason": "booking_reward",
    "idempotency_key": "mint_booking_789"
  }'
```

### Response

```json
{
  "status": "queued",
  "tx_id": "mint_booking_789",
  "message": "Mint transaction queued"
}
```

---

## Token Operations

### 1. Mint Tokens

Mint new tokens to a user's wallet.

**Endpoint:** `POST /token/mint`
**Authentication:** Required (API Key)
**Idempotency:** Supported via `idempotency_key`

#### Request Body

```json
{
  "user_id": "string",           // Required: User ID
  "amount": 100.0,               // Required: Amount to mint (HNV)
  "reason": "string",            // Required: Reason for minting
  "idempotency_key": "string"    // Optional: For duplicate prevention
}
```

#### Example: Mint Tokens for Booking Reward

```bash
curl -X POST https://api.haventoken.com/token/mint \
  -H "Content-Type: application/json" \
  -H "X-API-Key: sk_live_abc123..." \
  -d '{
    "user_id": "aurora_guest_456",
    "amount": 1200.0,
    "reason": "booking_reward_5_nights",
    "idempotency_key": "booking_abc123_mint"
  }'
```

#### Success Response (200 OK)

```json
{
  "status": "queued",
  "tx_id": "booking_abc123_mint",
  "message": "Mint transaction queued"
}
```

#### Duplicate Request Response (200 OK)

```json
{
  "status": "duplicate",
  "tx_id": "booking_abc123_mint",
  "message": "Transaction already processed"
}
```

#### Error Response (401 Unauthorized)

```json
{
  "detail": "Invalid API key"
}
```

#### Error Response (500 Internal Server Error)

```json
{
  "detail": "Blockchain connection error"
}
```

---

### 2. Redeem Tokens

Redeem (burn) tokens for fiat payout.

**Endpoint:** `POST /token/redeem`
**Authentication:** Required (API Key)
**Idempotency:** Required via `idempotency_key`

#### Request Body

```json
{
  "user_id": "string",              // Required: User ID
  "amount": 100.0,                  // Required: Amount to redeem
  "withdrawal_method": "string",    // Required: "bank_transfer" | "paypal" | "crypto"
  "withdrawal_address": "string",   // Optional: Destination address
  "idempotency_key": "string"       // Required: Unique request ID
}
```

#### Example: Redeem for Bank Transfer

```bash
curl -X POST https://api.haventoken.com/token/redeem \
  -H "Content-Type: application/json" \
  -H "X-API-Key: sk_live_abc123..." \
  -d '{
    "user_id": "user_12345",
    "amount": 500.0,
    "withdrawal_method": "bank_transfer",
    "withdrawal_address": "CA123456789",
    "idempotency_key": "redeem_user12345_20250115"
  }'
```

#### Success Response (200 OK)

```json
{
  "status": "queued",
  "request_id": "redeem_user12345_20250115",
  "burn_amount": 500.0,
  "payout_amount": 490.0,
  "message": "Redemption queued"
}
```

Note: 2% burn fee applied (500 * 0.98 = 490 payout).

#### Error Response (400 Bad Request)

```json
{
  "detail": "Insufficient balance"
}
```

#### Error Response (404 Not Found)

```json
{
  "detail": "User not found"
}
```

---

### 3. Get User Balance

Get current token balance for a user.

**Endpoint:** `GET /token/balance/{user_id}`
**Authentication:** Not required (public read)

#### Example Request

```bash
curl https://api.haventoken.com/token/balance/user_12345
```

#### Success Response (200 OK)

```json
{
  "user_id": "user_12345",
  "wallet_address": "0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb",
  "balance": 1250.5
}
```

#### Error Response (404 Not Found)

```json
{
  "detail": "User not found"
}
```

---

## Aurora Webhooks

Aurora PMS sends webhooks for booking lifecycle events.

### 1. Booking Created

Triggered when a new booking is created.

**Endpoint:** `POST /webhooks/aurora/booking-created`
**Authentication:** Webhook signature verification

#### Request Headers

```
X-Aurora-Signature: sha256_hmac_signature_here
Content-Type: application/json
```

#### Request Body

```json
{
  "id": "booking_789",
  "guest_id": "guest_456",
  "guest_email": "guest@example.com",
  "total_price": 750.0,
  "nights": 4,
  "status": "confirmed",
  "check_in": "2025-02-01",
  "check_out": "2025-02-05"
}
```

#### Example with Signature

```bash
# Generate HMAC signature
PAYLOAD='{"id":"booking_789","guest_id":"guest_456","total_price":750.0,"nights":4}'
SECRET="your_aurora_webhook_secret"
SIGNATURE=$(echo -n "$PAYLOAD" | openssl dgst -sha256 -hmac "$SECRET" | awk '{print $2}')

curl -X POST https://api.haventoken.com/webhooks/aurora/booking-created \
  -H "Content-Type: application/json" \
  -H "X-Aurora-Signature: $SIGNATURE" \
  -d "$PAYLOAD"
```

#### Success Response (200 OK)

```json
{
  "status": "accepted"
}
```

#### Error Response (401 Unauthorized)

```json
{
  "detail": "Invalid signature"
}
```

---

### 2. Booking Completed

Triggered when guest checks out.

**Endpoint:** `POST /webhooks/aurora/booking-completed`

#### Request Body

```json
{
  "id": "booking_789",
  "guest_id": "guest_456",
  "status": "completed",
  "checkout_date": "2025-02-05"
}
```

#### Example Request

```bash
curl -X POST https://api.haventoken.com/webhooks/aurora/booking-completed \
  -H "Content-Type: application/json" \
  -d '{
    "id": "booking_789",
    "guest_id": "guest_456",
    "status": "completed"
  }'
```

---

### 3. Booking Cancelled

Triggered when booking is cancelled (burns previously minted tokens).

**Endpoint:** `POST /webhooks/aurora/booking-cancelled`

#### Request Body

```json
{
  "id": "booking_789",
  "guest_id": "guest_456",
  "status": "cancelled",
  "cancellation_reason": "customer_request"
}
```

---

### 4. Review Submitted

Triggered when guest submits a review.

**Endpoint:** `POST /webhooks/aurora/review-submitted`

#### Request Body

```json
{
  "id": "review_123",
  "booking_id": "booking_789",
  "guest_id": "guest_456",
  "rating": 5,
  "comment": "Amazing stay!",
  "created_at": "2025-02-06T10:30:00Z"
}
```

Positive reviews (4+ stars) grant 50 HNV bonus.

---

## Tribe Webhooks

Tribe app sends webhooks for community events.

### 1. Event Attendance

Triggered when user attends an event.

**Endpoint:** `POST /webhooks/tribe/event-attendance`

#### Request Body

```json
{
  "id": "event_456",
  "attendee_id": "user_12345",
  "name": "Weekly Wisdom Circle",
  "type": "wisdom_circle",
  "attended_at": "2025-01-20T18:00:00Z"
}
```

#### Reward Tiers

- `wisdom_circle`: 100 HNV
- `workshop`: 75 HNV
- `networking`: 50 HNV
- `general`: 25 HNV

#### Example Request

```bash
curl -X POST https://api.haventoken.com/webhooks/tribe/event-attendance \
  -H "Content-Type: application/json" \
  -d '{
    "id": "event_456",
    "attendee_id": "user_12345",
    "name": "Leadership Workshop",
    "type": "workshop"
  }'
```

---

### 2. Community Contribution

Triggered when user contributes to community.

**Endpoint:** `POST /webhooks/tribe/contribution`

#### Request Body

```json
{
  "id": "contrib_789",
  "user_id": "user_12345",
  "type": "guide",
  "quality_score": 1.5,
  "title": "How to Network Effectively"
}
```

#### Contribution Types & Base Rewards

- `guide`: 25 HNV
- `resource`: 15 HNV
- `post`: 10 HNV
- `comment`: 5 HNV

Multiplied by `quality_score` (0.5 - 2.0).

---

### 3. Staking Started

Triggered when user stakes tokens.

**Endpoint:** `POST /webhooks/tribe/staking-started`

#### Request Body

```json
{
  "id": "stake_001",
  "user_id": "user_12345",
  "amount": 5000.0,
  "started_at": "2025-01-15T12:00:00Z"
}
```

---

### 4. Coaching Milestone

Triggered when user completes coaching milestone.

**Endpoint:** `POST /webhooks/tribe/coaching-milestone`

#### Request Body

```json
{
  "user_id": "user_12345",
  "milestone_name": "First Quarter Goals Achieved",
  "tier": "intermediate",
  "completed_at": "2025-03-31T23:59:59Z"
}
```

#### Tier Rewards

- `basic`: 100 HNV
- `intermediate`: 175 HNV
- `advanced`: 250 HNV

---

### 5. Referral Success

Triggered when referral completes first action.

**Endpoint:** `POST /webhooks/tribe/referral-success`

#### Request Body

```json
{
  "referrer_id": "user_12345",
  "referred_id": "new_user_789",
  "tier": "gold",
  "completed_at": "2025-01-20T14:30:00Z"
}
```

#### Tier Rewards

- `basic`: 100 HNV
- `silver`: 250 HNV
- `gold`: 500 HNV

---

## Analytics

### 1. User Analytics

Get comprehensive user statistics.

**Endpoint:** `GET /analytics/user/{user_id}`

#### Example Request

```bash
curl https://api.haventoken.com/analytics/user/user_12345
```

#### Success Response (200 OK)

```json
{
  "user_id": "user_12345",
  "email": "user@example.com",
  "wallet_address": "0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb",
  "balance": 1250.5,
  "total_earned": 3500.0,
  "total_redeemed": 2249.5,
  "kyc_verified": true
}
```

---

### 2. Token Statistics

Get global token statistics.

**Endpoint:** `GET /analytics/token-stats`

#### Example Request

```bash
curl https://api.haventoken.com/analytics/token-stats
```

#### Success Response (200 OK)

```json
{
  "total_minted": 250000.0,
  "total_burned": 50000.0,
  "circulating_supply": 200000.0,
  "total_users": 1523,
  "total_transactions": 8945
}
```

---

### 3. Transaction History

Get user transaction history with pagination.

**Endpoint:** `GET /analytics/transactions/{user_id}?limit=50&offset=0`

#### Example Request

```bash
curl https://api.haventoken.com/analytics/transactions/user_12345?limit=10&offset=0
```

#### Success Response (200 OK)

```json
{
  "user_id": "user_12345",
  "count": 10,
  "transactions": [
    {
      "tx_id": "mint_booking_789",
      "user_id": "user_12345",
      "tx_type": "mint",
      "amount": 1200.0,
      "status": "confirmed",
      "blockchain_tx": "0x1234567890abcdef...",
      "created_at": "2025-01-20T10:30:00Z",
      "confirmed_at": "2025-01-20T10:31:15Z"
    }
  ]
}
```

---

## Rate Limits

API rate limits protect the service from abuse.

### Limits

- **Public endpoints:** 100 requests/minute
- **Authenticated endpoints:** 1000 requests/minute
- **Webhook endpoints:** 500 requests/minute

### Rate Limit Headers

```
X-RateLimit-Limit: 1000
X-RateLimit-Remaining: 987
X-RateLimit-Reset: 1642687200
```

### Rate Limit Exceeded Response (429)

```json
{
  "detail": "Rate limit exceeded",
  "retry_after": 60
}
```

---

## Error Handling

### Standard Error Response Format

```json
{
  "detail": "Error message here",
  "error_code": "SPECIFIC_ERROR_CODE",
  "correlation_id": "req_abc123xyz"
}
```

### Common HTTP Status Codes

- `200 OK`: Success
- `400 Bad Request`: Invalid request data
- `401 Unauthorized`: Invalid or missing API key
- `404 Not Found`: Resource not found
- `422 Unprocessable Entity`: Validation error
- `429 Too Many Requests`: Rate limit exceeded
- `500 Internal Server Error`: Server error
- `503 Service Unavailable`: Service temporarily unavailable

### Example: Validation Error (422)

```json
{
  "detail": [
    {
      "loc": ["body", "amount"],
      "msg": "ensure this value is greater than 0",
      "type": "value_error.number.not_gt"
    }
  ]
}
```

---

## Idempotency

Idempotency keys prevent duplicate processing of critical operations.

### How It Works

1. Include `idempotency_key` in request
2. First request processes normally
3. Duplicate requests return cached response
4. Keys expire after 24 hours

### Example: Idempotent Mint Request

```bash
# First request
curl -X POST https://api.haventoken.com/token/mint \
  -H "X-API-Key: sk_live_abc123..." \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "user_12345",
    "amount": 100.0,
    "reason": "reward",
    "idempotency_key": "unique_key_12345"
  }'
```

**Response:**
```json
{
  "status": "queued",
  "tx_id": "unique_key_12345"
}
```

```bash
# Duplicate request (same idempotency_key)
curl -X POST https://api.haventoken.com/token/mint \
  -H "X-API-Key: sk_live_abc123..." \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "user_12345",
    "amount": 100.0,
    "reason": "reward",
    "idempotency_key": "unique_key_12345"
  }'
```

**Response:**
```json
{
  "status": "duplicate",
  "tx_id": "unique_key_12345",
  "message": "Transaction already processed"
}
```

### Best Practices

1. **Always use idempotency keys** for mint/redeem operations
2. **Use unique, deterministic keys**: `{operation}_{resource_id}_{timestamp}`
3. **Store keys on your side** to retry failed requests
4. **Don't reuse keys** for different operations

---

## Complete Integration Examples

### Example 1: Aurora Booking Flow

```bash
# 1. Booking created in Aurora PMS
# 2. Aurora sends webhook
curl -X POST https://api.haventoken.com/webhooks/aurora/booking-created \
  -H "X-Aurora-Signature: sha256_signature" \
  -H "Content-Type: application/json" \
  -d '{
    "id": "booking_2025_001",
    "guest_id": "guest_abc",
    "total_price": 1000.0,
    "nights": 5
  }'

# 3. System automatically:
#    - Creates/finds user wallet
#    - Calculates reward: 1000 * 2.0 * 1.2 = 2400 HNV
#    - Mints tokens to wallet
#    - Records transaction

# 4. Guest checks balance
curl https://api.haventoken.com/token/balance/guest_abc

# Response:
# {
#   "user_id": "guest_abc",
#   "balance": 2400.0
# }

# 5. Guest submits 5-star review
curl -X POST https://api.haventoken.com/webhooks/aurora/review-submitted \
  -H "Content-Type: application/json" \
  -d '{
    "id": "review_001",
    "booking_id": "booking_2025_001",
    "guest_id": "guest_abc",
    "rating": 5
  }'

# 6. System mints 50 HNV review bonus
# 7. New balance: 2450 HNV
```

### Example 2: Token Redemption Flow

```bash
# 1. User requests redemption
curl -X POST https://api.haventoken.com/token/redeem \
  -H "X-API-Key: sk_live_abc123..." \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "user_12345",
    "amount": 1000.0,
    "withdrawal_method": "bank_transfer",
    "withdrawal_address": "CA987654321",
    "idempotency_key": "redeem_20250120_user12345"
  }'

# Response:
# {
#   "status": "queued",
#   "burn_amount": 1000.0,
#   "payout_amount": 980.0
# }

# 2. System processes:
#    - Burns 1000 HNV
#    - Initiates $980 CAD payout (2% burn fee)
#    - Updates redemption status

# 3. Check transaction status
curl https://api.haventoken.com/analytics/transactions/user_12345?limit=1

# Response includes burn transaction
```

---

## SDK Examples

### Python SDK Example

```python
import requests

class HavenTokenAPI:
    def __init__(self, api_key, base_url="https://api.haventoken.com"):
        self.api_key = api_key
        self.base_url = base_url
        self.headers = {
            "X-API-Key": api_key,
            "Content-Type": "application/json"
        }

    def mint_tokens(self, user_id, amount, reason, idempotency_key=None):
        """Mint tokens to a user."""
        payload = {
            "user_id": user_id,
            "amount": amount,
            "reason": reason,
            "idempotency_key": idempotency_key
        }
        response = requests.post(
            f"{self.base_url}/token/mint",
            json=payload,
            headers=self.headers
        )
        return response.json()

    def get_balance(self, user_id):
        """Get user token balance."""
        response = requests.get(f"{self.base_url}/token/balance/{user_id}")
        return response.json()

# Usage
api = HavenTokenAPI("sk_live_abc123...")
result = api.mint_tokens(
    user_id="user_12345",
    amount=100.0,
    reason="test_reward",
    idempotency_key="test_001"
)
print(result)
```

### Node.js SDK Example

```javascript
const axios = require('axios');

class HavenTokenAPI {
  constructor(apiKey, baseURL = 'https://api.haventoken.com') {
    this.apiKey = apiKey;
    this.baseURL = baseURL;
    this.headers = {
      'X-API-Key': apiKey,
      'Content-Type': 'application/json'
    };
  }

  async mintTokens(userId, amount, reason, idempotencyKey = null) {
    const response = await axios.post(
      `${this.baseURL}/token/mint`,
      {
        user_id: userId,
        amount: amount,
        reason: reason,
        idempotency_key: idempotencyKey
      },
      { headers: this.headers }
    );
    return response.data;
  }

  async getBalance(userId) {
    const response = await axios.get(
      `${this.baseURL}/token/balance/${userId}`
    );
    return response.data;
  }
}

// Usage
const api = new HavenTokenAPI('sk_live_abc123...');
api.mintTokens('user_12345', 100.0, 'test_reward', 'test_001')
  .then(result => console.log(result))
  .catch(error => console.error(error));
```

---

## Support

For API support:
- **Documentation:** https://docs.haventoken.com
- **Email:** api-support@haventoken.com
- **Status Page:** https://status.haventoken.com

For urgent issues, include your correlation ID from response headers.
