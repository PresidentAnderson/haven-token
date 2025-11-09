"""
Admin API Endpoints
Administrative endpoints for wallet management, monitoring, and system operations.
"""

import logging
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Header, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from exceptions import (
    AuthorizationError,
    WalletCustodyError,
    InvalidParameterError
)
from services.wallet_custody import get_wallet_custody_service
from middleware.circuit_breaker import get_all_statuses as get_circuit_breaker_statuses

logger = logging.getLogger(__name__)

# Create admin router
router = APIRouter(prefix="/api/v1/admin", tags=["admin"])


# ============================================================================
# AUTHENTICATION & AUTHORIZATION
# ============================================================================

def verify_admin_key(x_admin_key: str = Header(...)) -> str:
    """
    Verify admin API key.

    Args:
        x_admin_key: Admin API key from header

    Returns:
        API key if valid

    Raises:
        HTTPException: If API key is invalid
    """
    import os
    expected_key = os.getenv("ADMIN_API_KEY")

    if not expected_key:
        raise HTTPException(
            status_code=500,
            detail="Admin API key not configured"
        )

    if x_admin_key != expected_key:
        logger.warning(f"Invalid admin API key attempt from header")
        raise HTTPException(
            status_code=401,
            detail="Invalid admin API key"
        )

    return x_admin_key


# ============================================================================
# PYDANTIC MODELS
# ============================================================================

class CreateWalletRequest(BaseModel):
    wallet_id: str
    metadata: Optional[dict] = None


class WalletResponse(BaseModel):
    wallet_id: str
    address: str
    status: str
    created_at: str
    last_used_at: Optional[str] = None
    metadata: Optional[dict] = None


class RotateWalletRequest(BaseModel):
    wallet_id: str


class RevokeWalletRequest(BaseModel):
    wallet_id: str
    reason: str


class TransactionStatusResponse(BaseModel):
    total_pending: int
    total_failed: int
    pending_transactions: list
    failed_transactions: list


# ============================================================================
# WALLET MANAGEMENT ENDPOINTS
# ============================================================================

@router.post("/wallets", response_model=WalletResponse)
async def create_wallet(
    request: CreateWalletRequest,
    admin_key: str = Depends(verify_admin_key)
):
    """
    Create a new custodial wallet.

    Requires admin authentication.

    Args:
        request: Wallet creation request
        admin_key: Admin API key

    Returns:
        Created wallet information
    """
    try:
        custody_service = get_wallet_custody_service()
        wallet = custody_service.create_wallet(
            wallet_id=request.wallet_id,
            metadata=request.metadata
        )

        logger.info(f"Admin created wallet: {request.wallet_id}")

        return WalletResponse(**wallet)

    except WalletCustodyError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error creating wallet: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to create wallet")


@router.get("/wallets/{wallet_id}", response_model=WalletResponse)
async def get_wallet(
    wallet_id: str,
    include_private_key: bool = Query(False, description="Include private key in response (use with caution)"),
    admin_key: str = Depends(verify_admin_key)
):
    """
    Get wallet information.

    Requires admin authentication.

    Args:
        wallet_id: Wallet identifier
        include_private_key: Whether to include decrypted private key (WARNING: sensitive)
        admin_key: Admin API key

    Returns:
        Wallet information
    """
    try:
        custody_service = get_wallet_custody_service()
        wallet = custody_service.get_wallet(
            wallet_id=wallet_id,
            include_private_key=include_private_key
        )

        if include_private_key:
            logger.warning(f"Admin accessed private key for wallet: {wallet_id}")

        return wallet

    except WalletCustodyError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error retrieving wallet: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to retrieve wallet")


