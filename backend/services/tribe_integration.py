"""
Tribe App Integration Service
Handles community events, rewards, staking.
"""

import os
import logging
from typing import Dict
from datetime import datetime
from sqlalchemy.orm import Session

from database.models import User, TribeEvent, TribeReward, StakingRecord
from services.token_agent import TokenAgent

logger = logging.getLogger(__name__)


class TribeIntegrationService:
    """
    Integrates HAVEN tokens with Tribe community app.
    Rewards for: event attendance, contributions, coaching, staking.
    """

    def __init__(self, token_agent: TokenAgent):
        self.tribe_api_url = os.getenv("TRIBE_API_URL", "http://localhost:3002")
        self.tribe_api_key = os.getenv("TRIBE_API_KEY")
        self.tribe_webhook_secret = os.getenv("TRIBE_WEBHOOK_SECRET")
        self.token_agent = token_agent

    # ─────────────────────────────────────────────────────────────────────────
    # EVENT REWARDS
    # ─────────────────────────────────────────────────────────────────────────

    def parseEventData(self, raw_data: Dict) -> Dict:
        """
        Parse and validate event data from Tribe webhook.

        Args:
            raw_data: Raw webhook payload from Tribe

        Returns:
            Normalized event data dictionary
        """
        return {
            "id": raw_data.get("id", raw_data.get("event_id")),
            "attendee_id": raw_data.get("attendee_id", raw_data.get("user_id")),
            "name": raw_data.get("name", raw_data.get("event_name", "Unknown Event")),
            "type": raw_data.get("type", raw_data.get("event_type", "general")),
            "attended": raw_data.get("attended", True),
            "timestamp": raw_data.get("timestamp", raw_data.get("attended_at")),
        }

    def calculateAttendanceReward(self, event_type: str) -> float:
        """
        Calculate reward tokens for event attendance based on tokenomics.

        Reward structure (from tokenomics):
        - wisdom_circle: 100 HNV
        - workshop: 75 HNV
        - networking: 50 HNV
        - general: 25 HNV

        Args:
            event_type: Type of event

        Returns:
            HNV reward amount
        """
        reward_map = {
            "wisdom_circle": 100.0,
            "workshop": 75.0,
            "networking": 50.0,
            "general": 25.0
        }
        reward = reward_map.get(event_type, 25.0)

        logger.info(f"Event reward: {event_type} = {reward} HNV")
        return reward

    def handleEventAttendance(self, event_data: Dict) -> bool:
        """
        Validate event attendance data before processing rewards.

        Args:
            event_data: Parsed event data

        Returns:
            True if event attendance is valid for reward processing
        """
        required_fields = ["id", "attendee_id", "type"]

        # Check all required fields are present
        for field in required_fields:
            if field not in event_data or event_data[field] is None:
                logger.error(f"Missing required field: {field}")
                return False

        # Validate attendance flag
        if not event_data.get("attended", True):
            logger.info(f"Event {event_data['id']} not attended, no reward")
            return False

        logger.info(f"Event attendance validated: {event_data['id']}")
        return True

    async def on_event_attendance(self, event_data: Dict, db: Session) -> None:
        """
        Triggered when user attends Tribe event.
        Reward: 25-100 HNV per event (as per tokenomics).
        """
        try:
            # 1. Parse and validate event data
            parsed_data = self.parseEventData(event_data)

            if not self.handleEventAttendance(parsed_data):
                logger.error("Event attendance validation failed")
                return

            event_id = parsed_data["id"]
            user_id = parsed_data["attendee_id"]
            event_name = parsed_data["name"]
            event_type = parsed_data["type"]

            logger.info(f"🎉 Tribe event attended: {event_name}")

            user = db.query(User).filter(User.user_id == user_id).first()
            if not user:
                logger.error(f"❌ User {user_id} not found")
                return

            # 2. Calculate reward using tokenomics method
            reward_tokens = self.calculateAttendanceReward(event_type)

            # Record event
            tribe_event = TribeEvent(
                event_id=event_id,
                user_id=user_id,
                event_name=event_name,
                event_type=event_type,
                attended=True,
                tokens_earned=reward_tokens,
                attended_at=datetime.utcnow()
            )
            db.add(tribe_event)
            db.commit()

            # Mint tokens
            await self.token_agent.process_mint(
                tx_id=f"tribe_event_{event_id}_{user_id}",
                user_id=user_id,
                amount=reward_tokens,
                reason=f"event_attendance_{event_name.replace(' ', '_')}",
                db=db
            )

            logger.info(f"✅ Minted {reward_tokens} HNV for event attendance")

        except Exception as e:
            logger.error(f"❌ Event attendance error: {str(e)}", exc_info=True)

    async def on_contribution(self, contribution_data: Dict, db: Session) -> None:
        """
        Triggered when user contributes to Tribe community.
        (Post, comment, resource shared, etc.)
        Reward: Variable based on contribution quality.
        """
        try:
            contribution_id = contribution_data["id"]
            user_id = contribution_data["user_id"]
            contribution_type = contribution_data.get("type", "post")  # "post", "comment", "resource"
            quality_score = contribution_data.get("quality_score", 1.0)  # 0.5 - 2.0

            user = db.query(User).filter(User.user_id == user_id).first()
            if not user:
                return

            # Base rewards per contribution type
            base_rewards = {
                "post": 10.0,
                "comment": 5.0,
                "resource": 15.0,
                "guide": 25.0
            }
            base_reward = base_rewards.get(contribution_type, 5.0)
            reward_tokens = base_reward * quality_score

            # Create reward record
            reward = TribeReward(
                reward_id=contribution_id,
                user_id=user_id,
                reward_type="contribution",
                amount=reward_tokens,
                description=f"{contribution_type} contribution",
                status="pending"
            )
            db.add(reward)
            db.commit()

            # Mint tokens
            await self.token_agent.process_mint(
                tx_id=f"tribe_contribution_{contribution_id}",
                user_id=user_id,
                amount=reward_tokens,
                reason=f"contribution_{contribution_type}",
                db=db
            )

            # Update reward status
            reward.status = "processed"
            reward.processed_at = datetime.utcnow()
            db.commit()

            logger.info(f"✅ Minted {reward_tokens} HNV for {contribution_type}")

        except Exception as e:
            logger.error(f"❌ Contribution error: {str(e)}", exc_info=True)

    # ─────────────────────────────────────────────────────────────────────────
    # STAKING REWARDS
    # ─────────────────────────────────────────────────────────────────────────

    async def on_staking_started(self, stake_data: Dict, db: Session) -> None:
        """
        User stakes tokens in governance pool.
        Generate staking receipt in Tribe dashboard.
        """
        try:
            stake_id = stake_data["id"]
            user_id = stake_data["user_id"]
            amount = float(stake_data["amount"])

            logger.info(f"💰 Staking started: user {user_id}, amount {amount} HNV")

            # Record staking event
            record = StakingRecord(
                stake_id=stake_id,
                user_id=user_id,
                amount=amount,
                status="active",
                started_at=datetime.utcnow()
            )
            db.add(record)
            db.commit()

            logger.info(f"✅ Staking recorded")

        except Exception as e:
            logger.error(f"❌ Staking error: {str(e)}", exc_info=True)

    async def calculate_staking_rewards(self, db: Session) -> None:
        """
        Run weekly: calculate APY rewards for stakers.
        Mint new tokens to staking pool.

        APY: 10% annually = 0.192% weekly
        """
        try:
            logger.info("🔄 Calculating staking rewards...")

            active_stakes = db.query(StakingRecord).filter(
                StakingRecord.status == "active"
            ).all()

            # Simple APY: 10% annually = 0.192% weekly
            apy = 0.10
            weekly_rate = apy / 52

            total_rewards = 0.0

            for stake in active_stakes:
                reward = stake.amount * weekly_rate
                stake.earned_rewards += reward
                total_rewards += reward

                # Mint reward tokens
                await self.token_agent.process_mint(
                    tx_id=f"staking_reward_{stake.stake_id}_{datetime.utcnow().timestamp()}",
                    user_id=stake.user_id,
                    amount=reward,
                    reason=f"staking_reward_weekly",
                    db=db
                )

            db.commit()

            logger.info(f"✅ Calculated rewards for {len(active_stakes)} stakes (Total: {total_rewards} HNV)")

        except Exception as e:
            logger.error(f"❌ Reward calculation error: {str(e)}", exc_info=True)

    # ─────────────────────────────────────────────────────────────────────────
    # COACHING MILESTONES
    # ─────────────────────────────────────────────────────────────────────────

    async def on_coaching_milestone(self, milestone_data: Dict, db: Session) -> None:
        """
        Triggered when user completes coaching milestone.
        Reward: Variable based on milestone tier (100-250 HNV as per tokenomics).
        """
        try:
            user_id = milestone_data["user_id"]
            milestone_name = milestone_data.get("milestone_name", "Unknown Milestone")
            milestone_tier = milestone_data.get("tier", "basic")  # basic, intermediate, advanced

            user = db.query(User).filter(User.user_id == user_id).first()
            if not user:
                return

            # Tier-based rewards
            tier_rewards = {
                "basic": 100.0,
                "intermediate": 175.0,
                "advanced": 250.0
            }
            reward_tokens = tier_rewards.get(milestone_tier, 100.0)

            # Create reward record
            reward = TribeReward(
                reward_id=f"coaching_{user_id}_{milestone_name.replace(' ', '_')}",
                user_id=user_id,
                reward_type="coaching",
                amount=reward_tokens,
                description=f"Coaching milestone: {milestone_name}",
                status="pending"
            )
            db.add(reward)
            db.commit()

            # Mint tokens
            await self.token_agent.process_mint(
                tx_id=f"tribe_coaching_{user_id}_{milestone_name.replace(' ', '_')}",
                user_id=user_id,
                amount=reward_tokens,
                reason=f"coaching_milestone_{milestone_name.replace(' ', '_')}",
                db=db
            )

            # Update reward status
            reward.status = "processed"
            reward.processed_at = datetime.utcnow()
            db.commit()

            logger.info(f"✅ Minted {reward_tokens} HNV for milestone: {milestone_name}")

        except Exception as e:
            logger.error(f"❌ Coaching error: {str(e)}", exc_info=True)

    # ─────────────────────────────────────────────────────────────────────────
    # SYNC & POLLING (Fallback)
    # ─────────────────────────────────────────────────────────────────────────

    async def sync_recent_events(self, db: Session) -> None:
        """
        Fallback polling: sync events from last 24 hours.
        Run daily as safety net for missed webhooks.
        """
        try:
            from datetime import timedelta
            import httpx

            logger.info("🔄 Syncing recent Tribe events...")

            since = datetime.utcnow() - timedelta(hours=24)

            # Query Tribe API for recent events
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.tribe_api_url}/api/events",
                    params={
                        "since": since.isoformat(),
                        "limit": 100
                    },
                    headers={"Authorization": f"Bearer {self.tribe_api_key}"}
                )
                response.raise_for_status()
                events = response.json()

            for event in events:
                # Check if already processed
                existing = db.query(TribeEvent).filter(
                    TribeEvent.event_id == event["id"]
                ).first()

                if not existing and event.get("attended"):
                    await self.on_event_attendance(event, db)

            logger.info(f"✅ Synced {len(events)} events")

        except Exception as e:
            logger.error(f"❌ Event sync error: {str(e)}", exc_info=True)

    # ─────────────────────────────────────────────────────────────────────────
    # REFERRAL REWARDS
    # ─────────────────────────────────────────────────────────────────────────

    async def on_referral_success(self, referral_data: Dict, db: Session) -> None:
        """
        Triggered when a referral is successful (new user completes first action).
        Reward: 100-500 HNV based on tier (as per tokenomics).
        """
        try:
            referrer_id = referral_data["referrer_id"]
            referred_id = referral_data["referred_id"]
            tier = referral_data.get("tier", "basic")  # basic, silver, gold

            referrer = db.query(User).filter(User.user_id == referrer_id).first()
            if not referrer:
                return

            # Tier-based rewards
            tier_rewards = {
                "basic": 100.0,
                "silver": 250.0,
                "gold": 500.0
            }
            reward_tokens = tier_rewards.get(tier, 100.0)

            # Mint tokens
            await self.token_agent.process_mint(
                tx_id=f"referral_{referrer_id}_{referred_id}",
                user_id=referrer_id,
                amount=reward_tokens,
                reason=f"referral_bonus_{tier}",
                db=db
            )

            logger.info(f"✅ Minted {reward_tokens} HNV for referral ({tier} tier)")

        except Exception as e:
            logger.error(f"❌ Referral error: {str(e)}", exc_info=True)
