"""
Configuration and Environment Variable Validation
Uses Pydantic Settings for type-safe configuration management.
"""

import os
from typing import Optional, List
from pydantic import BaseModel, Field, validator, PostgresDsn, RedisDsn, HttpUrl
from pydantic_settings import BaseSettings
import logging

logger = logging.getLogger(__name__)


class BlockchainConfig(BaseModel):
    """Blockchain-specific configuration."""

    rpc_url: str = Field(
        ...,
        description="RPC URL for blockchain connection (Alchemy, Infura, etc.)"
    )
    contract_address: str = Field(
        ...,
        description="HAVEN token contract address",
        min_length=42,
        max_length=42
    )
    backend_private_key: str = Field(
        ...,
        description="Private key for backend wallet (manages minting/burning)",
        min_length=64
    )
    chain_id: int = Field(
        84532,
        description="Chain ID (84532 for Base Sepolia, 8453 for Base Mainnet)"
    )

    @validator("contract_address")
    def validate_contract_address(cls, v):
        """Validate Ethereum address format."""
        if not v.startswith("0x"):
            raise ValueError("Contract address must start with '0x'")
        if len(v) != 42:
            raise ValueError("Contract address must be 42 characters (0x + 40 hex chars)")
        try:
            int(v[2:], 16)
        except ValueError:
            raise ValueError("Contract address must be valid hexadecimal")
        return v.lower()

    @validator("backend_private_key")
    def validate_private_key(cls, v):
        """Validate private key format."""
        clean_key = v.replace("0x", "")
        if len(clean_key) != 64:
            raise ValueError("Private key must be 64 hexadecimal characters (optionally prefixed with 0x)")
        try:
            int(clean_key, 16)
        except ValueError:
            raise ValueError("Private key must be valid hexadecimal")
        # Ensure it has 0x prefix for consistency
        return f"0x{clean_key}" if not v.startswith("0x") else v

    @validator("chain_id")
    def validate_chain_id(cls, v):
        """Validate chain ID is a known network."""
        known_chains = {
            1: "Ethereum Mainnet",
            5: "Goerli Testnet",
            8453: "Base Mainnet",
            84532: "Base Sepolia Testnet",
            11155111: "Sepolia Testnet"
        }
        if v not in known_chains:
            logger.warning(
                f"Chain ID {v} is not a recognized network. "
                f"Known chains: {known_chains}"
            )
        return v


class DatabaseConfig(BaseModel):
    """Database configuration."""

    database_url: str = Field(
        ...,
        description="PostgreSQL database connection URL"
    )

    @validator("database_url")
    def validate_database_url(cls, v):
        """Validate database URL format."""
        if not v.startswith("postgresql://") and not v.startswith("postgres://"):
            raise ValueError(
                "Database URL must start with 'postgresql://' or 'postgres://'"
            )
        return v


class RedisConfig(BaseModel):
    """Redis cache configuration."""

    redis_url: str = Field(
        "redis://localhost:6379/0",
        description="Redis connection URL for caching and rate limiting"
    )

    @validator("redis_url")
    def validate_redis_url(cls, v):
        """Validate Redis URL format."""
        if not v.startswith("redis://") and not v.startswith("memory://"):
            raise ValueError(
                "Redis URL must start with 'redis://' (or 'memory://' for in-memory storage)"
            )
        return v


class ExternalAPIConfig(BaseModel):
    """External API integration configuration."""

    aurora_api_url: Optional[str] = Field(
        None,
        description="Aurora PMS API base URL"
    )
    aurora_api_key: Optional[str] = Field(
        None,
        description="Aurora PMS API key"
    )
    aurora_webhook_secret: Optional[str] = Field(
        None,
        description="Secret for verifying Aurora webhooks"
    )

    tribe_api_url: Optional[str] = Field(
        None,
        description="Tribe App API base URL"
    )
    tribe_api_key: Optional[str] = Field(
        None,
        description="Tribe App API key"
    )
    tribe_webhook_secret: Optional[str] = Field(
        None,
        description="Secret for verifying Tribe webhooks"
    )

    stripe_secret_key: Optional[str] = Field(
        None,
        description="Stripe secret key for payment processing"
    )
    stripe_webhook_secret: Optional[str] = Field(
        None,
        description="Stripe webhook signing secret"
    )


