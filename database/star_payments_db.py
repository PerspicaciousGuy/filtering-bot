"""Durable, idempotent Telegram Stars payment fulfillment."""

import asyncio
import datetime
import logging
from dataclasses import dataclass

from pymongo import ReturnDocument
from pymongo.errors import DuplicateKeyError, PyMongoError


logger = logging.getLogger(__name__)

STATUS_RECEIVED = "received"
STATUS_ACTIVATED = "activated"


@dataclass(frozen=True)
class StarPaymentActivation:
    """Result of applying one Telegram Stars charge to a user."""

    expires_at: datetime.datetime
    was_applied: bool


class StarPaymentsMixin:
    """Persist Stars charges and apply each charge at most once."""

    _star_payment_indexes_ready = False
    _star_payment_indexes_lock = asyncio.Lock()

    async def ensure_star_payment_indexes(self):
        """Create payment-ledger indexes once per process."""
        if self._star_payment_indexes_ready:
            return
        async with self._star_payment_indexes_lock:
            if self._star_payment_indexes_ready:
                return
            await self.star_payments.create_index(
                "telegram_payment_charge_id",
                unique=True,
            )
            await self.star_payments.create_index(
                [("user_id", 1), ("created_at", -1)]
            )
            self._star_payment_indexes_ready = True

    async def _register_star_payment(self, payment):
        now = datetime.datetime.utcnow()
        document = {
            **payment,
            "status": STATUS_RECEIVED,
            "created_at": now,
            "updated_at": now,
        }
        charge_filter = {
            "telegram_payment_charge_id": payment["telegram_payment_charge_id"]
        }
        try:
            stored = await self.star_payments.find_one_and_update(
                charge_filter,
                {"$setOnInsert": document},
                upsert=True,
                return_document=ReturnDocument.AFTER,
            )
        except DuplicateKeyError:
            stored = await self.star_payments.find_one(charge_filter)
        immutable_fields = (
            "user_id",
            "days",
            "stars",
            "currency",
            "invoice_payload",
        )
        if not stored or any(
            stored.get(field) != payment.get(field)
            for field in immutable_fields
        ):
            raise ValueError("Telegram Stars charge details do not match")
        return stored

    async def _apply_star_charge_to_user(self, payment):
        now = datetime.datetime.utcnow()
        charge_id = payment["telegram_payment_charge_id"]
        extension_ms = int(payment["days"]) * 24 * 60 * 60 * 1000
        return await self.col.find_one_and_update(
            {
                "id": int(payment["user_id"]),
                "applied_star_charge_ids": {"$ne": charge_id},
            },
            [{
                "$set": {
                    "is_premium": True,
                    "premium_expiry": {
                        "$add": [
                            {
                                "$cond": [
                                    {
                                        "$gt": [
                                            {"$ifNull": ["$premium_expiry", now]},
                                            now,
                                        ]
                                    },
                                    "$premium_expiry",
                                    now,
                                ]
                            },
                            extension_ms,
                        ]
                    },
                    "premium_expiry_notified_for": None,
                    "applied_star_charge_ids": {
                        "$concatArrays": [
                            {"$ifNull": ["$applied_star_charge_ids", []]},
                            [charge_id],
                        ]
                    },
                }
            }],
            projection={"premium_expiry": 1},
            return_document=ReturnDocument.AFTER,
        )

    async def _existing_star_activation(self, payment):
        user = await self.col.find_one(
            {"id": int(payment["user_id"])},
            {"premium_expiry": 1, "applied_star_charge_ids": 1},
        )
        charge_id = payment["telegram_payment_charge_id"]
        if not user:
            raise ValueError("Paid Telegram user does not exist")
        if charge_id not in user.get("applied_star_charge_ids", []):
            raise ValueError("Telegram Stars charge could not be applied")
        return user["premium_expiry"]

    async def _finalize_star_payment(self, payment, expires_at):
        charge_id = payment["telegram_payment_charge_id"]
        await self.star_payments.update_one(
            {"telegram_payment_charge_id": charge_id},
            {
                "$set": {
                    "status": STATUS_ACTIVATED,
                    "premium_expires_at": expires_at,
                    "activated_at": datetime.datetime.utcnow(),
                    "updated_at": datetime.datetime.utcnow(),
                },
                "$unset": {"last_error": ""},
            },
        )

    async def activate_star_payment(self, payment):
        """Activate Premium once for a validated Telegram Stars charge."""
        await self.ensure_star_payment_indexes()
        stored = await self._register_star_payment(payment)
        if stored.get("status") == STATUS_ACTIVATED:
            return StarPaymentActivation(
                expires_at=stored["premium_expires_at"],
                was_applied=False,
            )

        user = await self._apply_star_charge_to_user(payment)
        was_applied = user is not None
        expires_at = (
            user["premium_expiry"]
            if was_applied
            else await self._existing_star_activation(payment)
        )
        try:
            await self._finalize_star_payment(payment, expires_at)
        except PyMongoError:
            logger.exception("Premium activated but payment finalization failed")
        return StarPaymentActivation(expires_at, was_applied)


__all__ = ["StarPaymentActivation", "StarPaymentsMixin"]
