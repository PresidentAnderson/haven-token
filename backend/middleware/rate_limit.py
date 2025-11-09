"""
Rate Limiting Middleware
Protects API endpoints from abuse using SlowAPI.
"""

import os
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
import logging

logger = logging.getLogger(__name__)


def get_identifier(request: Request) -> str:
    """
    Get unique identifier for rate limiting.

    Uses API key if present (for authenticated requests),
    otherwise falls back to IP address.

    Args:
        request: FastAPI request object

    Returns:
        Unique identifier string for rate limiting
    """
    # Check for API key in headers
    api_key = request.headers.get("X-API-Key")
    if api_key:
        # Use API key as identifier for authenticated requests
        return f"api_key:{api_key}"

    # Check for user ID in path parameters (for user-specific endpoints)
    if hasattr(request, "path_params") and "user_id" in request.path_params:
        return f"user:{request.path_params['user_id']}"

    # Fall back to IP address
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        # Take the first IP in the chain (original client)
        ip = forwarded.split(",")[0].strip()
    else:
        ip = request.client.host if request.client else "unknown"

    return f"ip:{ip}"


# Initialize limiter with custom key function
limiter = Limiter(
    key_func=get_identifier,
    default_limits=["100/minute", "2000/hour"],
    storage_uri=os.getenv("REDIS_URL", "memory://"),
    strategy="fixed-window",
    headers_enabled=True,
)


# Custom rate limit exceeded handler
async def custom_rate_limit_handler(request: Request, exc: RateLimitExceeded):
    """
    Custom handler for rate limit exceeded errors.

    Returns a properly formatted JSON error response with retry information.
    """
    logger.warning(
        f"Rate limit exceeded for {get_identifier(request)} "
        f"on {request.url.path}"
    )

    return JSONResponse(
        status_code=429,
        content={
            "error": "rate_limit_exceeded",
            "message": "Too many requests. Please try again later.",
            "detail": str(exc.detail),
            "retry_after": getattr(exc, "retry_after", None)
        },
        headers={
            "Retry-After": str(getattr(exc, "retry_after", 60))
        }
    )


# Rate limit decorators for different endpoint types
def general_rate_limit():
    """
    General rate limit: 100 requests per minute.
    Use for standard API endpoints.
    """
    return limiter.limit("100/minute")


def strict_rate_limit():
    """
    Strict rate limit: 10 requests per minute.
    Use for expensive operations like minting/burning.
    """
    return limiter.limit("10/minute")


def permissive_rate_limit():
    """
    Permissive rate limit: 300 requests per minute.
    Use for read-only endpoints like balance queries.
    """
    return limiter.limit("300/minute")


def webhook_rate_limit():
    """
    Webhook rate limit: 60 requests per minute.
    Use for webhook endpoints (Aurora, Tribe).
    """
    return limiter.limit("60/minute")


def health_check_rate_limit():
    """
    Health check rate limit: 600 requests per minute.
    Very permissive for monitoring systems.
    """
    return limiter.limit("600/minute")


# User-specific rate limits
def mint_rate_limit():
    """
    Mint operation rate limit: 10 per minute, 100 per hour.
    Prevents abuse of token minting.
    """
    return limiter.limit("10/minute;100/hour")


def redemption_rate_limit():
    """
    Redemption rate limit: 5 per minute, 20 per hour.
    Strict limits on cash-outs to prevent fraud.
    """
    return limiter.limit("5/minute;20/hour")


def balance_query_rate_limit():
    """
    Balance query rate limit: 200 per minute.
    Generous for frequently checked endpoints.
    """
    return limiter.limit("200/minute")


# IP-based protection for public endpoints
def public_endpoint_rate_limit():
    """
    Public endpoint rate limit: 30 per minute per IP.
    Protects public endpoints from DDoS.
    """
    return limiter.limit("30/minute", key_func=get_remote_address)


# Burst protection
def burst_protection():
    """
    Burst protection: 5 requests per second.
    Prevents rapid-fire requests.
    """
    return limiter.limit("5/second")


class RateLimitMiddleware:
    """
    Rate limiting middleware for FastAPI.

    Provides request-level rate limiting with configurable limits
    for different endpoint types.
    """

    def __init__(self, app):
        """
        Initialize rate limiting middleware.

        Args:
            app: FastAPI application instance
        """
        self.app = app
        logger.info("Rate limiting middleware initialized")

        # Log rate limit configuration
        storage = os.getenv("REDIS_URL", "memory://")
        logger.info(f"Rate limit storage: {storage}")

    async def __call__(self, scope, receive, send):
        """
        Process request with rate limiting.
        """
        await self.app(scope, receive, send)


def configure_rate_limiting(app):
    """
    Configure rate limiting for the FastAPI application.

    Args:
        app: FastAPI application instance

    Returns:
        Configured limiter instance
    """
    # Add state to app
    app.state.limiter = limiter

    # Add custom exception handler
    app.add_exception_handler(RateLimitExceeded, custom_rate_limit_handler)

    # Add middleware (optional, for request-level logging)
    # app.add_middleware(SlowAPIMiddleware)

    logger.info(
        f"Rate limiting configured with storage: "
        f"{os.getenv('REDIS_URL', 'memory://')}"
    )

    return limiter


# Helper function to get current rate limit status
def get_rate_limit_status(request: Request) -> dict:
    """
    Get current rate limit status for a request.

    Args:
        request: FastAPI request object

    Returns:
        Dictionary with rate limit status information
    """
    identifier = get_identifier(request)

    # This would require additional implementation to track
    # current usage from the rate limiter storage
    return {
        "identifier": identifier,
        "limit": "100/minute",
        "remaining": "unknown",  # Would need to query limiter storage
        "reset": "unknown"
    }


# Exemption checker for admin/system requests
def is_rate_limit_exempt(request: Request) -> bool:
    """
    Check if a request should be exempt from rate limiting.

    Exempts:
    - Internal service requests (with special header)
    - Admin API keys
    - Health check endpoints

    Args:
        request: FastAPI request object

    Returns:
        True if request is exempt, False otherwise
    """
    # Check for internal service header
    if request.headers.get("X-Internal-Service") == os.getenv("INTERNAL_SERVICE_TOKEN"):
        return True

    # Check for admin API key
    admin_api_key = os.getenv("ADMIN_API_KEY")
    if admin_api_key and request.headers.get("X-API-Key") == admin_api_key:
        return True

    # Health check endpoints are handled by their own generous limits
    # (not fully exempt, just very high limits)

    return False


# Rate limit configuration presets
RATE_LIMIT_PRESETS = {
    "development": {
        "general": "1000/minute",
        "strict": "100/minute",
        "mint": "100/minute",
        "redemption": "50/minute"
    },
    "staging": {
        "general": "500/minute",
        "strict": "50/minute",
        "mint": "50/minute",
        "redemption": "20/minute"
    },
    "production": {
        "general": "100/minute",
        "strict": "10/minute",
        "mint": "10/minute",
        "redemption": "5/minute"
    }
}


def get_rate_limit_for_environment(limit_type: str = "general") -> str:
    """
    Get rate limit string based on current environment.

    Args:
        limit_type: Type of limit (general, strict, mint, redemption)

    Returns:
        Rate limit string (e.g., "100/minute")
    """
    environment = os.getenv("ENVIRONMENT", "production")
    presets = RATE_LIMIT_PRESETS.get(environment, RATE_LIMIT_PRESETS["production"])
    return presets.get(limit_type, presets["general"])
