"""
HAVEN Token Backend API
FastAPI application for managing token operations and integrations.
"""

import os
import logging
from datetime import datetime
from typing import Optional, List
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Depends, BackgroundTasks, Header, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from pydantic import BaseModel, EmailStr
from dotenv import load_dotenv
from apscheduler.schedulers.asyncio import AsyncIOScheduler

# Import services
from services.token_agent import token_agent
from services.aurora_integration import AuroraIntegrationService
from services.tribe_integration import TribeIntegrationService
from database.models import Base, User, Transaction, RedemptionRequest
from middleware.webhook_auth import verify_aurora_webhook, verify_tribe_webhook
from middleware.idempotency import IdempotencyMiddleware, require_idempotency_key

# Load environment
load_dotenv()

# Configure logging
logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO"),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Database setup
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:haven_dev@localhost:5432/haven")
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create tables
Base.metadata.create_all(bind=engine)

# Initialize services
aurora_service = AuroraIntegrationService(token_agent)
tribe_service = TribeIntegrationService(token_agent)

# Scheduler for background tasks
scheduler = AsyncIOScheduler()


# ─────────────────────────────────────────────────────────────────────────
# LIFESPAN CONTEXT (Startup/Shutdown)
# ─────────────────────────────────────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Handle startup and shutdown events."""
    # Startup
    logger.info("🚀 Starting HAVEN Token API...")

    # Schedule background jobs
    scheduler.add_job(
        sync_aurora_bookings_job,
        "cron",
        hour=2,  # Run at 2 AM daily
        id="aurora_sync"
    )

    scheduler.add_job(
        calculate_staking_rewards_job,
        "cron",
        day_of_week="mon",  # Run weekly on Monday
        hour=3,
        id="staking_rewards"
    )

    scheduler.add_job(
        sync_tribe_events_job,
        "cron",
        hour=4,  # Run at 4 AM daily
        id="tribe_event_sync"
    )

    scheduler.start()
    logger.info("✅ Scheduler started")

    yield

    # Shutdown
    logger.info("🛑 Shutting down HAVEN Token API...")
    scheduler.shutdown()


# ─────────────────────────────────────────────────────────────────────────
# FASTAPI APP
# ─────────────────────────────────────────────────────────────────────────

