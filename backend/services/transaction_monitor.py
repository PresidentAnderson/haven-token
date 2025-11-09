"""
Transaction Monitoring Service
Real-time monitoring of blockchain transactions with alerting capabilities.
"""

import logging
import asyncio
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from web3 import Web3

from database.models import Transaction
from services.alerting import AlertingService, Alert, AlertSeverity
from exceptions import BlockchainError

logger = logging.getLogger(__name__)


class TransactionMonitor:
    """
    Monitors blockchain transactions for issues and triggers alerts.

    Monitors:
    - Pending transactions > 5 minutes
    - Failed transactions
    - Gas price spikes
    - Unusual transaction patterns
    """

    def __init__(
        self,
        db_session: Session,
        w3: Web3,
        alerting_service: AlertingService,
        pending_threshold_minutes: int = 5,
        gas_spike_threshold_multiplier: float = 2.0
    ):
        """
        Initialize transaction monitor.

        Args:
            db_session: Database session
            w3: Web3 instance
            alerting_service: Alerting service for notifications
            pending_threshold_minutes: Minutes before alerting on pending transactions
            gas_spike_threshold_multiplier: Multiplier for gas price spike detection
        """
        self.db = db_session
        self.w3 = w3
        self.alerting_service = alerting_service
        self.pending_threshold_minutes = pending_threshold_minutes
        self.gas_spike_threshold_multiplier = gas_spike_threshold_multiplier

        # Track baseline gas price
        self.baseline_gas_price: Optional[int] = None
        self.last_gas_price_check = datetime.utcnow()

        logger.info("📊 TransactionMonitor initialized")

    async def check_pending_transactions(self) -> List[Dict[str, Any]]:
        """
        Check for transactions pending longer than threshold.

        Returns:
            List of pending transaction alerts
        """
        try:
            threshold = datetime.utcnow() - timedelta(minutes=self.pending_threshold_minutes)

            pending_txs = self.db.query(Transaction).filter(
                Transaction.status.in_(["pending", "confirming"]),
                Transaction.created_at < threshold
            ).all()

            alerts = []

            for tx in pending_txs:
                time_pending = (datetime.utcnow() - tx.created_at).total_seconds() / 60

                # Check if transaction is still pending on blockchain
                blockchain_status = None
                if tx.blockchain_tx:
                    try:
                        receipt = self.w3.eth.get_transaction_receipt(tx.blockchain_tx)
                        blockchain_status = "confirmed" if receipt else "pending"
                    except Exception:
                        blockchain_status = "not_found"

                alert_data = {
                    "tx_id": tx.tx_id,
                    "user_id": tx.user_id,
                    "tx_type": tx.tx_type,
                    "amount": tx.amount,
                    "created_at": tx.created_at.isoformat(),
                    "time_pending_minutes": round(time_pending, 2),
                    "blockchain_tx": tx.blockchain_tx,
                    "blockchain_status": blockchain_status
                }

                # Create alert
                severity = AlertSeverity.WARNING
                if time_pending > 30:
                    severity = AlertSeverity.CRITICAL
                elif time_pending > 15:
                    severity = AlertSeverity.ERROR

                alert = Alert(
                    title=f"Transaction Pending: {tx.tx_id}",
                    message=f"Transaction {tx.tx_id} has been pending for {round(time_pending, 1)} minutes",
                    severity=severity,
                    category="transaction_pending",
                    data=alert_data
                )

                await self.alerting_service.send_alert(alert)
                alerts.append(alert_data)

                logger.warning(
                    f"⏱️  Transaction {tx.tx_id} pending for {round(time_pending, 1)} minutes"
                )

            return alerts

        except Exception as e:
            logger.error(f"Error checking pending transactions: {str(e)}", exc_info=True)
            return []

    async def check_failed_transactions(self) -> List[Dict[str, Any]]:
        """
        Check for recently failed transactions.

        Returns:
            List of failed transaction alerts
        """
        try:
            # Check last hour for new failures
            since = datetime.utcnow() - timedelta(hours=1)

            failed_txs = self.db.query(Transaction).filter(
                Transaction.status == "failed",
                Transaction.created_at >= since
            ).all()

            alerts = []

            for tx in failed_txs:
                alert_data = {
                    "tx_id": tx.tx_id,
                    "user_id": tx.user_id,
                    "tx_type": tx.tx_type,
                    "amount": tx.amount,
                    "created_at": tx.created_at.isoformat(),
                    "reason": tx.reason,
                    "blockchain_tx": tx.blockchain_tx
                }

                # Create alert
                alert = Alert(
                    title=f"Transaction Failed: {tx.tx_id}",
                    message=f"Transaction {tx.tx_id} failed. Type: {tx.tx_type}, Amount: {tx.amount}",
                    severity=AlertSeverity.ERROR,
                    category="transaction_failed",
                    data=alert_data
                )

                await self.alerting_service.send_alert(alert)
                alerts.append(alert_data)

                logger.error(f"❌ Transaction {tx.tx_id} failed: {tx.reason}")

            return alerts

        except Exception as e:
            logger.error(f"Error checking failed transactions: {str(e)}", exc_info=True)
            return []

    async def check_gas_prices(self) -> Optional[Dict[str, Any]]:
        """
        Check for gas price spikes.

        Returns:
            Gas price alert data if spike detected, None otherwise
        """
        try:
            current_gas_price = self.w3.eth.gas_price

            # Update baseline if first check or periodic update (every hour)
            if (self.baseline_gas_price is None or
                (datetime.utcnow() - self.last_gas_price_check).total_seconds() > 3600):
                self.baseline_gas_price = current_gas_price
                self.last_gas_price_check = datetime.utcnow()
                logger.info(f"⛽ Updated baseline gas price: {self.w3.from_wei(current_gas_price, 'gwei')} gwei")
                return None

            # Check for spike
            spike_threshold = self.baseline_gas_price * self.gas_spike_threshold_multiplier

            if current_gas_price > spike_threshold:
                current_gwei = float(self.w3.from_wei(current_gas_price, 'gwei'))
                baseline_gwei = float(self.w3.from_wei(self.baseline_gas_price, 'gwei'))
                multiplier = current_gas_price / self.baseline_gas_price

                alert_data = {
                    "current_gas_price_gwei": current_gwei,
                    "baseline_gas_price_gwei": baseline_gwei,
                    "multiplier": round(multiplier, 2),
                    "threshold_multiplier": self.gas_spike_threshold_multiplier,
                    "timestamp": datetime.utcnow().isoformat()
                }

                # Create alert
                alert = Alert(
                    title="Gas Price Spike Detected",
                    message=f"Gas price spiked to {current_gwei:.2f} gwei ({multiplier:.1f}x baseline of {baseline_gwei:.2f} gwei)",
                    severity=AlertSeverity.WARNING,
                    category="gas_price_spike",
                    data=alert_data
                )

                await self.alerting_service.send_alert(alert)

                logger.warning(
                    f"⛽ Gas price spike: {current_gwei:.2f} gwei "
                    f"({multiplier:.1f}x baseline {baseline_gwei:.2f} gwei)"
                )

                return alert_data

            return None

        except Exception as e:
            logger.error(f"Error checking gas prices: {str(e)}", exc_info=True)
            return None

    async def check_transaction_on_chain(self, tx_id: str) -> Optional[Dict[str, Any]]:
        """
        Check transaction status on blockchain and update database.

        Args:
            tx_id: Transaction ID to check

        Returns:
            Transaction status information
        """
        try:
            tx = self.db.query(Transaction).filter(Transaction.tx_id == tx_id).first()
            if not tx or not tx.blockchain_tx:
                return None

            try:
                receipt = self.w3.eth.get_transaction_receipt(tx.blockchain_tx)

                if receipt:
                    # Update transaction status
                    if receipt['status'] == 1:
                        tx.status = "confirmed"
                        tx.confirmed_at = datetime.utcnow()
                        tx.gas_used = receipt['gasUsed']
                        logger.info(f"✅ Confirmed transaction {tx_id}")
                    else:
                        tx.status = "failed"
                        logger.error(f"❌ Transaction {tx_id} failed on chain")

                    self.db.commit()

                    return {
                        "tx_id": tx_id,
                        "blockchain_tx": tx.blockchain_tx,
                        "status": tx.status,
                        "gas_used": tx.gas_used,
                        "confirmed_at": tx.confirmed_at.isoformat() if tx.confirmed_at else None
                    }

            except Exception as e:
                # Transaction not found on chain
                logger.warning(f"Transaction {tx_id} not found on chain: {str(e)}")
                return None

        except Exception as e:
            logger.error(f"Error checking transaction on chain: {str(e)}", exc_info=True)
            return None

    async def monitor_user_transactions(self, user_id: str) -> Dict[str, Any]:
        """
        Monitor all transactions for a specific user.

        Args:
            user_id: User ID to monitor

        Returns:
            Summary of user's transaction status
        """
        try:
            transactions = self.db.query(Transaction).filter(
                Transaction.user_id == user_id
            ).all()

            pending_count = sum(1 for tx in transactions if tx.status in ["pending", "confirming"])
            failed_count = sum(1 for tx in transactions if tx.status == "failed")
            confirmed_count = sum(1 for tx in transactions if tx.status == "confirmed")

            # Check for stuck transactions
            threshold = datetime.utcnow() - timedelta(minutes=self.pending_threshold_minutes)
            stuck_txs = [
                tx for tx in transactions
                if tx.status in ["pending", "confirming"] and tx.created_at < threshold
            ]

            return {
                "user_id": user_id,
                "total_transactions": len(transactions),
                "pending_count": pending_count,
                "failed_count": failed_count,
                "confirmed_count": confirmed_count,
                "stuck_transactions": len(stuck_txs),
                "stuck_tx_ids": [tx.tx_id for tx in stuck_txs]
            }

        except Exception as e:
            logger.error(f"Error monitoring user transactions: {str(e)}", exc_info=True)
            return {"error": str(e)}

    async def get_monitoring_summary(self) -> Dict[str, Any]:
        """
        Get overall monitoring summary.

        Returns:
            Monitoring summary with key metrics
        """
        try:
            # Count transactions by status
            pending_count = self.db.query(Transaction).filter(
                Transaction.status.in_(["pending", "confirming"])
            ).count()

            failed_count = self.db.query(Transaction).filter(
                Transaction.status == "failed"
            ).count()

            confirmed_count = self.db.query(Transaction).filter(
                Transaction.status == "confirmed"
            ).count()

            # Stuck transactions
            threshold = datetime.utcnow() - timedelta(minutes=self.pending_threshold_minutes)
            stuck_count = self.db.query(Transaction).filter(
                Transaction.status.in_(["pending", "confirming"]),
                Transaction.created_at < threshold
            ).count()

            # Recent failures (last 24 hours)
            since = datetime.utcnow() - timedelta(hours=24)
            recent_failures = self.db.query(Transaction).filter(
                Transaction.status == "failed",
                Transaction.created_at >= since
            ).count()

            # Get current gas price
            try:
                current_gas_price = self.w3.eth.gas_price
                current_gas_gwei = float(self.w3.from_wei(current_gas_price, 'gwei'))
            except:
                current_gas_gwei = None

            return {
                "timestamp": datetime.utcnow().isoformat(),
                "transactions": {
                    "pending": pending_count,
                    "failed": failed_count,
                    "confirmed": confirmed_count,
                    "stuck": stuck_count
                },
                "recent_failures_24h": recent_failures,
                "gas_price_gwei": current_gas_gwei,
                "baseline_gas_price_gwei": float(self.w3.from_wei(self.baseline_gas_price, 'gwei')) if self.baseline_gas_price else None
            }

        except Exception as e:
            logger.error(f"Error getting monitoring summary: {str(e)}", exc_info=True)
            return {"error": str(e)}

    async def run_monitoring_cycle(self):
        """
        Run a complete monitoring cycle.
        This should be called periodically (e.g., every minute).
        """
        logger.info("🔍 Running transaction monitoring cycle...")

        try:
            # Check pending transactions
            pending_alerts = await self.check_pending_transactions()
            if pending_alerts:
                logger.info(f"Found {len(pending_alerts)} stuck pending transactions")

            # Check failed transactions
            failed_alerts = await self.check_failed_transactions()
            if failed_alerts:
                logger.info(f"Found {len(failed_alerts)} recent failed transactions")

            # Check gas prices
            gas_alert = await self.check_gas_prices()
            if gas_alert:
                logger.info("Gas price spike detected")

            # Get summary
            summary = await self.get_monitoring_summary()
            logger.info(
                f"📊 Monitoring summary: "
                f"pending={summary['transactions']['pending']}, "
                f"stuck={summary['transactions']['stuck']}, "
                f"failed={summary['transactions']['failed']}, "
                f"gas={summary.get('gas_price_gwei')} gwei"
            )

        except Exception as e:
            logger.error(f"Error in monitoring cycle: {str(e)}", exc_info=True)


# Singleton instance
_transaction_monitor: Optional[TransactionMonitor] = None


def get_transaction_monitor() -> TransactionMonitor:
    """Get the singleton transaction monitor instance."""
    global _transaction_monitor
    if _transaction_monitor is None:
        raise RuntimeError("TransactionMonitor not initialized. Call init_transaction_monitor() first.")
    return _transaction_monitor


def init_transaction_monitor(
    db_session: Session,
    w3: Web3,
    alerting_service: AlertingService,
    pending_threshold_minutes: int = 5,
    gas_spike_threshold_multiplier: float = 2.0
) -> TransactionMonitor:
    """
    Initialize the singleton transaction monitor.

    Args:
        db_session: Database session
        w3: Web3 instance
        alerting_service: Alerting service
        pending_threshold_minutes: Threshold for pending transactions
        gas_spike_threshold_multiplier: Multiplier for gas spike detection

    Returns:
        TransactionMonitor instance
    """
    global _transaction_monitor
    _transaction_monitor = TransactionMonitor(
        db_session=db_session,
        w3=w3,
        alerting_service=alerting_service,
        pending_threshold_minutes=pending_threshold_minutes,
        gas_spike_threshold_multiplier=gas_spike_threshold_multiplier
    )
    return _transaction_monitor
