import os
import unittest
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch
from urllib.parse import parse_qs, urlparse

from pyrogram.errors import ButtonUrlInvalid

REQUIRED_TEST_ENVIRONMENT = {
    "API_ID": "123456",
    "API_HASH": "test-api-hash",
    "BOT_TOKEN": "123456:test-bot-token",
    "DATABASE_URI": "mongodb://localhost:27017",
    "ADMINS": "123456789",
}
for name, value in REQUIRED_TEST_ENVIRONMENT.items():
    os.environ.setdefault(name, value)


from EbookGuy.features.premium import (
    manual_payment_options,
    manual_payments,
)


class ManualPaymentOptionTests(unittest.TestCase):
    def test_builds_upi_link_for_selected_plan_amount(self):
        settings = {"premium_30_days_inr": 170}

        with (
            patch.object(
                manual_payment_options,
                "UPI_ID",
                "merchant@bank",
            ),
            patch.object(
                manual_payment_options,
                "UPI_PAYEE_NAME",
                "Example Merchant",
            ),
        ):
            payment_url = manual_payment_options.build_upi_payment_url(
                30,
                settings,
            )

        query = parse_qs(urlparse(payment_url).query)
        self.assertEqual(urlparse(payment_url).scheme, "upi")
        self.assertEqual(query["pa"], ["merchant@bank"])
        self.assertEqual(query["pn"], ["Example Merchant"])
        self.assertEqual(query["cu"], ["INR"])
        self.assertEqual(query["am"], ["170"])

    def test_maps_binance_link_to_90_day_plan(self):
        settings = {"premium_90_days_inr": 425}

        with (
            patch.dict(
                manual_payment_options.BINANCE_URLS,
                {90: "https://pay.example/90"},
                clear=True,
            ),
            patch.dict(
                manual_payment_options.BINANCE_AMOUNTS,
                {90: "4.99"},
                clear=True,
            ),
            patch.object(
                manual_payment_options,
                "BINANCE_PAY_ID",
                "123456789",
            ),
        ):
            details = manual_payment_options.get_manual_payment_details(
                "binance",
                90,
                settings,
            )

        self.assertEqual(details.payment_url, "https://pay.example/90")
        self.assertEqual(details.amount_label, "USD 4.99")
        self.assertEqual(details.destination_value, "123456789")

    def test_hides_invalid_binance_url(self):
        settings = {"premium_30_days_inr": 170}

        with patch.dict(
            manual_payment_options.BINANCE_URLS,
            {30: "binance://unsupported"},
            clear=True,
        ):
            details = manual_payment_options.get_manual_payment_details(
                "binance",
                30,
                settings,
            )

        self.assertIsNone(details)


class ManualPaymentCallbackTests(unittest.IsolatedAsyncioTestCase):
    async def test_falls_back_when_telegram_rejects_upi_url(self):
        details = manual_payment_options.ManualPaymentDetails(
            provider="upi",
            provider_label="Google Pay / UPI",
            days=30,
            amount_label="INR 170",
            destination_label="UPI ID",
            destination_value="merchant@bank",
            payment_url="upi://pay?pa=merchant%40bank&am=170",
        )
        message = SimpleNamespace(
            edit_text=AsyncMock(
                side_effect=[ButtonUrlInvalid(), None],
            )
        )
        query = SimpleNamespace(
            data="manual_payment_upi_30",
            answer=AsyncMock(),
            message=message,
        )

        with (
            patch.object(
                manual_payments,
                "get_global_settings",
                AsyncMock(return_value={"premium_purchases_enabled": True}),
            ),
            patch.object(
                manual_payments,
                "get_manual_payment_details",
                return_value=details,
            ),
        ):
            await manual_payments.handle_manual_payment_callback(
                None,
                query,
            )

        self.assertEqual(message.edit_text.await_count, 2)
        fallback_call = message.edit_text.await_args_list[1]
        self.assertIn("Direct UPI link unavailable", fallback_call.args[0])
        fallback_rows = fallback_call.kwargs["reply_markup"].inline_keyboard
        self.assertEqual(fallback_rows[0][0].text, "I Have Paid")


if __name__ == "__main__":
    unittest.main()
