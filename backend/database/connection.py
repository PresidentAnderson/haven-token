"""
Database Connection Pool Configuration

Provides optimized connection pooling for PostgreSQL with health checks,
monitoring, and automatic reconnection.
"""

import os
import logging
from typing import Generator
from contextlib import contextmanager
from sqlalchemy import create_engine, event, pool
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import QueuePool, NullPool
from sqlalchemy.exc import OperationalError, DisconnectionError
import time

logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────────────────────────────────
# POOL CONFIGURATION
# ─────────────────────────────────────────────────────────────────────────

def get_pool_config() -> dict:
    """
    Get connection pool configuration from environment.

    Configuration:
    - pool_size: Number of connections to keep open (default: 10)
    - max_overflow: Additional connections when pool is full (default: 20)
    - pool_timeout: Seconds to wait for connection (default: 30)
    - pool_recycle: Recycle connections after N seconds (default: 3600)
    - pool_pre_ping: Test connections before use (default: True)

    Environment Variables:
        DB_POOL_SIZE: Pool size (default: 10)
        DB_MAX_OVERFLOW: Max overflow (default: 20)
        DB_POOL_TIMEOUT: Pool timeout in seconds (default: 30)
        DB_POOL_RECYCLE: Pool recycle time in seconds (default: 3600)
        DB_POOL_PRE_PING: Enable pre-ping (default: true)
        ENVIRONMENT: Runtime environment (production/development)

    Returns:
        Dictionary of pool configuration parameters
    """
    environment = os.getenv("ENVIRONMENT", "development")

    # Production settings
    if environment == "production":
        return {
            "poolclass": QueuePool,
            "pool_size": int(os.getenv("DB_POOL_SIZE", "10")),
            "max_overflow": int(os.getenv("DB_MAX_OVERFLOW", "20")),
            "pool_timeout": int(os.getenv("DB_POOL_TIMEOUT", "30")),
            "pool_recycle": int(os.getenv("DB_POOL_RECYCLE", "3600")),
            "pool_pre_ping": os.getenv("DB_POOL_PRE_PING", "true").lower() == "true",
            "echo": False,
            "echo_pool": os.getenv("DB_ECHO_POOL", "false").lower() == "true",
        }
    # Development settings (more lenient)
    else:
        return {
            "poolclass": QueuePool,
            "pool_size": int(os.getenv("DB_POOL_SIZE", "5")),
            "max_overflow": int(os.getenv("DB_MAX_OVERFLOW", "10")),
            "pool_timeout": int(os.getenv("DB_POOL_TIMEOUT", "30")),
            "pool_recycle": int(os.getenv("DB_POOL_RECYCLE", "1800")),
            "pool_pre_ping": True,
            "echo": os.getenv("DB_ECHO", "false").lower() == "true",
            "echo_pool": os.getenv("DB_ECHO_POOL", "false").lower() == "true",
        }


# ─────────────────────────────────────────────────────────────────────────
# ENGINE CREATION
# ─────────────────────────────────────────────────────────────────────────

def create_db_engine():
    """
    Create SQLAlchemy engine with connection pooling.

    Features:
    - Connection pooling with configurable size
    - Automatic connection health checks (pre-ping)
    - Connection recycling to prevent stale connections
    - Event listeners for monitoring
    - Error handling and logging

    Returns:
        Configured SQLAlchemy Engine instance
    """
    database_url = os.getenv("DATABASE_URL", "postgresql://postgres:haven_dev@localhost:5432/haven")

    # Get pool configuration
    pool_config = get_pool_config()

    logger.info(
        f"Creating database engine with pool_size={pool_config['pool_size']}, "
        f"max_overflow={pool_config['max_overflow']}, "
        f"pool_pre_ping={pool_config['pool_pre_ping']}"
    )

    # Create engine with pooling
    engine = create_engine(
        database_url,
        **pool_config
    )

    # Add event listeners for monitoring
    _add_event_listeners(engine)

    # Test connection
    _test_connection(engine)

    logger.info("✅ Database engine created successfully")
    return engine


def _add_event_listeners(engine):
    """Add event listeners for connection monitoring and debugging."""

    @event.listens_for(engine, "connect")
    def receive_connect(dbapi_conn, connection_record):
        """Log when new connection is created."""
        logger.debug(f"Database connection established: {id(dbapi_conn)}")

    @event.listens_for(engine, "checkout")
    def receive_checkout(dbapi_conn, connection_record, connection_proxy):
        """Log when connection is checked out from pool."""
        logger.debug(f"Connection checked out from pool: {id(dbapi_conn)}")

    @event.listens_for(engine, "checkin")
    def receive_checkin(dbapi_conn, connection_record):
        """Log when connection is returned to pool."""
        logger.debug(f"Connection returned to pool: {id(dbapi_conn)}")

    @event.listens_for(engine, "close")
    def receive_close(dbapi_conn, connection_record):
        """Log when connection is closed."""
        logger.info(f"Database connection closed: {id(dbapi_conn)}")

    @event.listens_for(engine, "close_detached")
    def receive_close_detached(dbapi_conn):
        """Log when detached connection is closed."""
        logger.info(f"Detached connection closed: {id(dbapi_conn)}")

    @event.listens_for(engine, "handle_error")
    def receive_handle_error(exception_context):
        """Log database errors."""
        logger.error(
            f"Database error: {exception_context.original_exception}",
            exc_info=True
        )