class MonitoringConfig(BaseModel):
    """Monitoring and alerting configuration."""

    slack_bot_token: Optional[str] = Field(
        None,
        description="Slack bot token for alerts"
    )
    slack_alert_channel: Optional[str] = Field(
        None,
        description="Slack channel for alerts (e.g., #haven-alerts)"
    )
    sentry_dsn: Optional[str] = Field(
        None,
        description="Sentry DSN for error tracking"
    )


class ApplicationConfig(BaseModel):
    """General application configuration."""

    environment: str = Field(
        "development",
        description="Environment: development, staging, production"
    )
    port: int = Field(
        8000,
        description="API server port",
        ge=1,
        le=65535
    )
    workers: int = Field(
        1,
        description="Number of worker processes",
        ge=1,
        le=32
    )
    log_level: str = Field(
        "INFO",
        description="Logging level: DEBUG, INFO, WARNING, ERROR, CRITICAL"
    )
    api_key: str = Field(
        ...,
        description="API key for authenticating requests",
        min_length=16
    )
    allowed_origins: List[str] = Field(
        default_factory=lambda: ["http://localhost:3000"],
        description="CORS allowed origins (comma-separated)"
    )

    @validator("environment")
    def validate_environment(cls, v):
        """Validate environment is a known type."""
        valid_envs = ["development", "staging", "production", "test"]
        if v.lower() not in valid_envs:
            raise ValueError(
                f"Environment must be one of: {', '.join(valid_envs)}. Got: {v}"
            )
        return v.lower()

    @validator("log_level")
    def validate_log_level(cls, v):
        """Validate log level."""
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if v.upper() not in valid_levels:
            raise ValueError(
                f"Log level must be one of: {', '.join(valid_levels)}. Got: {v}"
            )
        return v.upper()

    @validator("allowed_origins", pre=True)
    def parse_allowed_origins(cls, v):
        """Parse comma-separated origins string."""
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",")]
        return v


class Settings(BaseSettings):
    """
    Complete application settings.

    Validates all required environment variables on startup.
    """

    # Blockchain settings
    blockchain: BlockchainConfig

    # Database settings
    database: DatabaseConfig

    # Redis cache settings
    redis: RedisConfig = RedisConfig()

    # External API integrations
    external_apis: ExternalAPIConfig = ExternalAPIConfig()

    # Monitoring
    monitoring: MonitoringConfig = MonitoringConfig()

    # Application settings
    app: ApplicationConfig

    class Config:
        env_nested_delimiter = "__"
        case_sensitive = False

    @classmethod
    def from_env(cls) -> "Settings":
        """
        Load settings from environment variables.

        Raises:
            ValidationError: If required variables are missing or invalid

        Returns:
            Validated Settings instance
        """
        try:
            # Build nested config from flat environment variables
            config = {
                "blockchain": {
                    "rpc_url": os.getenv("RPC_URL"),
                    "contract_address": os.getenv("HAVEN_CONTRACT_ADDRESS"),
                    "backend_private_key": os.getenv("BACKEND_PRIVATE_KEY"),
                    "chain_id": int(os.getenv("CHAIN_ID", "84532")),
                },
                "database": {
                    "database_url": os.getenv("DATABASE_URL"),
                },
                "redis": {
                    "redis_url": os.getenv("REDIS_URL", "redis://localhost:6379/0"),
                },
                "external_apis": {
                    "aurora_api_url": os.getenv("AURORA_API_URL"),
                    "aurora_api_key": os.getenv("AURORA_API_KEY"),
                    "aurora_webhook_secret": os.getenv("AURORA_WEBHOOK_SECRET"),
                    "tribe_api_url": os.getenv("TRIBE_API_URL"),
                    "tribe_api_key": os.getenv("TRIBE_API_KEY"),
                    "tribe_webhook_secret": os.getenv("TRIBE_WEBHOOK_SECRET"),
                    "stripe_secret_key": os.getenv("STRIPE_SECRET_KEY"),
                    "stripe_webhook_secret": os.getenv("STRIPE_WEBHOOK_SECRET"),
                },
                "monitoring": {
                    "slack_bot_token": os.getenv("SLACK_BOT_TOKEN"),
                    "slack_alert_channel": os.getenv("SLACK_ALERT_CHANNEL"),
                    "sentry_dsn": os.getenv("SENTRY_DSN"),
                },
                "app": {
                    "environment": os.getenv("ENVIRONMENT", "development"),
                    "port": int(os.getenv("PORT", "8000")),
                    "workers": int(os.getenv("WORKERS", "1")),
                    "log_level": os.getenv("LOG_LEVEL", "INFO"),
                    "api_key": os.getenv("API_KEY"),
                    "allowed_origins": os.getenv(
                        "ALLOWED_ORIGINS",
                        "http://localhost:3000"
                    ),
                },
            }

            settings = cls(**config)
            logger.info("Configuration loaded and validated successfully")
            return settings

        except Exception as e:
            logger.error(f"Configuration validation failed: {str(e)}")
            raise


