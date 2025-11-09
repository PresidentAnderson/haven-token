"""
Global Error Handler Middleware
Handles exceptions globally and returns structured error responses.
"""

import logging
import traceback
import uuid
from datetime import datetime
from typing import Optional
from fastapi import Request, status
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from exceptions import (
    HAVENBaseException,
    ValidationError,
    AuthenticationError,
    AuthorizationError,
    BlockchainError,
    BusinessLogicError,
    SystemError,
    CircuitBreakerOpenError,
    UserNotFoundError,
    InsufficientBalanceError,
    DuplicateTransactionError
)

logger = logging.getLogger(__name__)


class ErrorContext:
    """Context information for error logging."""

    def __init__(
        self,
        request: Request,
        error_id: str,
        user_id: Optional[str] = None,
        request_id: Optional[str] = None
    ):
        self.request = request
        self.error_id = error_id
        self.user_id = user_id
        self.request_id = request_id or str(uuid.uuid4())
        self.timestamp = datetime.utcnow()
        self.path = request.url.path
        self.method = request.method
        self.client_ip = request.client.host if request.client else None


def log_error(exc: Exception, context: ErrorContext):
    """
    Log error with full context.

    Args:
        exc: Exception that occurred
        context: Error context information
    """
    error_details = {
        "error_id": context.error_id,
        "request_id": context.request_id,
        "user_id": context.user_id,
        "timestamp": context.timestamp.isoformat(),
        "path": context.path,
        "method": context.method,
        "client_ip": context.client_ip,
        "error_type": exc.__class__.__name__,
        "error_message": str(exc)
    }

    if isinstance(exc, HAVENBaseException):
        error_details.update({
            "error_code": exc.error_code,
            "details": exc.details
        })

    # Log with appropriate level based on error type
    if isinstance(exc, (ValidationError, DuplicateTransactionError)):
        # Expected errors - log at INFO level
        logger.info(f"Validation/Business error: {error_details}")
    elif isinstance(exc, (AuthenticationError, AuthorizationError)):
        # Auth errors - log at WARNING level
        logger.warning(f"Authentication/Authorization error: {error_details}")
    elif isinstance(exc, BusinessLogicError):
        # Business logic errors - log at WARNING level
        logger.warning(f"Business logic error: {error_details}")
    elif isinstance(exc, CircuitBreakerOpenError):
        # Circuit breaker - log at WARNING level
        logger.warning(f"Circuit breaker open: {error_details}")
    else:
        # System errors and unexpected exceptions - log at ERROR level with stack trace
        logger.error(
            f"System error: {error_details}\n"
            f"Stack trace:\n{traceback.format_exc()}"
        )


def save_error_to_database(exc: Exception, context: ErrorContext, db: Optional[Session] = None):
    """
    Save error to database for auditing.

    Args:
        exc: Exception that occurred
        context: Error context information
        db: Database session (optional)
    """
    if db is None:
        return

    try:
        # Import here to avoid circular dependency
        from database.models import Base, Column, Integer, String, DateTime, Text
        from sqlalchemy import create_engine
        import json

        # Create ErrorLog model if it doesn't exist
        # In production, this should be in models.py
        class ErrorLog(Base):
            __tablename__ = "error_logs"

            id = Column(Integer, primary_key=True, index=True)
            error_id = Column(String(100), unique=True, index=True)
            request_id = Column(String(100), index=True)
            user_id = Column(String(100), index=True, nullable=True)
            error_type = Column(String(100), index=True)
            error_code = Column(String(50), index=True, nullable=True)
            error_message = Column(Text)
            path = Column(String(255))
            method = Column(String(10))
            client_ip = Column(String(50))
            details = Column(Text, nullable=True)
            stack_trace = Column(Text, nullable=True)
            created_at = Column(DateTime, default=datetime.utcnow, index=True)

        # Save to database
        error_log = ErrorLog(
            error_id=context.error_id,
            request_id=context.request_id,
            user_id=context.user_id,
            error_type=exc.__class__.__name__,
            error_code=exc.error_code if isinstance(exc, HAVENBaseException) else None,
            error_message=str(exc),
            path=context.path,
            method=context.method,
            client_ip=context.client_ip,
            details=json.dumps(exc.details) if isinstance(exc, HAVENBaseException) else None,
            stack_trace=traceback.format_exc()
        )
        db.add(error_log)
        db.commit()

    except Exception as db_error:
        # Don't let database errors prevent error response
        logger.error(f"Failed to save error to database: {db_error}")