def _test_connection(engine):
    """Test database connection on startup."""
    max_retries = 3
    retry_delay = 2

    for attempt in range(max_retries):
        try:
            with engine.connect() as conn:
                conn.execute("SELECT 1")
            logger.info("Database connection test successful")
            return
        except (OperationalError, DisconnectionError) as e:
            logger.warning(f"Connection test attempt {attempt + 1} failed: {str(e)}")
            if attempt < max_retries - 1:
                time.sleep(retry_delay)
            else:
                logger.error("Failed to connect to database after multiple attempts")
                raise


# ─────────────────────────────────────────────────────────────────────────
# SESSION MANAGEMENT
# ─────────────────────────────────────────────────────────────────────────

# Global engine and session factory (initialized once)
_engine = None
_SessionLocal = None


def get_engine():
    """Get or create the global database engine."""
    global _engine
    if _engine is None:
        _engine = create_db_engine()
    return _engine


def get_session_factory():
    """Get or create the global session factory."""
    global _SessionLocal
    if _SessionLocal is None:
        engine = get_engine()
        _SessionLocal = sessionmaker(
            autocommit=False,
            autoflush=False,
            bind=engine
        )
    return _SessionLocal


def get_db() -> Generator[Session, None, None]:
    """
    Dependency function for FastAPI to get database session.

    Yields database session and ensures proper cleanup.
    Handles errors gracefully and logs issues.

    Usage in FastAPI:
        @app.get("/users")
        def get_users(db: Session = Depends(get_db)):
            return db.query(User).all()

    Yields:
        Database session instance
    """
    SessionLocal = get_session_factory()
    db = SessionLocal()
    try:
        yield db
    except Exception as e:
        logger.error(f"Database session error: {str(e)}", exc_info=True)
        db.rollback()
        raise
    finally:
        db.close()


@contextmanager
def get_db_context():
    """
    Context manager for database sessions outside of FastAPI.

    Usage:
        with get_db_context() as db:
            users = db.query(User).all()

    Yields:
        Database session instance
    """
    SessionLocal = get_session_factory()
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception as e:
        logger.error(f"Database context error: {str(e)}", exc_info=True)
        db.rollback()
        raise
    finally:
        db.close()


# ─────────────────────────────────────────────────────────────────────────
# POOL MONITORING
# ─────────────────────────────────────────────────────────────────────────

def get_pool_status() -> dict:
    """
    Get current connection pool statistics.

    Returns dictionary with pool metrics for monitoring.

    Returns:
        Dictionary containing:
        - pool_size: Configured pool size
        - checked_in: Connections currently in pool
        - checked_out: Connections currently in use
        - overflow: Overflow connections created
        - total_connections: Total connections (pool + overflow)
        - max_overflow: Maximum overflow allowed
    """
    engine = get_engine()

    if not isinstance(engine.pool, QueuePool):
        return {
            "pool_type": type(engine.pool).__name__,
            "message": "Pool statistics not available for this pool type"
        }

    pool = engine.pool

    return {
        "pool_size": pool.size(),
        "checked_in": pool.checkedin(),
        "checked_out": pool.checkedout(),
        "overflow": pool.overflow(),
        "total_connections": pool.checkedin() + pool.checkedout(),
        "max_overflow": pool._max_overflow,
        "pool_timeout": pool._timeout,
        "pool_recycle": pool._recycle,
    }


def log_pool_status():
    """Log current pool status for monitoring."""
    status = get_pool_status()
    logger.info(f"Connection pool status: {status}")


# ─────────────────────────────────────────────────────────────────────────
# CLEANUP
# ─────────────────────────────────────────────────────────────────────────

def dispose_engine():
    """
    Dispose of the database engine and close all connections.

    Should be called on application shutdown.
    """
    global _engine, _SessionLocal

    if _engine is not None:
        logger.info("Disposing database engine and closing all connections")
        _engine.dispose()
        _engine = None
        _SessionLocal = None
        logger.info("✅ Database engine disposed")


# ─────────────────────────────────────────────────────────────────────────
# HEALTH CHECK
# ─────────────────────────────────────────────────────────────────────────

def check_database_health() -> tuple[bool, str]:
    """
    Check database connectivity and pool health.

    Returns:
        Tuple of (is_healthy: bool, message: str)
    """
    try:
        engine = get_engine()

        # Test connection
        with engine.connect() as conn:
            conn.execute("SELECT 1")

        # Check pool status
        pool_status = get_pool_status()

        # Warning if pool is at capacity
        if pool_status.get("checked_out", 0) >= pool_status.get("pool_size", 0):
            return True, "Database healthy but pool at capacity"

        return True, "Database healthy"

    except Exception as e:
        logger.error(f"Database health check failed: {str(e)}", exc_info=True)
        return False, f"Database unhealthy: {str(e)}"


# ─────────────────────────────────────────────────────────────────────────
# INITIALIZATION
# ─────────────────────────────────────────────────────────────────────────

def init_database():
    """
    Initialize database and create tables.

    Should be called on application startup.
    """
    from database.models import Base

    engine = get_engine()

    logger.info("Creating database tables if they don't exist...")
    Base.metadata.create_all(bind=engine)
    logger.info("✅ Database tables created/verified")


# Example usage
if __name__ == "__main__":
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )

    # Initialize database
    init_database()

    # Test connection
    with get_db_context() as db:
        result = db.execute("SELECT version()")
        version = result.fetchone()[0]
        print(f"PostgreSQL version: {version}")

    # Check pool status
    status = get_pool_status()
    print(f"Pool status: {status}")

    # Health check
    is_healthy, message = check_database_health()
    print(f"Health check: {is_healthy} - {message}")

    # Cleanup
    dispose_engine()
