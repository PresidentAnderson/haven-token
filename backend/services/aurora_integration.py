"""
Aurora PMS Integration Service
Handles bi-directional token minting/burning with Aurora bookings.
"""

import os
import logging
from typing import Dict, Optional
from datetime import datetime, timedelta
import httpx
from sqlalchemy.orm import Session

from database.models import User, Transaction, AuroraBooking
from services.token_agent import TokenAgent

logger = logging.getLogger(__name__)


class AuroraIntegrationService:
    """
    Listens to Aurora booking events and automatically mints/burns tokens.
    Webhook-based architecture for real-time sync.
    """

    def __init__(self, token_agent: TokenAgent):
        self.aurora_api_url = os.getenv("AURORA_API_URL", "http://localhost:3001")
        self.aurora_api_key = os.getenv("AURORA_API_KEY")
        self.webhook_secret = os.getenv("AURORA_WEBHOOK_SECRET")
        self.token_agent = token_agent

    # ─────────────────────────────────────────────────────────────────────────
    # WEBHOOK HANDLERS (Called by Aurora)
    # ─────────────────────────────────────────────────────────────────────────

    def parseBookingData(self, raw_data: Dict) -> Dict:
        """
        Parse and validate booking data from Aurora webhook.

        Args:
            raw_data: Raw webhook payload from Aurora

        Returns:
            Normalized booking data dictionary
        """
        return {
            "id": raw_data.get("id", raw_data.get("booking_id")),
            "guest_id": raw_data.get("guest_id", raw_data.get("guestId")),
            "guest_email": raw_data.get("guest_email", raw_data.get("email", "")),
            "total_price": float(raw_data.get("total_price", raw_data.get("totalPrice", 0))),
            "nights": int(raw_data.get("nights", raw_data.get("numberOfNights", 1))),
            "status": raw_data.get("status", "active"),
            "check_in": raw_data.get("check_in", raw_data.get("checkIn")),
            "check_out": raw_data.get("check_out", raw_data.get("checkOut")),
        }

    def calculateRewardAmount(self, booking_total: float, nights: int, review_completed: bool = False) -> float:
        """
        Calculate reward tokens for a booking based on tokenomics.

        Reward structure:
        - Base: 2 HNV per CAD spent
        - Multiplier: +20% for multi-night stays (>1 night)
        - Bonus: +50 HNV if review completed (4+ stars)

        Args:
            booking_total: Total booking amount in CAD
            nights: Number of nights
            review_completed: Whether review was completed

        Returns:
            Total HNV reward amount
        """
        # Base reward: 2 HNV per CAD
        base_tokens = booking_total * 2.0

        # Multi-night multiplier: +20% for >1 night
        night_multiplier = 1.0 + (0.20 if nights > 1 else 0.0)

        # Calculate base reward with multiplier
        reward_tokens = base_tokens * night_multiplier

        # Add review bonus if applicable (handled separately in on_review_submitted)
        # This method only calculates booking reward, not review bonus

        logger.info(f"Reward calculation: ${booking_total} CAD x 2.0 x {night_multiplier} = {reward_tokens} HNV")

        return reward_tokens

    def handleBookingConfirmation(self, booking_data: Dict) -> bool:
        """
        Validate booking confirmation before processing rewards.

        Args:
            booking_data: Parsed booking data

        Returns:
            True if booking is valid for reward processing
        """
        required_fields = ["id", "guest_id", "total_price", "nights"]

        # Check all required fields are present
        for field in required_fields:
            if field not in booking_data or booking_data[field] is None:
                logger.error(f"Missing required field: {field}")
                return False

        # Validate booking total is positive
        if booking_data["total_price"] <= 0:
            logger.error(f"Invalid booking total: {booking_data['total_price']}")
            return False

        # Validate nights is positive
        if booking_data["nights"] <= 0:
            logger.error(f"Invalid nights: {booking_data['nights']}")
            return False

        logger.info(f"Booking confirmation validated: {booking_data['id']}")
        return True

    async def on_booking_created(self, booking_data: Dict, db: Session) -> None:
        """
        Triggered when guest completes booking in Aurora.
        Mint tokens based on booking value.

        Reward structure:
        - Base: 2 tokens per CAD spent
        - Multiplier: +20% for multi-night stays (>1 night)
        - Bonus: +50 HNV if review completed (4+ stars)
        """
        try:
            # 1. Parse and validate booking data
            parsed_data = self.parseBookingData(booking_data)

            if not self.handleBookingConfirmation(parsed_data):
                logger.error("Booking confirmation validation failed")
                return

            booking_id = parsed_data["id"]
            guest_id = parsed_data["guest_id"]
            booking_total = parsed_data["total_price"]
            nights = parsed_data["nights"]

            logger.info(f"🔔 Aurora booking created: {booking_id} (${booking_total} CAD)")

            # 2. Get or create user wallet
            user = await self._ensure_user_wallet(guest_id, parsed_data.get("guest_email", ""), db)

            # 3. Calculate reward using tokenomics method
            reward_tokens = self.calculateRewardAmount(booking_total, nights)

            # 4. Record in DB
            booking_record = AuroraBooking(
                booking_id=booking_id,
                user_id=user.user_id,
                booking_total=booking_total,
                nights=nights,
                reward_tokens=reward_tokens,
                status="active",
                created_at=datetime.utcnow()
            )
            db.add(booking_record)
            db.commit()

            # 5. Mint tokens async
            tx_id = f"aurora_booking_{booking_id}"
            await self.token_agent.process_mint(
                tx_id=tx_id,
                user_id=user.user_id,
                amount=reward_tokens,
                reason=f"booking_reward_{booking_id}_{nights}nights",
                db=db
            )

            logger.info(f"✅ Minted {reward_tokens} HNV for booking {booking_id}")

        except Exception as e:
            logger.error(f"❌ Booking handler error: {str(e)}", exc_info=True)
            raise

    async def on_booking_completed(self, booking_data: Dict, db: Session) -> None:
        """
        Triggered when guest checks out.
        Apply completion bonus (if not already applied).
        """
        try:
            booking_id = booking_data["id"]
            guest_id = booking_data["guest_id"]

            logger.info(f"🔔 Aurora booking completed: {booking_id}")

            user = db.query(User).filter(User.user_id == guest_id).first()
            if not user:
                logger.error(f"❌ User {guest_id} not found")
                return

            # Get booking record
            booking = db.query(AuroraBooking).filter(
                AuroraBooking.booking_id == booking_id
            ).first()
            if not booking:
                logger.error(f"❌ Booking {booking_id} not found in DB")
                return

            # Update booking status
            booking.status = "completed"
            booking.completed_at = datetime.utcnow()
            db.commit()

            logger.info(f"✅ Booking {booking_id} marked complete")

        except Exception as e:
            logger.error(f"❌ Completion handler error: {str(e)}", exc_info=True)
            raise

    async def on_booking_cancelled(self, booking_data: Dict, db: Session) -> None:
        """
        Triggered when booking cancelled.
        Reverse (burn) any minted tokens for this booking.
        """
        try:
            booking_id = booking_data["id"]
            guest_id = booking_data["guest_id"]
            refund_reason = booking_data.get("cancellation_reason", "cancelled")

            logger.info(f"🔔 Aurora booking cancelled: {booking_id}")

            user = db.query(User).filter(User.user_id == guest_id).first()
            if not user:
                return

            booking = db.query(AuroraBooking).filter(
                AuroraBooking.booking_id == booking_id
            ).first()
            if not booking or booking.status == "cancelled":
                return

            # Burn tokens
            await self.token_agent.process_burn(
                user_id=user.user_id,
                amount=booking.reward_tokens,
                reason=f"booking_cancelled_{booking_id}_{refund_reason}",
                db=db
            )

            # Update DB
            booking.status = "cancelled"
            booking.cancelled_at = datetime.utcnow()
            db.commit()

            logger.info(f"✅ Burned {booking.reward_tokens} HNV for cancelled booking {booking_id}")

        except Exception as e:
            logger.error(f"❌ Cancellation handler error: {str(e)}", exc_info=True)
            raise

    async def on_review_submitted(self, review_data: Dict, db: Session) -> None:
        """
        Triggered when guest submits review post-booking.
        Mint bonus tokens if review is positive (4+ stars).
        """
        try:
            review_id = review_data["id"]
            booking_id = review_data.get("booking_id", "")
            guest_id = review_data["guest_id"]
            rating = review_data.get("rating", 0)  # 1-5 stars

            logger.info(f"🔔 Aurora review submitted: {review_id} (booking {booking_id})")

            # Only reward 4+ star reviews
            if rating < 4:
                logger.info(f"⏭️  Review rating {rating} < 4, no bonus")
                return

            user = db.query(User).filter(User.user_id == guest_id).first()
            if not user:
                return

            # Bonus: 50 HNV per positive review (as per tokenomics)
            bonus_tokens = 50.0

            await self.token_agent.process_mint(
                tx_id=f"aurora_review_{review_id}",
                user_id=user.user_id,
                amount=bonus_tokens,
                reason=f"review_bonus_booking_{booking_id}_rating_{rating}",
                db=db
            )

            logger.info(f"✅ Minted {bonus_tokens} HNV review bonus")

        except Exception as e:
            logger.error(f"❌ Review handler error: {str(e)}", exc_info=True)
            raise

    # ─────────────────────────────────────────────────────────────────────────
    # HELPER METHODS
    # ─────────────────────────────────────────────────────────────────────────

    async def _ensure_user_wallet(self, aurora_user_id: str, email: str, db: Session) -> User:
        """
        Get existing user or create new with wallet address.
        """
        user = db.query(User).filter(User.user_id == aurora_user_id).first()

        if not user:
            # Create new user with generated wallet
            from web3 import Web3
            w3 = Web3()
            account = w3.eth.account.create()
            wallet_address = account.address

            user = User(
                user_id=aurora_user_id,
                email=email or f"{aurora_user_id}@aurora.placeholder",
                wallet_address=wallet_address,
                kyc_verified=False,
                created_at=datetime.utcnow()
            )
            db.add(user)
            db.commit()
            logger.info(f"✅ Created user {aurora_user_id} with wallet {wallet_address}")

        return user

    # ─────────────────────────────────────────────────────────────────────────
    # SYNC & POLLING (Fallback)
    # ─────────────────────────────────────────────────────────────────────────

    async def sync_recent_bookings(self, db: Session) -> None:
        """
        Fallback polling: sync bookings created in last hour.
        Run daily as safety net for missed webhooks.
        """
        try:
            logger.info("🔄 Syncing recent Aurora bookings...")

            since = datetime.utcnow() - timedelta(hours=1)

            bookings = await self._query_aurora_api(
                "/bookings",
                params={
                    "created_after": since.isoformat(),
                    "limit": 100
                }
            )

            for booking in bookings:
                # Check if already processed
                existing = db.query(AuroraBooking).filter(
                    AuroraBooking.booking_id == booking["id"]
                ).first()

                if not existing:
                    await self.on_booking_created(booking, db)

            logger.info(f"✅ Synced {len(bookings)} bookings")

        except Exception as e:
            logger.error(f"❌ Sync error: {str(e)}", exc_info=True)

    async def _query_aurora_api(self, endpoint: str, params: Dict) -> list:
        """
        Query Aurora API with authentication.
        """
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.aurora_api_url}{endpoint}",
                params=params,
                headers={"Authorization": f"Bearer {self.aurora_api_key}"}
            )
            response.raise_for_status()
            return response.json()