app = FastAPI(
    title="HAVEN Token API",
    description="Backend API for HAVEN Token ecosystem",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("ALLOWED_ORIGINS", "http://localhost:3000").split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ─────────────────────────────────────────────────────────────────────────
# DEPENDENCIES
# ─────────────────────────────────────────────────────────────────────────

def get_db():
    """Database dependency."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def verify_api_key(x_api_key: str = Header(...)):
    """Verify API key for protected endpoints."""
    expected_key = os.getenv("API_KEY", "test_key")
    if x_api_key != expected_key:
        raise HTTPException(status_code=401, detail="Invalid API key")
    return x_api_key


def verify_webhook_signature(signature: str, payload: dict, secret: str) -> bool:
    """Verify webhook signature."""
    import hmac
    import hashlib
    import json

    expected = hmac.new(
        secret.encode(),
        json.dumps(payload, sort_keys=True).encode(),
        hashlib.sha256
    ).hexdigest()

    return hmac.compare_digest(signature, expected)


# ─────────────────────────────────────────────────────────────────────────
# PYDANTIC MODELS
# ─────────────────────────────────────────────────────────────────────────

class MintRequest(BaseModel):
    user_id: str
    amount: float
    reason: str
    idempotency_key: Optional[str] = None


class RedeemRequest(BaseModel):
    user_id: str
    amount: float
    withdrawal_method: str  # "bank_transfer", "paypal", "crypto"
    withdrawal_address: Optional[str] = None
    idempotency_key: str


class UserResponse(BaseModel):
    user_id: str
    email: Optional[str]
    wallet_address: str
    balance: float
    total_earned: float
    total_redeemed: float
    kyc_verified: bool


class TransactionResponse(BaseModel):
    tx_id: str
    user_id: str
    tx_type: str
    amount: float
    status: str
    blockchain_tx: Optional[str]
    created_at: datetime
    confirmed_at: Optional[datetime]


class TokenStatsResponse(BaseModel):
    total_minted: float
    total_burned: float
    circulating_supply: float
    total_users: int
    total_transactions: int


# ─────────────────────────────────────────────────────────────────────────
# HEALTH & STATUS
# ─────────────────────────────────────────────────────────────────────────

@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "service": "HAVEN Token API",
        "version": "1.0.0",
        "status": "operational"
    }


@app.get("/health")
async def health_check(db: Session = Depends(get_db)):
    """Health check endpoint."""
    try:
        # Check database
        db.execute("SELECT 1")

        # Check blockchain connection
        supply = token_agent.get_total_supply()

        return {
            "status": "healthy",
            "database": "connected",
            "blockchain": "connected",
            "circulating_supply": supply
        }
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        return JSONResponse(
            status_code=503,
            content={
                "status": "unhealthy",
                "error": str(e)
            }
        )


# ─────────────────────────────────────────────────────────────────────────
# TOKEN OPERATIONS
# ─────────────────────────────────────────────────────────────────────────

@app.post("/token/mint")
async def mint_tokens(
    mint_request: MintRequest,
    background_tasks: BackgroundTasks,
    request: Request,
    db: Session = Depends(get_db),
    api_key: str = Depends(verify_api_key),
    idempotency_key: Optional[str] = Header(None, alias="Idempotency-Key")
):
    """
    Mint tokens to a user.
    Requires API key authentication.
    Supports optional idempotency via Idempotency-Key header.
    """
    try:
        # Use header idempotency key if provided, otherwise use request body key
        effective_key = idempotency_key or mint_request.idempotency_key

        # Check Redis cache for idempotent response
        if effective_key:
            cache_key = IdempotencyMiddleware.generate_key(effective_key, request.url.path)
            cached = IdempotencyMiddleware.get_cached_response(cache_key)
            if cached:
                return cached.get("body", cached)

        # Generate transaction ID
        tx_id = effective_key or f"mint_{mint_request.user_id}_{datetime.utcnow().timestamp()}"

        # Check database for duplicate
        existing = db.query(Transaction).filter(Transaction.tx_id == tx_id).first()
        if existing:
            result = {
                "status": "duplicate",
                "tx_id": tx_id,
                "message": "Transaction already processed"
            }
            # Cache the duplicate response
            if effective_key:
                IdempotencyMiddleware.store_response(cache_key, {"body": result, "status_code": 200})
            return result

        # Process mint in background
        background_tasks.add_task(
            token_agent.process_mint,
            tx_id=tx_id,
            user_id=mint_request.user_id,
            amount=mint_request.amount,
            reason=mint_request.reason,
            db=db
        )

        result = {
            "status": "queued",
            "tx_id": tx_id,
            "message": "Mint transaction queued"
        }

        # Cache the result
        if effective_key:
            IdempotencyMiddleware.store_response(cache_key, {"body": result, "status_code": 200})

        return result

    except Exception as e:
        logger.error(f"Mint error: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/token/redeem")
async def redeem_tokens(
    redeem_request: RedeemRequest,
    background_tasks: BackgroundTasks,
    http_request: Request,
    db: Session = Depends(get_db),
    api_key: str = Depends(verify_api_key),
    idempotency_key: Optional[str] = Header(None, alias="Idempotency-Key")
):
    """
    Redeem tokens for fiat payout.
    Burns tokens and initiates withdrawal.
    Requires idempotency key (header or body).
    """
    try:
        # Use header idempotency key if provided, otherwise use request body key
        effective_key = idempotency_key or redeem_request.idempotency_key

        if not effective_key:
            raise HTTPException(
                status_code=400,
                detail="Idempotency key is required for redemption (header or body)"
            )

        # Check Redis cache for idempotent response
        cache_key = IdempotencyMiddleware.generate_key(effective_key, http_request.url.path)
        cached = IdempotencyMiddleware.get_cached_response(cache_key)
        if cached:
            return cached.get("body", cached)

        # Check database for duplicate
        existing = db.query(RedemptionRequest).filter(
            RedemptionRequest.request_id == effective_key
        ).first()
        if existing:
            result = {
                "status": "duplicate",
                "request_id": effective_key
            }
            # Cache the duplicate response
            IdempotencyMiddleware.store_response(cache_key, {"body": result, "status_code": 200})
            return result

        # Get user
        user = db.query(User).filter(User.user_id == redeem_request.user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        # Check balance
        balance = token_agent.get_balance(user.wallet_address)
        if balance < redeem_request.amount:
            raise HTTPException(status_code=400, detail="Insufficient balance")

        # Create redemption request
        redemption = RedemptionRequest(
            request_id=effective_key,
            user_id=redeem_request.user_id,
            amount=redeem_request.amount,
            withdrawal_method=redeem_request.withdrawal_method,
            withdrawal_address=redeem_request.withdrawal_address,
            status="pending",
            created_at=datetime.utcnow()
        )
        db.add(redemption)
        db.commit()

        # Process burn (with 2% burn fee as per tokenomics)
        burn_amount = redeem_request.amount
        payout_amount = redeem_request.amount * 0.98  # 2% burn

        background_tasks.add_task(
            token_agent.process_burn,
            user_id=redeem_request.user_id,
            amount=burn_amount,
            reason=f"redemption_{effective_key}",
            db=db
        )

        result = {
            "status": "queued",
            "request_id": effective_key,
            "burn_amount": burn_amount,
            "payout_amount": payout_amount,
            "message": "Redemption queued"
        }

        # Cache the result
        IdempotencyMiddleware.store_response(cache_key, {"body": result, "status_code": 200})

        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Redeem error: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/token/balance/{user_id}")
async def get_user_balance(
    user_id: str,
    db: Session = Depends(get_db)
):
    """Get user's token balance."""
    try:
        user = db.query(User).filter(User.user_id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        balance = token_agent.get_balance(user.wallet_address)

        return {
            "user_id": user_id,
            "wallet_address": user.wallet_address,
            "balance": balance
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Balance query error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# ─────────────────────────────────────────────────────────────────────────
# AURORA WEBHOOKS
# ─────────────────────────────────────────────────────────────────────────

@app.post("/webhooks/aurora/booking-created")
async def aurora_booking_created(
    request: Request,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    verified: bool = Depends(verify_aurora_webhook)
):
    """Aurora webhook: new booking created."""
    try:
        payload = await request.json()

        background_tasks.add_task(
            aurora_service.on_booking_created,
            booking_data=payload,
            db=db
        )

        return {"status": "accepted"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Aurora webhook error: {str(e)}", exc_info=True)
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/webhooks/aurora/booking-completed")
async def aurora_booking_completed(
    request: Request,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    verified: bool = Depends(verify_aurora_webhook)
):
    """Aurora webhook: booking completed (check-out)."""
    try:
        payload = await request.json()

        background_tasks.add_task(
            aurora_service.on_booking_completed,
            booking_data=payload,
            db=db
        )

        return {"status": "accepted"}

    except Exception as e:
        logger.error(f"Aurora webhook error: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/webhooks/aurora/booking-cancelled")
async def aurora_booking_cancelled(
    request: Request,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    verified: bool = Depends(verify_aurora_webhook)
):
    """Aurora webhook: booking cancelled."""
    try:
        payload = await request.json()

        background_tasks.add_task(
            aurora_service.on_booking_cancelled,
            booking_data=payload,
            db=db
        )

        return {"status": "accepted"}

    except Exception as e:
        logger.error(f"Aurora webhook error: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/webhooks/aurora/review-submitted")
async def aurora_review_submitted(
    request: Request,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    verified: bool = Depends(verify_aurora_webhook)
):
    """Aurora webhook: guest review submitted."""
    try:
        payload = await request.json()

        background_tasks.add_task(
            aurora_service.on_review_submitted,
            review_data=payload,
            db=db
        )

        return {"status": "accepted"}

    except Exception as e:
        logger.error(f"Aurora webhook error: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))


# ─────────────────────────────────────────────────────────────────────────
# TRIBE WEBHOOKS
# ─────────────────────────────────────────────────────────────────────────

@app.post("/webhooks/tribe/event-attendance")
async def tribe_event_attendance(
    request: Request,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    verified: bool = Depends(verify_tribe_webhook)
):
    """Tribe webhook: event attendance."""
    try:
        payload = await request.json()

        background_tasks.add_task(
            tribe_service.on_event_attendance,
            event_data=payload,
            db=db
        )

        return {"status": "accepted"}

    except Exception as e:
        logger.error(f"Tribe webhook error: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/webhooks/tribe/contribution")
async def tribe_contribution(
    request: Request,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    verified: bool = Depends(verify_tribe_webhook)
):
    """Tribe webhook: community contribution."""
    try:
        payload = await request.json()

        background_tasks.add_task(
            tribe_service.on_contribution,
            contribution_data=payload,
            db=db
        )

        return {"status": "accepted"}

    except Exception as e:
        logger.error(f"Tribe webhook error: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/webhooks/tribe/staking-started")
async def tribe_staking_started(
    request: Request,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    verified: bool = Depends(verify_tribe_webhook)
):
    """Tribe webhook: staking initiated."""
    try:
        payload = await request.json()

        background_tasks.add_task(
            tribe_service.on_staking_started,
            stake_data=payload,
            db=db
        )

        return {"status": "accepted"}

    except Exception as e:
        logger.error(f"Tribe webhook error: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/webhooks/tribe/coaching-milestone")
async def tribe_coaching_milestone(
    request: Request,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    verified: bool = Depends(verify_tribe_webhook)
):
    """Tribe webhook: coaching milestone completed."""
    try:
        payload = await request.json()

        background_tasks.add_task(
            tribe_service.on_coaching_milestone,
            milestone_data=payload,
            db=db
        )

        return {"status": "accepted"}

    except Exception as e:
        logger.error(f"Tribe webhook error: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/webhooks/tribe/referral-success")
async def tribe_referral_success(
    request: Request,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    verified: bool = Depends(verify_tribe_webhook)
):
    """Tribe webhook: referral successful."""
    try:
        payload = await request.json()

        background_tasks.add_task(
            tribe_service.on_referral_success,
            referral_data=payload,
            db=db
        )

        return {"status": "accepted"}

    except Exception as e:
        logger.error(f"Tribe webhook error: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))


# ─────────────────────────────────────────────────────────────────────────
# ANALYTICS
# ─────────────────────────────────────────────────────────────────────────

@app.get("/analytics/user/{user_id}", response_model=UserResponse)
async def get_user_analytics(
    user_id: str,
    db: Session = Depends(get_db)
):
    """Get user analytics and statistics."""
    try:
        user = db.query(User).filter(User.user_id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        # Get on-chain balance
        balance = token_agent.get_balance(user.wallet_address)

        # Calculate total earned (all mint transactions)
        total_earned = db.query(Transaction).filter(
            Transaction.user_id == user_id,
            Transaction.tx_type == "mint",
            Transaction.status == "confirmed"
        ).count() * 1.0  # Simplified; should sum amounts

        # Calculate total redeemed
        total_redeemed = db.query(RedemptionRequest).filter(
            RedemptionRequest.user_id == user_id,
            RedemptionRequest.status == "completed"
        ).count() * 1.0  # Simplified

        return UserResponse(
            user_id=user.user_id,
            email=user.email,
            wallet_address=user.wallet_address,
            balance=balance,
            total_earned=total_earned,
            total_redeemed=total_redeemed,
            kyc_verified=user.kyc_verified
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Analytics error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/analytics/token-stats", response_model=TokenStatsResponse)
async def get_token_stats(db: Session = Depends(get_db)):
    """Get global token statistics."""
    try:
        # Get on-chain stats
        stats = token_agent.get_emission_stats()

        # Get database stats
        total_users = db.query(User).count()
        total_transactions = db.query(Transaction).count()

        return TokenStatsResponse(
            total_minted=stats["totalMinted"],
            total_burned=stats["totalBurned"],
            circulating_supply=stats["circulating"],
            total_users=total_users,
            total_transactions=total_transactions
        )

    except Exception as e:
        logger.error(f"Stats error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/analytics/transactions/{user_id}")
async def get_user_transactions(
    user_id: str,
    limit: int = 50,
    offset: int = 0,
    db: Session = Depends(get_db)
):
    """Get user transaction history."""
    try:
        transactions = db.query(Transaction).filter(
            Transaction.user_id == user_id
        ).order_by(
            Transaction.created_at.desc()
        ).limit(limit).offset(offset).all()

        return {
            "user_id": user_id,
            "count": len(transactions),
            "transactions": [
                TransactionResponse(
                    tx_id=tx.tx_id,
                    user_id=tx.user_id,
                    tx_type=tx.tx_type,
                    amount=tx.amount,
                    status=tx.status,
                    blockchain_tx=tx.blockchain_tx,
                    created_at=tx.created_at,
                    confirmed_at=tx.confirmed_at
                )
                for tx in transactions
            ]
        }

    except Exception as e:
        logger.error(f"Transaction query error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# ─────────────────────────────────────────────────────────────────────────
# BACKGROUND JOBS
# ─────────────────────────────────────────────────────────────────────────

async def sync_aurora_bookings_job():
    """Scheduled job: Sync Aurora bookings daily."""
    logger.info("🔄 Running scheduled Aurora sync...")
    db = SessionLocal()
    try:
        await aurora_service.sync_recent_bookings(db)
    except Exception as e:
        logger.error(f"Aurora sync job error: {str(e)}")
    finally:
        db.close()


async def calculate_staking_rewards_job():
    """Scheduled job: Calculate staking rewards weekly."""
    logger.info("💰 Running scheduled staking rewards calculation...")
    db = SessionLocal()
    try:
        await tribe_service.calculate_staking_rewards(db)
    except Exception as e:
        logger.error(f"Staking rewards job error: {str(e)}")
    finally:
        db.close()


async def sync_tribe_events_job():
    """Scheduled job: Sync Tribe events daily."""
    logger.info("🔄 Running scheduled Tribe event sync...")
    db = SessionLocal()
    try:
        await tribe_service.sync_recent_events(db)
    except Exception as e:
        logger.error(f"Tribe event sync job error: {str(e)}")
    finally:
        db.close()


# ─────────────────────────────────────────────────────────────────────────
# ERROR HANDLERS
# ─────────────────────────────────────────────────────────────────────────

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler."""
    logger.error(f"Unhandled exception: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "detail": "Internal server error",
            "message": str(exc) if os.getenv("ENVIRONMENT") == "development" else "An error occurred"
        }
    )


# ─────────────────────────────────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import uvicorn

    port = int(os.getenv("PORT", 8000))
    workers = int(os.getenv("WORKERS", 1))

    uvicorn.run(
        "app:app",
        host="0.0.0.0",
        port=port,
        workers=workers,
        reload=os.getenv("ENVIRONMENT") == "development"
    )
