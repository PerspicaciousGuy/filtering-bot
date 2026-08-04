import os
import unittest
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

REQUIRED_TEST_ENVIRONMENT = {
    "API_ID": "123456",
    "API_HASH": "test-api-hash",
    "BOT_TOKEN": "123456:test-bot-token",
    "DATABASE_URI": "mongodb://localhost:27017",
    "ADMINS": "123456789",
}
for name, value in REQUIRED_TEST_ENVIRONMENT.items():
    os.environ.setdefault(name, value)


from EbookGuy.features.premium import payments


class PremiumPayloadTests(unittest.TestCase):
    def test_parses_current_invoice_payload(self):
        purchase = payments._parse_premium_payload(
            "premium_30_123456789_100"
        )

        self.assertEqual(purchase.user_id, 123456789)
        self.assertEqual(purchase.days, 30)
        self.assertEqual(purchase.stars, 100)

    def test_rejects_unknown_plan(self):
        with self.assertRaisesRegex(ValueError, "Invalid premium plan"):
            payments._parse_premium_payload(
                "premium_365_123456789_100"
            )

    def test_rejects_success_with_changed_amount(self):
        purchase = payments.PremiumPurchase(123456789, 30, 100)
        payment = SimpleNamespace(
            telegram_payment_charge_id="charge-1",
            currency="XTR",
            total_amount=99,
        )

        with self.assertRaisesRegex(ValueError, "Invalid successful"):
            payments._validate_successful_payment(
                payment,
                purchase,
                123456789,
            )

    def test_hides_unconfigured_external_payment_portal(self):
        settings = {"stars_payments_enabled": True}

        with patch.object(payments, "PAYMENT_WEBSITE", ""):
            buttons = payments._payment_method_buttons(30, settings)

        self.assertEqual(len(buttons), 2)
        self.assertEqual(buttons[0][0].callback_data, "confirm_premium_30")
        self.assertEqual(buttons[1][0].callback_data, "show_premium")


class PreCheckoutTests(unittest.IsolatedAsyncioTestCase):
    async def test_accepts_matching_stars_payment(self):
        query = SimpleNamespace(
            invoice_payload="premium_30_123456789_100",
            from_user=SimpleNamespace(id=123456789),
            currency="XTR",
            total_amount=100,
            answer=AsyncMock(),
        )
        settings = {
            "premium_purchases_enabled": True,
            "stars_payments_enabled": True,
        }

        with (
            patch.object(
                payments,
                "get_global_settings",
                AsyncMock(return_value=settings),
            ),
            patch.object(payments, "get_stars_price", return_value=100),
        ):
            await payments.handle_pre_checkout_handler(None, query)

        query.answer.assert_awaited_once_with(
            ok=True,
            error_message=None,
        )

    async def test_rejects_changed_stars_amount(self):
        query = SimpleNamespace(
            invoice_payload="premium_30_123456789_100",
            from_user=SimpleNamespace(id=123456789),
            currency="XTR",
            total_amount=99,
            answer=AsyncMock(),
        )
        settings = {
            "premium_purchases_enabled": True,
            "stars_payments_enabled": True,
        }

        with (
            patch.object(
                payments,
                "get_global_settings",
                AsyncMock(return_value=settings),
            ),
            patch.object(payments, "get_stars_price", return_value=100),
        ):
            await payments.handle_pre_checkout_handler(None, query)

        query.answer.assert_awaited_once_with(
            ok=False,
            error_message="Invalid payment request",
        )


if __name__ == "__main__":
    unittest.main()
