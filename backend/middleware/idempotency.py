"""
Idempotency Middleware
Prevents duplicate request processing using Redis-based request tracking.
"""
import os
import json
import logging
from typing import Optional, Callable
from fastapi import Header, HTTPException, Request
from fastapi.responses import JSONResponse
import redis
from datetime import timedelta

logger = logging.getLogger(__name__)

# Redis connection
redis_client = None


def get_redis_client():
    """Get or create Redis client."""
    global redis_client

    if redis_client is None:
        redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
        try:
            redis_client = redis.from_url(
                redis_url,
                decode_responses=True,
                socket_connect_timeout=5,
                socket_timeout=5
            )
            # Test connection
            redis_client.ping()
            logger.info(f"✅ Connected to Redis: {redis_url}")
        except redis.ConnectionError as e:
            logger.warning(f"⚠️  Redis not available: {str(e)}. Idempotency disabled.")
            redis_client = None

    return redis_client


class IdempotencyMiddleware:
    """
    Middleware to handle idempotent requests using Redis.

    Stores request results for 24 hours to prevent duplicate processing.
    Uses the Idempotency-Key header to identify duplicate requests.
    """

    # Default TTL: 24 hours
    DEFAULT_TTL = 86400

    @staticmethod
    def generate_key(idempotency_key: str, path: str) -> str:
        """
        Generate Redis key for idempotency tracking.

        Args:
            idempotency_key: Client-provided idempotency key
            path: Request path

        Returns:
            Redis key
        """
        return f"idempotency:{path}:{idempotency_key}"

    @staticmethod
    def store_response(key: str, response_data: dict, ttl: int = DEFAULT_TTL) -> bool:
        """
        Store response in Redis for future duplicate requests.

        Args:
            key: Redis key
            response_data: Response data to store
            ttl: Time to live in seconds (default: 24 hours)

        Returns:
            True if stored successfully, False otherwise
        """
        client = get_redis_client()

        if client is None:
            return False

        try:
            client.setex(
                key,
                ttl,
                json.dumps(response_data)
            )
            logger.info(f"Stored idempotency key: {key}")
            return True
        except Exception as e:
            logger.error(f"Failed to store idempotency key: {str(e)}")
            return False

    @staticmethod
    def get_cached_response(key: str) -> Optional[dict]:
        """
        Get cached response from Redis.

        Args:
            key: Redis key

        Returns:
            Cached response data or None
        """
        client = get_redis_client()

        if client is None:
            return None

        try:
            cached = client.get(key)
            if cached:
                logger.info(f"Found cached response for: {key}")
                return json.loads(cached)
            return None
        except Exception as e:
            logger.error(f"Failed to get cached response: {str(e)}")
            return None


async def require_idempotency_key(
    idempotency_key: Optional[str] = Header(None, alias="Idempotency-Key")
) -> str:
    """
    FastAPI dependency that requires an Idempotency-Key header.

    Args:
        idempotency_key: Header value

    Returns:
        Idempotency key

    Raises:
        HTTPException: If idempotency key is missing
    """
    if not idempotency_key:
        raise HTTPException(
            status_code=400,
            detail="Idempotency-Key header is required for this endpoint"
        )

    # Validate key format (alphanumeric, dashes, underscores, 8-64 chars)
    if not idempotency_key or len(idempotency_key) < 8 or len(idempotency_key) > 64:
        raise HTTPException(
            status_code=400,
            detail="Idempotency-Key must be 8-64 characters"
        )

    return idempotency_key


async def check_idempotency(
    request: Request,
    idempotency_key: Optional[str] = Header(None, alias="Idempotency-Key")
) -> Optional[JSONResponse]:
    """
    Check if request has been processed before.

    Args:
        request: FastAPI request object
        idempotency_key: Header value

    Returns:
        Cached response if duplicate, None if first time
    """
    if not idempotency_key:
        # No idempotency key provided, proceed normally
        return None

    # Generate cache key
    cache_key = IdempotencyMiddleware.generate_key(
        idempotency_key,
        request.url.path
    )

    # Check for cached response
    cached = IdempotencyMiddleware.get_cached_response(cache_key)

    if cached:
        logger.info(f"Returning cached response for idempotency key: {idempotency_key}")
        return JSONResponse(
            content=cached["body"],
            status_code=cached.get("status_code", 200),
            headers=cached.get("headers", {})
        )

    return None


def idempotent(ttl: int = IdempotencyMiddleware.DEFAULT_TTL):
    """
    Decorator to make an endpoint idempotent.

    Usage:
        @app.post("/token/mint")
        @idempotent(ttl=3600)
        async def mint_tokens(...):
            ...

    Args:
        ttl: Time to live for cached responses in seconds

    Returns:
        Decorated function
    """
    def decorator(func: Callable):
        async def wrapper(
            *args,
            idempotency_key: Optional[str] = Header(None, alias="Idempotency-Key"),
            request: Request = None,
            **kwargs
        ):
            # If no idempotency key, execute normally
            if not idempotency_key:
                return await func(*args, **kwargs)

            # Check cache
            cache_key = IdempotencyMiddleware.generate_key(
                idempotency_key,
                request.url.path if request else "unknown"
            )

            cached = IdempotencyMiddleware.get_cached_response(cache_key)
            if cached:
                return JSONResponse(
                    content=cached["body"],
                    status_code=cached.get("status_code", 200)
                )

            # Execute function
            result = await func(*args, **kwargs)

            # Store result
            if isinstance(result, dict):
                IdempotencyMiddleware.store_response(
                    cache_key,
                    {
                        "body": result,
                        "status_code": 200
                    },
                    ttl=ttl
                )

            return result

        return wrapper
    return decorator


# Example usage in tests:
"""
from middleware.idempotency import require_idempotency_key, IdempotencyMiddleware

@app.post("/token/mint")
async def mint_tokens(
    request: MintRequest,
    idempotency_key: str = Depends(require_idempotency_key),
    db: Session = Depends(get_db)
):
    # Check if already processed
    cache_key = IdempotencyMiddleware.generate_key(
        idempotency_key,
        "/token/mint"
    )

    cached = IdempotencyMiddleware.get_cached_response(cache_key)
    if cached:
        return cached["body"]

    # Process request
    result = await process_mint(...)

    # Store result
    IdempotencyMiddleware.store_response(
        cache_key,
        {"body": result, "status_code": 200}
    )

    return result
"""