def get_http_status_code(exc: Exception) -> int:
    """
    Determine appropriate HTTP status code for exception.

    Args:
        exc: Exception

    Returns:
        HTTP status code
    """
    if isinstance(exc, ValidationError):
        return status.HTTP_400_BAD_REQUEST
    elif isinstance(exc, AuthenticationError):
        return status.HTTP_401_UNAUTHORIZED
    elif isinstance(exc, AuthorizationError):
        return status.HTTP_403_FORBIDDEN
    elif isinstance(exc, UserNotFoundError):
        return status.HTTP_404_NOT_FOUND
    elif isinstance(exc, DuplicateTransactionError):
        return status.HTTP_409_CONFLICT
    elif isinstance(exc, InsufficientBalanceError):
        return status.HTTP_400_BAD_REQUEST
    elif isinstance(exc, CircuitBreakerOpenError):
        return status.HTTP_503_SERVICE_UNAVAILABLE
    elif isinstance(exc, BusinessLogicError):
        return status.HTTP_400_BAD_REQUEST
    elif isinstance(exc, BlockchainError):
        return status.HTTP_502_BAD_GATEWAY
    elif isinstance(exc, SystemError):
        return status.HTTP_500_INTERNAL_SERVER_ERROR
    elif isinstance(exc, HAVENBaseException):
        return status.HTTP_500_INTERNAL_SERVER_ERROR
    else:
        return status.HTTP_500_INTERNAL_SERVER_ERROR


def create_error_response(exc: Exception, context: ErrorContext, include_stack_trace: bool = False) -> dict:
    """
    Create structured error response.

    Args:
        exc: Exception
        context: Error context
        include_stack_trace: Whether to include stack trace (dev mode only)

    Returns:
        Error response dictionary
    """
    if isinstance(exc, HAVENBaseException):
        response = {
            "error": exc.error_code,
            "message": exc.message,
            "user_message": exc.user_message,
            "error_id": context.error_id,
            "request_id": context.request_id,
            "timestamp": context.timestamp.isoformat()
        }

        # Include details if present
        if exc.details:
            response["details"] = exc.details

    else:
        # Generic error response for non-HAVEN exceptions
        response = {
            "error": "INTERNAL_ERROR",
            "message": "An unexpected error occurred",
            "user_message": "An error occurred. Please try again later.",
            "error_id": context.error_id,
            "request_id": context.request_id,
            "timestamp": context.timestamp.isoformat()
        }

    # Add stack trace in development mode
    if include_stack_trace:
        response["stack_trace"] = traceback.format_exc()

    return response


async def haven_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """
    Global exception handler for FastAPI.

    Args:
        request: FastAPI request object
        exc: Exception that occurred

    Returns:
        JSONResponse with error details
    """
    # Generate unique error ID
    error_id = str(uuid.uuid4())

    # Extract user_id from request if available
    user_id = None
    try:
        # Try to get user_id from various sources
        if hasattr(request.state, "user_id"):
            user_id = request.state.user_id
        elif "user_id" in request.path_params:
            user_id = request.path_params["user_id"]
    except:
        pass

    # Create error context
    context = ErrorContext(
        request=request,
        error_id=error_id,
        user_id=user_id
    )

    # Log error
    log_error(exc, context)

    # Get database session if available
    # In production, this should be injected properly
    db = None
    if hasattr(request.state, "db"):
        db = request.state.db

    # Save to database (async in background)
    try:
        save_error_to_database(exc, context, db)
    except:
        pass  # Don't let database save errors prevent response

    # Determine if we should include stack traces (dev mode only)
    import os
    include_stack_trace = os.getenv("ENVIRONMENT") == "development"

    # Create response
    response_data = create_error_response(exc, context, include_stack_trace)
    status_code = get_http_status_code(exc)

    return JSONResponse(
        status_code=status_code,
        content=response_data
    )


# Specific exception handlers for common FastAPI exceptions

async def validation_exception_handler(request: Request, exc) -> JSONResponse:
    """Handler for Pydantic validation errors."""
    error_id = str(uuid.uuid4())
    context = ErrorContext(request=request, error_id=error_id)

    # Convert Pydantic validation error to our format
    validation_error = ValidationError(
        message="Request validation failed",
        details={"validation_errors": exc.errors()}
    )

    log_error(validation_error, context)

    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=create_error_response(validation_error, context)
    )


async def http_exception_handler(request: Request, exc) -> JSONResponse:
    """Handler for FastAPI HTTPException."""
    error_id = str(uuid.uuid4())
    context = ErrorContext(request=request, error_id=error_id)

    # Map HTTP exception to our error structure
    response_data = {
        "error": f"HTTP_{exc.status_code}",
        "message": exc.detail,
        "user_message": exc.detail,
        "error_id": error_id,
        "request_id": context.request_id,
        "timestamp": context.timestamp.isoformat()
    }

    # Log only if it's a server error
    if exc.status_code >= 500:
        logger.error(f"HTTP {exc.status_code} error: {exc.detail}")

    return JSONResponse(
        status_code=exc.status_code,
        content=response_data
    )
