import datetime
import unittest
from unittest.mock import AsyncMock

from database.star_payments_db import (
    STATUS_ACTIVATED,
    STATUS_RECEIVED,
    StarPaymentsMixin,
)

PAYMENT = {
    "telegram_payment_charge_id": "charge-1",
    "user_id": 123456789,
    "days": 30,
    "stars": 100,
    "currency": "XTR",
    "invoice_payload": "premium_30_123456789_100",
}


class StarPaymentActivationTests(unittest.IsolatedAsyncioTestCase):
    async def test_does_not_reapply_activated_charge(self):
        expires_at = datetime.datetime(
            2026,
            9,
            1,
            tzinfo=datetime.timezone.utc,
        )
        subject = StarPaymentsMixin()
        subject.ensure_star_payment_indexes = AsyncMock()
        subject._register_star_payment = AsyncMock(return_value={
            **PAYMENT,
            "status": STATUS_ACTIVATED,
            "premium_expires_at": expires_at,
        })
        subject._apply_star_charge_to_user = AsyncMock()

        activation = await subject.activate_star_payment(PAYMENT)

        self.assertFalse(activation.was_applied)
        self.assertEqual(activation.expires_at, expires_at)
        subject._apply_star_charge_to_user.assert_not_awaited()

    async def test_applies_and_finalizes_new_charge(self):
        expires_at = datetime.datetime(
            2026,
            9,
            1,
            tzinfo=datetime.timezone.utc,
        )
        subject = StarPaymentsMixin()
        subject.ensure_star_payment_indexes = AsyncMock()
        subject._register_star_payment = AsyncMock(return_value={
            **PAYMENT,
            "status": STATUS_RECEIVED,
        })
        subject._apply_star_charge_to_user = AsyncMock(return_value={
            "premium_expiry": expires_at,
        })
        subject._finalize_star_payment = AsyncMock()

        activation = await subject.activate_star_payment(PAYMENT)

        self.assertTrue(activation.was_applied)
        self.assertEqual(activation.expires_at, expires_at)
        subject._finalize_star_payment.assert_awaited_once_with(
            PAYMENT,
            expires_at,
        )


if __name__ == "__main__":
    unittest.main()
