"""
Webhook Authentication Middleware
Provides HMAC-SHA256 signature verification for incoming webhooks
"""
import hmac
import hashlib
import time
from typing import Optional
from fastapi import Header, HTTPException, Request
import logging

logger = logging.getLogger(__name__)

# Maximum age of webhook (5 minutes)
MAX_WEBHOOK_AGE_SECONDS = 300


def verify_webhook_signature(
    payload: bytes,
    signature: str,
    secret: str,
    timestamp: Optional[str] = None
) -> bool:
    """
    Verify HMAC-SHA256 signature for webhook payload

    Args:
        payload: Raw request body as bytes
        signature: Signature from webhook header
        secret: Shared secret for HMAC
        timestamp: Optional timestamp for replay attack prevention

    Returns:
        bool: True if signature is valid, False otherwise
    """
    if not signature or not secret:
        logger.warning("Missing signature or secret")
        return False

    # Verify timestamp if provided (prevent replay attacks)
    if timestamp:
        try:
            webhook_time = int(timestamp)
            current_time = int(time.time())
            age = current_time - webhook_time

            if age > MAX_WEBHOOK_AGE_SECONDS:
                logger.warning(f"Webhook too old: {age} seconds (max: {MAX_WEBHOOK_AGE_SECONDS})")
                return False

            if age < -60:  # Allow 60 seconds clock skew
                logger.warning(f"Webhook timestamp in future: {age} seconds")
                return False

        except (ValueError, TypeError) as e:
            logger.warning(f"Invalid timestamp: {timestamp}, error: {e}")
            return False

    # Compute expected signature
    expected_signature = hmac.new(
        secret.encode('utf-8'),
        payload,
        hashlib.sha256
    ).hexdigest()

    # Constant-time comparison to prevent timing attacks
    return hmac.compare_digest(signature, expected_signature)


async def verify_aurora_webhook(
    request: Request,
    x_aurora_signature: str = Header(None),
    x_aurora_timestamp: str = Header(None)
) -> bool:
    """
    Verify Aurora PMS webhook signature

    Raises:
        HTTPException: If signature is invalid
    """
    import os

    # Get webhook secret from environment
    secret = os.getenv("AURORA_WEBHOOK_SECRET", "")

    if not secret:
        logger.error("AURORA_WEBHOOK_SECRET not configured")
        raise HTTPException(
            status_code=500,
            detail="Webhook authentication not configured"
        )

    if not x_aurora_signature:
        logger.warning("Missing X-Aurora-Signature header")
        raise HTTPException(
            status_code=401,
            detail="Missing webhook signature"
        )

    # Get raw request body
    body = await request.body()

    # Verify signature
    is_valid = verify_webhook_signature(
        payload=body,
        signature=x_aurora_signature,
        secret=secret,
        timestamp=x_aurora_timestamp
    )

    if not is_valid:
        logger.warning(f"Invalid Aurora webhook signature from {request.client.host}")
        raise HTTPException(
            status_code=401,
            detail="Invalid webhook signature"
        )

    return True


async def verify_tribe_webhook(
    request: Request,
    x_tribe_signature: str = Header(None),
    x_tribe_timestamp: str = Header(None)
) -> bool:
    """
    Verify Tribe App webhook signature

    Raises:
        HTTPException: If signature is invalid
    """
    import os

    # Get webhook secret from environment
    secret = os.getenv("TRIBE_WEBHOOK_SECRET", "")

    if not secret:
        logger.error("TRIBE_WEBHOOK_SECRET not configured")
        raise HTTPException(
            status_code=500,
            detail="Webhook authentication not configured"
        )

    if not x_tribe_signature:
        logger.warning("Missing X-Tribe-Signature header")
        raise HTTPException(
            status_code=401,
            detail="Missing webhook signature"
        )

    # Get raw request body
    body = await request.body()

    # Verify signature
    is_valid = verify_webhook_signature(
        payload=body,
        signature=x_tribe_signature,
        secret=secret,
        timestamp=x_tribe_timestamp
    )

    if not is_valid:
        logger.warning(f"Invalid Tribe webhook signature from {request.client.host}")
        raise HTTPException(
            status_code=401,
            detail="Invalid webhook signature"
        )

    return True


def generate_webhook_signature(payload: bytes, secret: str, timestamp: Optional[int] = None) -> dict:
    """
    Generate webhook signature for testing

    Args:
        payload: Request body as bytes
        secret: Shared secret
        timestamp: Unix timestamp (defaults to current time)

    Returns:
        dict: Headers to include in webhook request
    """
    if timestamp is None:
        timestamp = int(time.time())

    signature = hmac.new(
        secret.encode('utf-8'),
        payload,
        hashlib.sha256
    ).hexdigest()

    return {
        "signature": signature,
        "timestamp": str(timestamp)
    }


# Example usage in tests:
"""
from middleware.webhook_auth import generate_webhook_signature
import json

# Create test payload
payload = {"booking_id": "123", "amount": 100}
payload_bytes = json.dumps(payload).encode('utf-8')

# Generate signature
headers = generate_webhook_signature(payload_bytes, "test_secret")

# Make request with headers
response = client.post(
    "/webhooks/aurora/booking-created",
    json=payload,
    headers={
        "X-Aurora-Signature": headers["signature"],
        "X-Aurora-Timestamp": headers["timestamp"]
    }
)
"""