@router.get("/wallets", response_model=list[WalletResponse])
async def list_wallets(
    status: Optional[str] = Query(None, description="Filter by status (active, rotated, revoked)"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of results"),
    offset: int = Query(0, ge=0, description="Offset for pagination"),
    admin_key: str = Depends(verify_admin_key)
):
    """
    List all wallets in custody.

    Requires admin authentication.

    Args:
        status: Filter by status
        limit: Maximum number of results
        offset: Offset for pagination
        admin_key: Admin API key

    Returns:
        List of wallet information
    """
    try:
        custody_service = get_wallet_custody_service()
        wallets = custody_service.list_wallets(
            status=status,
            limit=limit,
            offset=offset
        )

        return wallets

    except Exception as e:
        logger.error(f"Error listing wallets: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to list wallets")


@router.post("/wallets/{wallet_id}/rotate", response_model=WalletResponse)
async def rotate_wallet(
    wallet_id: str,
    admin_key: str = Depends(verify_admin_key)
):
    """
    Rotate wallet by creating a new wallet and marking the old one as rotated.

    Requires admin authentication.

    Args:
        wallet_id: Wallet identifier to rotate
        admin_key: Admin API key

    Returns:
        New wallet information
    """
    try:
        custody_service = get_wallet_custody_service()
        new_wallet = custody_service.rotate_wallet(wallet_id)

        logger.warning(f"Admin rotated wallet: {wallet_id}")

        return WalletResponse(**new_wallet)

    except WalletCustodyError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error rotating wallet: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to rotate wallet")


@router.post("/wallets/{wallet_id}/revoke")
async def revoke_wallet(
    wallet_id: str,
    request: RevokeWalletRequest,
    admin_key: str = Depends(verify_admin_key)
):
    """
    Revoke a wallet (mark as inactive).

    Requires admin authentication.

    Args:
        wallet_id: Wallet identifier to revoke
        request: Revocation request with reason
        admin_key: Admin API key

    Returns:
        Success response
    """
    try:
        custody_service = get_wallet_custody_service()
        custody_service.revoke_wallet(wallet_id, request.reason)

        logger.warning(f"Admin revoked wallet: {wallet_id}, reason: {request.reason}")

        return {
            "status": "success",
            "message": f"Wallet {wallet_id} revoked",
            "reason": request.reason
        }

    except WalletCustodyError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error revoking wallet: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to revoke wallet")


# ============================================================================
# TRANSACTION MONITORING ENDPOINTS
# ============================================================================

@router.get("/transactions/status", response_model=TransactionStatusResponse)
async def get_transaction_status(
    admin_key: str = Depends(verify_admin_key),
    db: Session = Depends(lambda: None)  # Will be injected by app
):
    """
    Get transaction monitoring status.

    Shows pending and failed transactions for monitoring dashboard.

    Requires admin authentication.

    Args:
        admin_key: Admin API key
        db: Database session

    Returns:
        Transaction status information
    """
    try:
        from database.models import Transaction
        from datetime import datetime, timedelta

        if db is None:
            raise HTTPException(status_code=500, detail="Database not available")

        # Get pending transactions older than 5 minutes
        five_minutes_ago = datetime.utcnow() - timedelta(minutes=5)
        pending_txs = db.query(Transaction).filter(
            Transaction.status == "pending",
            Transaction.created_at < five_minutes_ago
        ).order_by(Transaction.created_at.asc()).limit(100).all()

        # Get failed transactions from last 24 hours
        yesterday = datetime.utcnow() - timedelta(hours=24)
        failed_txs = db.query(Transaction).filter(
            Transaction.status == "failed",
            Transaction.created_at > yesterday
        ).order_by(Transaction.created_at.desc()).limit(100).all()

        return TransactionStatusResponse(
            total_pending=len(pending_txs),
            total_failed=len(failed_txs),
            pending_transactions=[
                {
                    "tx_id": tx.tx_id,
                    "user_id": tx.user_id,
                    "tx_type": tx.tx_type,
                    "amount": tx.amount,
                    "created_at": tx.created_at.isoformat(),
                    "blockchain_tx": tx.blockchain_tx
                }
                for tx in pending_txs
            ],
            failed_transactions=[
                {
                    "tx_id": tx.tx_id,
                    "user_id": tx.user_id,
                    "tx_type": tx.tx_type,
                    "amount": tx.amount,
                    "created_at": tx.created_at.isoformat(),
                    "reason": tx.reason,
                    "blockchain_tx": tx.blockchain_tx
                }
                for tx in failed_txs
            ]
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting transaction status: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to get transaction status")


@router.post("/transactions/{tx_id}/retry")
async def retry_transaction(
    tx_id: str,
    admin_key: str = Depends(verify_admin_key),
    db: Session = Depends(lambda: None)
):
    """
    Retry a failed transaction.

    Requires admin authentication.

    Args:
        tx_id: Transaction ID to retry
        admin_key: Admin API key
        db: Database session

    Returns:
        Success response
    """
    try:
        from database.models import Transaction

        if db is None:
            raise HTTPException(status_code=500, detail="Database not available")

        # Get transaction
        tx = db.query(Transaction).filter(Transaction.tx_id == tx_id).first()
        if not tx:
            raise HTTPException(status_code=404, detail="Transaction not found")

        if tx.status != "failed":
            raise HTTPException(status_code=400, detail="Only failed transactions can be retried")

        # Reset transaction status
        tx.status = "pending"
        tx.blockchain_tx = None
        db.commit()

        logger.info(f"Admin initiated retry for transaction: {tx_id}")

        return {
            "status": "success",
            "message": f"Transaction {tx_id} queued for retry",
            "tx_id": tx_id
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrying transaction: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to retry transaction")


# ============================================================================
# SYSTEM HEALTH & MONITORING
# ============================================================================

@router.get("/health/circuit-breakers")
async def get_circuit_breaker_status(
    admin_key: str = Depends(verify_admin_key)
):
    """
    Get status of all circuit breakers.

    Requires admin authentication.

    Args:
        admin_key: Admin API key

    Returns:
        Circuit breaker status information
    """
    try:
        statuses = get_circuit_breaker_statuses()

        return {
            "circuit_breakers": statuses,
            "total_count": len(statuses),
            "open_count": sum(1 for s in statuses.values() if s["state"] == "open"),
            "half_open_count": sum(1 for s in statuses.values() if s["state"] == "half_open")
        }

    except Exception as e:
        logger.error(f"Error getting circuit breaker status: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to get circuit breaker status")


@router.post("/health/circuit-breakers/{name}/reset")
async def reset_circuit_breaker(
    name: str,
    admin_key: str = Depends(verify_admin_key)
):
    """
    Manually reset a circuit breaker.

    Use with caution - only for emergency recovery.

    Requires admin authentication.

    Args:
        name: Circuit breaker name
        admin_key: Admin API key

    Returns:
        Success response
    """
    try:
        from middleware.circuit_breaker import get_circuit_breaker

        circuit_breaker = get_circuit_breaker(name)
        if not circuit_breaker:
            raise HTTPException(status_code=404, detail=f"Circuit breaker '{name}' not found")

        circuit_breaker.reset()

        logger.warning(f"Admin manually reset circuit breaker: {name}")

        return {
            "status": "success",
            "message": f"Circuit breaker '{name}' reset to CLOSED state",
            "circuit_breaker": name
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error resetting circuit breaker: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to reset circuit breaker")


@router.get("/health/nonce-status/{wallet_address}")
async def get_nonce_status(
    wallet_address: str,
    admin_key: str = Depends(verify_admin_key)
):
    """
    Get nonce status for a wallet address.

    Requires admin authentication.

    Args:
        wallet_address: Wallet address
        admin_key: Admin API key

    Returns:
        Nonce status information
    """
    try:
        from services.nonce_manager import get_nonce_manager

        nonce_manager = get_nonce_manager()
        status = nonce_manager.get_status(wallet_address)

        return status

    except Exception as e:
        logger.error(f"Error getting nonce status: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to get nonce status")


@router.post("/health/nonce-reset/{wallet_address}")
async def reset_nonce(
    wallet_address: str,
    admin_key: str = Depends(verify_admin_key)
):
    """
    Reset nonce for a wallet address to blockchain state.

    Use to recover from nonce errors.

    Requires admin authentication.

    Args:
        wallet_address: Wallet address
        admin_key: Admin API key

    Returns:
        Success response with new nonce
    """
    try:
        from services.nonce_manager import get_nonce_manager

        nonce_manager = get_nonce_manager()
        new_nonce = nonce_manager.reset_nonce(wallet_address)

        logger.warning(f"Admin reset nonce for {wallet_address} to {new_nonce}")

        return {
            "status": "success",
            "message": f"Nonce reset for {wallet_address}",
            "wallet_address": wallet_address,
            "new_nonce": new_nonce
        }

    except Exception as e:
        logger.error(f"Error resetting nonce: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to reset nonce")


# ============================================================================
# AUDIT LOGS
# ============================================================================

@router.get("/audit/wallet-logs")
async def get_wallet_audit_logs(
    wallet_id: Optional[str] = Query(None, description="Filter by wallet ID"),
    action: Optional[str] = Query(None, description="Filter by action"),
    severity: Optional[str] = Query(None, description="Filter by severity"),
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    admin_key: str = Depends(verify_admin_key),
    db: Session = Depends(lambda: None)
):
    """
    Get wallet audit logs.

    Requires admin authentication.

    Args:
        wallet_id: Filter by wallet ID
        action: Filter by action
        severity: Filter by severity
        limit: Maximum results
        offset: Pagination offset
        admin_key: Admin API key
        db: Database session

    Returns:
        List of audit log entries
    """
    try:
        from database.models import Base, Column, Integer, String, DateTime, Text

        class WalletAuditLog(Base):
            __tablename__ = "wallet_audit_logs"
            id = Column(Integer, primary_key=True)
            wallet_id = Column(String(100))
            action = Column(String(50))
            severity = Column(String(20))
            details = Column(Text, nullable=True)
            timestamp = Column(DateTime)

        if db is None:
            raise HTTPException(status_code=500, detail="Database not available")

        query = db.query(WalletAuditLog)

        if wallet_id:
            query = query.filter(WalletAuditLog.wallet_id == wallet_id)
        if action:
            query = query.filter(WalletAuditLog.action == action)
        if severity:
            query = query.filter(WalletAuditLog.severity == severity)

        logs = query.order_by(WalletAuditLog.timestamp.desc()).limit(limit).offset(offset).all()

        import json
        return {
            "count": len(logs),
            "logs": [
                {
                    "id": log.id,
                    "wallet_id": log.wallet_id,
                    "action": log.action,
                    "severity": log.severity,
                    "details": json.loads(log.details) if log.details else None,
                    "timestamp": log.timestamp.isoformat()
                }
                for log in logs
            ]
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting audit logs: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to get audit logs")
