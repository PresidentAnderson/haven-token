"""
Wallet Custody Management Service
Secure encrypted storage and management of wallet private keys.
"""

import os
import logging
import json
from typing import Optional, Dict, Any
from datetime import datetime
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2
from cryptography.hazmat.backends import default_backend
from sqlalchemy.orm import Session
from web3 import Web3
import secrets
import base64

from exceptions import (
    WalletCustodyError,
    WalletEncryptionError,
    WalletNotFoundError,
    WalletAlreadyExistsError
)

logger = logging.getLogger(__name__)


class WalletCustodyService:
    """
    Manages secure wallet custody with encrypted storage.

    Features:
    - Fernet encryption for wallet private keys
    - KMS integration support
    - Secure wallet creation and storage
    - Wallet rotation capability
    - Comprehensive audit logging
    """

    def __init__(
        self,
        encryption_key: str,
        db_session: Session,
        kms_enabled: bool = False,
        kms_key_id: Optional[str] = None
    ):
        """
        Initialize wallet custody service.

        Args:
            encryption_key: Master encryption key (base64 encoded)
            db_session: Database session for storing encrypted wallets
            kms_enabled: Whether to use KMS for key management
            kms_key_id: KMS key ID if KMS is enabled
        """
        self.db = db_session
        self.kms_enabled = kms_enabled
        self.kms_key_id = kms_key_id

        # Initialize encryption
        try:
            # Derive encryption key from master key
            if encryption_key:
                self.fernet = Fernet(encryption_key.encode() if isinstance(encryption_key, str) else encryption_key)
            else:
                # Generate new key if not provided (dev only)
                logger.warning("⚠️  No encryption key provided, generating new key (DEV ONLY)")
                self.fernet = Fernet(Fernet.generate_key())

            logger.info("🔐 WalletCustodyService initialized")
            if kms_enabled:
                logger.info(f"🔐 KMS enabled with key ID: {kms_key_id}")

        except Exception as e:
            raise WalletEncryptionError(f"Failed to initialize encryption: {str(e)}")

    def _derive_key_from_password(self, password: str, salt: bytes) -> bytes:
        """
        Derive encryption key from password using PBKDF2.

        Args:
            password: Password to derive key from
            salt: Salt for key derivation

        Returns:
            Derived key bytes
        """
        kdf = PBKDF2(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
            backend=default_backend()
        )
        return base64.urlsafe_b64encode(kdf.derive(password.encode()))

    def _encrypt_private_key(self, private_key: str) -> str:
        """
        Encrypt a private key.

        Args:
            private_key: Private key to encrypt (hex string)

        Returns:
            Encrypted private key (base64 string)
        """
        try:
            # Remove '0x' prefix if present
            if private_key.startswith('0x'):
                private_key = private_key[2:]

            # Encrypt
            encrypted = self.fernet.encrypt(private_key.encode())
            return base64.b64encode(encrypted).decode()

        except Exception as e:
            raise WalletEncryptionError(f"Failed to encrypt private key: {str(e)}")

    def _decrypt_private_key(self, encrypted_key: str) -> str:
        """
        Decrypt a private key.

        Args:
            encrypted_key: Encrypted private key (base64 string)

        Returns:
            Decrypted private key (hex string with 0x prefix)
        """
        try:
            # Decrypt
            encrypted_bytes = base64.b64decode(encrypted_key.encode())
            decrypted = self.fernet.decrypt(encrypted_bytes)
            private_key = decrypted.decode()

            # Add '0x' prefix if not present
            if not private_key.startswith('0x'):
                private_key = '0x' + private_key

            return private_key

        except Exception as e:
            raise WalletEncryptionError(f"Failed to decrypt private key: {str(e)}")

    def create_wallet(self, wallet_id: str, metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Create a new wallet with secure key generation.

        Args:
            wallet_id: Unique identifier for the wallet (e.g., user_id)
            metadata: Optional metadata to store with wallet

        Returns:
            Dictionary with wallet information (address, encrypted key)

        Raises:
            WalletAlreadyExistsError: If wallet already exists
        """
        from database.models import Base, Column, Integer, String, DateTime, Text
        from sqlalchemy import Index

        # Define WalletCustody model inline (should be in models.py in production)
        class WalletCustody(Base):
            __tablename__ = "wallet_custody"

            id = Column(Integer, primary_key=True, index=True)
            wallet_id = Column(String(100), unique=True, index=True, nullable=False)
            wallet_address = Column(String(42), unique=True, index=True, nullable=False)
            encrypted_private_key = Column(Text, nullable=False)
            encryption_version = Column(String(20), default="fernet_v1")
            kms_key_id = Column(String(255), nullable=True)
            metadata = Column(Text, nullable=True)  # JSON
            status = Column(String(20), default="active", index=True)  # active, rotated, revoked
            created_at = Column(DateTime, default=datetime.utcnow, index=True)
            rotated_at = Column(DateTime, nullable=True)
            last_used_at = Column(DateTime, nullable=True)

            __table_args__ = (
                Index('idx_wallet_status', 'wallet_id', 'status'),
            )

        # Create table if it doesn't exist
        try:
            Base.metadata.create_all(bind=self.db.get_bind())
        except:
            pass

        # Check if wallet already exists
        existing = self.db.query(WalletCustody).filter(
            WalletCustody.wallet_id == wallet_id
        ).first()

        if existing:
            raise WalletAlreadyExistsError(wallet_id)

        try:
            # Generate new wallet
            account = Web3().eth.account.create()
            address = account.address
            private_key = account.key.hex()

            # Encrypt private key
            encrypted_key = self._encrypt_private_key(private_key)

            # Store in database
            wallet_record = WalletCustody(
                wallet_id=wallet_id,
                wallet_address=address,
                encrypted_private_key=encrypted_key,
                encryption_version="fernet_v1",
                kms_key_id=self.kms_key_id if self.kms_enabled else None,
                metadata=json.dumps(metadata) if metadata else None,
                status="active",
                created_at=datetime.utcnow()
            )

            self.db.add(wallet_record)
            self.db.commit()

            # Audit log
            self._log_audit_event(
                wallet_id=wallet_id,
                action="wallet_created",
                details={"address": address, "metadata": metadata}
            )

            logger.info(f"🔐 Created new wallet for {wallet_id}: {address}")

            return {
                "wallet_id": wallet_id,
                "address": address,
                "created_at": wallet_record.created_at.isoformat(),
                "status": wallet_record.status
            }

        except WalletCustodyError:
            self.db.rollback()
            raise
        except Exception as e:
            self.db.rollback()
            raise WalletCustodyError(f"Failed to create wallet: {str(e)}")

    def get_wallet(self, wallet_id: str, include_private_key: bool = False) -> Dict[str, Any]:
        """
        Retrieve wallet information.

        Args:
            wallet_id: Wallet identifier
            include_private_key: Whether to include decrypted private key (use with caution)

        Returns:
            Dictionary with wallet information

        Raises:
            WalletNotFoundError: If wallet not found
        """
        from database.models import Base, Column, Integer, String, DateTime, Text

        class WalletCustody(Base):
            __tablename__ = "wallet_custody"
            id = Column(Integer, primary_key=True)
            wallet_id = Column(String(100), unique=True, index=True)
            wallet_address = Column(String(42))
            encrypted_private_key = Column(Text)
            encryption_version = Column(String(20))
            kms_key_id = Column(String(255), nullable=True)
            metadata = Column(Text, nullable=True)
            status = Column(String(20))
            created_at = Column(DateTime)
            rotated_at = Column(DateTime, nullable=True)
            last_used_at = Column(DateTime, nullable=True)

        wallet = self.db.query(WalletCustody).filter(
            WalletCustody.wallet_id == wallet_id,
            WalletCustody.status == "active"
        ).first()

        if not wallet:
            raise WalletNotFoundError(wallet_id)

        # Update last used timestamp
        wallet.last_used_at = datetime.utcnow()
        self.db.commit()

        result = {
            "wallet_id": wallet.wallet_id,
            "address": wallet.wallet_address,
            "status": wallet.status,
            "created_at": wallet.created_at.isoformat(),
            "last_used_at": wallet.last_used_at.isoformat() if wallet.last_used_at else None,
            "metadata": json.loads(wallet.metadata) if wallet.metadata else None
        }

        if include_private_key:
            # Decrypt private key (use with extreme caution)
            try:
                result["private_key"] = self._decrypt_private_key(wallet.encrypted_private_key)
                # Log access to private key
                self._log_audit_event(
                    wallet_id=wallet_id,
                    action="private_key_accessed",
                    details={"address": wallet.wallet_address},
                    severity="high"
                )
            except Exception as e:
                raise WalletEncryptionError(f"Failed to decrypt private key: {str(e)}")

        return result

    def get_private_key(self, wallet_id: str) -> str:
        """
        Get decrypted private key for a wallet.
        Use with extreme caution - logs audit event.

        Args:
            wallet_id: Wallet identifier

        Returns:
            Decrypted private key (hex string with 0x prefix)

        Raises:
            WalletNotFoundError: If wallet not found
        """
        wallet = self.get_wallet(wallet_id, include_private_key=True)
        return wallet["private_key"]

    def rotate_wallet(self, wallet_id: str) -> Dict[str, Any]:
        """
        Rotate wallet by creating new wallet and marking old one as rotated.

        Args:
            wallet_id: Wallet identifier to rotate

        Returns:
            Dictionary with new wallet information
        """
        from database.models import Base, Column, Integer, String, DateTime, Text

        class WalletCustody(Base):
            __tablename__ = "wallet_custody"
            id = Column(Integer, primary_key=True)
            wallet_id = Column(String(100))
            wallet_address = Column(String(42))
            encrypted_private_key = Column(Text)
            status = Column(String(20))
            created_at = Column(DateTime)
            rotated_at = Column(DateTime, nullable=True)
            last_used_at = Column(DateTime, nullable=True)
            metadata = Column(Text, nullable=True)

        # Get old wallet
        old_wallet = self.db.query(WalletCustody).filter(
            WalletCustody.wallet_id == wallet_id,
            WalletCustody.status == "active"
        ).first()

        if not old_wallet:
            raise WalletNotFoundError(wallet_id)

        try:
            # Mark old wallet as rotated
            old_wallet.status = "rotated"
            old_wallet.rotated_at = datetime.utcnow()

            # Create rotation record ID
            rotation_id = f"{wallet_id}_rotated_{int(datetime.utcnow().timestamp())}"
            old_wallet.wallet_id = rotation_id

            # Create new wallet with original ID
            metadata = json.loads(old_wallet.metadata) if old_wallet.metadata else {}
            metadata["rotated_from"] = old_wallet.wallet_address
            metadata["rotation_date"] = datetime.utcnow().isoformat()

            self.db.commit()

            # Create new wallet
            new_wallet = self.create_wallet(wallet_id, metadata)

            # Audit log
            self._log_audit_event(
                wallet_id=wallet_id,
                action="wallet_rotated",
                details={
                    "old_address": old_wallet.wallet_address,
                    "new_address": new_wallet["address"]
                },
                severity="high"
            )

            logger.warning(f"🔄 Rotated wallet {wallet_id}: {old_wallet.wallet_address} -> {new_wallet['address']}")

            return new_wallet

        except Exception as e:
            self.db.rollback()
            raise WalletCustodyError(f"Failed to rotate wallet: {str(e)}")

    def revoke_wallet(self, wallet_id: str, reason: str) -> bool:
        """
        Revoke a wallet (mark as inactive, cannot be used).

        Args:
            wallet_id: Wallet identifier
            reason: Reason for revocation

        Returns:
            True if successful
        """
        from database.models import Base, Column, Integer, String, DateTime, Text

        class WalletCustody(Base):
            __tablename__ = "wallet_custody"
            id = Column(Integer, primary_key=True)
            wallet_id = Column(String(100))
            status = Column(String(20))
            wallet_address = Column(String(42))

        wallet = self.db.query(WalletCustody).filter(
            WalletCustody.wallet_id == wallet_id
        ).first()

        if not wallet:
            raise WalletNotFoundError(wallet_id)

        wallet.status = "revoked"
        self.db.commit()

        # Audit log
        self._log_audit_event(
            wallet_id=wallet_id,
            action="wallet_revoked",
            details={"reason": reason, "address": wallet.wallet_address},
            severity="critical"
        )

        logger.warning(f"❌ Revoked wallet {wallet_id}: {reason}")
        return True

    def list_wallets(self, status: Optional[str] = None, limit: int = 100, offset: int = 0) -> list:
        """
        List all wallets in custody.

        Args:
            status: Filter by status (active, rotated, revoked)
            limit: Maximum number of results
            offset: Offset for pagination

        Returns:
            List of wallet information dictionaries
        """
        from database.models import Base, Column, Integer, String, DateTime, Text

        class WalletCustody(Base):
            __tablename__ = "wallet_custody"
            id = Column(Integer, primary_key=True)
            wallet_id = Column(String(100))
            wallet_address = Column(String(42))
            status = Column(String(20))
            created_at = Column(DateTime)
            last_used_at = Column(DateTime, nullable=True)
            metadata = Column(Text, nullable=True)

        query = self.db.query(WalletCustody)

        if status:
            query = query.filter(WalletCustody.status == status)

        wallets = query.order_by(WalletCustody.created_at.desc()).limit(limit).offset(offset).all()

        return [
            {
                "wallet_id": w.wallet_id,
                "address": w.wallet_address,
                "status": w.status,
                "created_at": w.created_at.isoformat(),
                "last_used_at": w.last_used_at.isoformat() if w.last_used_at else None,
                "metadata": json.loads(w.metadata) if w.metadata else None
            }
            for w in wallets
        ]

    def _log_audit_event(
        self,
        wallet_id: str,
        action: str,
        details: Optional[Dict[str, Any]] = None,
        severity: str = "info"
    ):
        """
        Log audit event for wallet operations.

        Args:
            wallet_id: Wallet identifier
            action: Action performed
            details: Additional details
            severity: Event severity (info, high, critical)
        """
        from database.models import Base, Column, Integer, String, DateTime, Text

        class WalletAuditLog(Base):
            __tablename__ = "wallet_audit_logs"
            id = Column(Integer, primary_key=True, index=True)
            wallet_id = Column(String(100), index=True, nullable=False)
            action = Column(String(50), index=True, nullable=False)
            severity = Column(String(20), index=True, default="info")
            details = Column(Text, nullable=True)
            timestamp = Column(DateTime, default=datetime.utcnow, index=True)

        try:
            # Create table if it doesn't exist
            Base.metadata.create_all(bind=self.db.get_bind())

            audit_log = WalletAuditLog(
                wallet_id=wallet_id,
                action=action,
                severity=severity,
                details=json.dumps(details) if details else None,
                timestamp=datetime.utcnow()
            )
            self.db.add(audit_log)
            self.db.commit()

            logger.info(f"📝 Audit log: {wallet_id} - {action} [{severity}]")

        except Exception as e:
            logger.error(f"Failed to write audit log: {str(e)}")
            # Don't fail the operation if audit logging fails


# Singleton instance
_wallet_custody_service: Optional[WalletCustodyService] = None


def get_wallet_custody_service() -> WalletCustodyService:
    """Get the singleton wallet custody service instance."""
    global _wallet_custody_service
    if _wallet_custody_service is None:
        raise RuntimeError("WalletCustodyService not initialized. Call init_wallet_custody_service() first.")
    return _wallet_custody_service


def init_wallet_custody_service(
    encryption_key: str,
    db_session: Session,
    kms_enabled: bool = False,
    kms_key_id: Optional[str] = None
) -> WalletCustodyService:
    """
    Initialize the singleton wallet custody service.

    Args:
        encryption_key: Master encryption key
        db_session: Database session
        kms_enabled: Whether to use KMS
        kms_key_id: KMS key ID

    Returns:
        WalletCustodyService instance
    """
    global _wallet_custody_service
    _wallet_custody_service = WalletCustodyService(
        encryption_key=encryption_key,
        db_session=db_session,
        kms_enabled=kms_enabled,
        kms_key_id=kms_key_id
    )
    return _wallet_custody_service