def validate_configuration() -> Settings:
    """
    Validate configuration on application startup.

    This function should be called during app initialization to ensure
    all required environment variables are present and valid.

    Returns:
        Validated Settings instance

    Raises:
        SystemExit: If configuration is invalid (exits with code 1)
    """
    try:
        settings = Settings.from_env()

        # Log configuration summary (without sensitive values)
        logger.info("=" * 60)
        logger.info("HAVEN Token API - Configuration Summary")
        logger.info("=" * 60)
        logger.info(f"Environment: {settings.app.environment}")
        logger.info(f"Port: {settings.app.port}")
        logger.info(f"Workers: {settings.app.workers}")
        logger.info(f"Log Level: {settings.app.log_level}")
        logger.info(f"Chain ID: {settings.blockchain.chain_id}")
        logger.info(f"Contract: {settings.blockchain.contract_address}")
        logger.info(f"Database: {settings.database.database_url.split('@')[-1]}")  # Hide credentials
        logger.info(f"Redis: {settings.redis.redis_url.split('@')[-1] if '@' in settings.redis.redis_url else settings.redis.redis_url}")
        logger.info(f"CORS Origins: {', '.join(settings.app.allowed_origins)}")

        # Optional integrations
        if settings.external_apis.aurora_api_url:
            logger.info(f"Aurora Integration: Enabled")
        if settings.external_apis.tribe_api_url:
            logger.info(f"Tribe Integration: Enabled")
        if settings.external_apis.stripe_secret_key:
            logger.info(f"Stripe Integration: Enabled")

        # Monitoring
        if settings.monitoring.sentry_dsn:
            logger.info(f"Sentry Monitoring: Enabled")
        if settings.monitoring.slack_bot_token:
            logger.info(f"Slack Alerts: Enabled ({settings.monitoring.slack_alert_channel})")

        logger.info("=" * 60)

        return settings

    except Exception as e:
        logger.critical("=" * 60)
        logger.critical("CONFIGURATION ERROR - Application cannot start")
        logger.critical("=" * 60)
        logger.critical(f"Error: {str(e)}")
        logger.critical("")
        logger.critical("Please check your .env file and ensure all required")
        logger.critical("environment variables are set correctly:")
        logger.critical("")
        logger.critical("Required variables:")
        logger.critical("  - RPC_URL")
        logger.critical("  - HAVEN_CONTRACT_ADDRESS")
        logger.critical("  - BACKEND_PRIVATE_KEY")
        logger.critical("  - DATABASE_URL")
        logger.critical("  - API_KEY")
        logger.critical("")
        logger.critical("Optional variables:")
        logger.critical("  - CHAIN_ID (default: 84532)")
        logger.critical("  - REDIS_URL (default: redis://localhost:6379/0)")
        logger.critical("  - ENVIRONMENT (default: development)")
        logger.critical("  - PORT (default: 8000)")
        logger.critical("  - LOG_LEVEL (default: INFO)")
        logger.critical("")
        logger.critical("See .env.example for a complete list of variables")
        logger.critical("=" * 60)

        raise SystemExit(1)


# Singleton instance (loaded on import)
# Note: In production, you may want to load this lazily
_settings: Optional[Settings] = None


def get_settings() -> Settings:
    """
    Get the validated settings instance.

    Returns:
        Settings instance
    """
    global _settings
    if _settings is None:
        _settings = validate_configuration()
    return _settings
