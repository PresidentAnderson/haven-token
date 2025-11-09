"""
Request Logging Middleware for FastAPI

Adds correlation IDs to all requests and logs API calls with timing.
"""

import time
import logging
from typing import Callable
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

from utils.logging import set_correlation_id, clear_correlation_id, log_api_request


logger = logging.getLogger(__name__)


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """
    Middleware to log all API requests with correlation IDs.

    Features:
    - Generates correlation ID for each request
    - Logs request/response with timing
    - Adds correlation ID to response headers
    - Handles exceptions gracefully
    """

    def __init__(self, app: ASGIApp):
        super().__init__(app)

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request and add logging."""
        # Generate correlation ID
        correlation_id = request.headers.get("X-Correlation-ID")
        if not correlation_id:
            correlation_id = set_correlation_id()
        else:
            set_correlation_id(correlation_id)

        # Record start time
        start_time = time.time()

        # Extract user ID if available (from auth)
        user_id = None
        if hasattr(request.state, 'user_id'):
            user_id = request.state.user_id

        # Process request
        try:
            response = await call_next(request)

            # Calculate duration
            duration_ms = (time.time() - start_time) * 1000

            # Log request
            log_api_request(
                logger=logger,
                method=request.method,
                path=request.url.path,
                status_code=response.status_code,
                duration_ms=duration_ms,
                user_id=user_id,
                extra={
                    'query_params': dict(request.query_params),
                    'client_host': request.client.host if request.client else None
                }
            )

            # Add correlation ID to response headers
            response.headers["X-Correlation-ID"] = correlation_id

            return response

        except Exception as e:
            # Calculate duration
            duration_ms = (time.time() - start_time) * 1000

            # Log error
            logger.error(
                f"Request failed: {request.method} {request.url.path}",
                extra={
                    'extra_fields': {
                        'api_endpoint': request.url.path,
                        'http_method': request.method,
                        'duration_ms': round(duration_ms, 2),
                        'user_id': user_id,
                        'error': str(e)
                    }
                },
                exc_info=True
            )

            # Re-raise exception
            raise

        finally:
            # Clear correlation ID after request
            clear_correlation_id()


class AuditLoggingMiddleware(BaseHTTPMiddleware):
    """
    Middleware for audit logging of sensitive operations.

    Logs to separate audit log file for compliance and security.
    """

    def __init__(self, app: ASGIApp):
        super().__init__(app)
        self.audit_logger = logging.getLogger("audit")

        # Endpoints that require audit logging
        self.audit_paths = [
            "/token/mint",
            "/token/redeem",
            "/token/burn",
            "/admin/"
        ]

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request and add audit logging if needed."""
        # Check if this is an auditable endpoint
        should_audit = any(
            request.url.path.startswith(path)
            for path in self.audit_paths
        )

        if should_audit:
            # Read request body for audit (if JSON)
            body = None
            if request.method in ["POST", "PUT", "PATCH"]:
                try:
                    body = await request.body()
                    # Store for later use by endpoint
                    request._body = body
                except:
                    pass

            # Get user info
            user_id = getattr(request.state, 'user_id', 'anonymous')
            api_key = request.headers.get("X-API-Key", "none")[:16] + "..."

            # Log audit entry
            self.audit_logger.info(
                f"Audit: {request.method} {request.url.path}",
                extra={
                    'extra_fields': {
                        'user_id': user_id,
                        'api_endpoint': request.url.path,
                        'http_method': request.method,
                        'api_key_prefix': api_key,
                        'client_ip': request.client.host if request.client else None,
                        'user_agent': request.headers.get('User-Agent'),
                        'body_size': len(body) if body else 0
                    }
                }
            )

        # Process request normally
        response = await call_next(request)
        return response
