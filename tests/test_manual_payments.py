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
from EbookGuy.features.admin import settings_runtime_validation
from EbookGuy.shared.settings_schema import validate_setting_value


def manual_payment_settings(**overrides):
    settings = {
        "premium_30_days_inr": 170,
        "premium_90_days_inr": 425,
        "upi_payments_enabled": True,
        "upi_id": "merchant@bank",
        "upi_payee_name": "Example Merchant",
        "binance_payments_enabled": True,
        "binance_pay_id": "123456789",
        "binance_pay_url_30": "https://s.binance.com/example30",
        "binance_pay_url_90": "https://s.binance.com/example90",
        "binance_30_days_usd_cents": 199,
        "binance_90_days_usd_cents": 499,
    }
    settings.update(overrides)
    return settings


class ManualPaymentOptionTests(unittest.TestCase):
    def test_builds_upi_link_for_selected_plan_amount(self):
        settings = manual_payment_settings()

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
        settings = manual_payment_settings(
            binance_pay_url_90="https://s.binance.com/plan90",
        )

        details = manual_payment_options.get_manual_payment_details(
            "binance",
            90,
            settings,
        )

        self.assertEqual(details.payment_url, "https://s.binance.com/plan90")
        self.assertEqual(details.amount_label, "USD 4.99")
        self.assertEqual(details.destination_value, "123456789")

    def test_hides_invalid_binance_url(self):
        settings = manual_payment_settings(
            binance_pay_url_30="binance://unsupported",
        )

        details = manual_payment_options.get_manual_payment_details(
            "binance",
            30,
            settings,
        )

        self.assertIsNone(details)

    def test_hides_disabled_manual_payment_methods(self):
        settings = manual_payment_settings(
            upi_payments_enabled=False,
            binance_payments_enabled=False,
        )

        names = manual_payment_options.manual_payment_method_names(30, settings)

        self.assertEqual(names, [])


class ManualPaymentSettingValidationTests(unittest.TestCase):
    def test_accepts_binance_short_link(self):
        value = validate_setting_value(
            "binance_pay_url_30",
            "https://s.binance.com/example",
        )

        self.assertEqual(value, "https://s.binance.com/example")

    def test_rejects_non_binance_payment_link(self):
        with self.assertRaisesRegex(ValueError, "binance.com"):
            validate_setting_value(
                "binance_pay_url_30",
                "https://example.com/payment",
            )

    def test_clears_optional_payment_values_with_zero(self):
        self.assertEqual(validate_setting_value("upi_id", "0"), "")
        self.assertEqual(validate_setting_value("binance_pay_id", "0"), "")


class ManualPaymentRuntimeValidationTests(unittest.IsolatedAsyncioTestCase):
    async def test_rejects_enabling_incomplete_upi_configuration(self):
        settings = manual_payment_settings(
            upi_payments_enabled=False,
            upi_id="",
            upi_payee_name="",
        )

        with patch.object(
            settings_runtime_validation,
            "get_global_settings",
            AsyncMock(return_value=settings),
        ):
            with self.assertRaisesRegex(ValueError, "UPI ID and payee name"):
                await settings_runtime_validation.validate_runtime_setting(
                    None,
                    "upi_payments_enabled",
                    True,
                )

    async def test_allows_configuring_upi_while_method_is_disabled(self):
        settings = manual_payment_settings(
            upi_payments_enabled=False,
            upi_id="",
            upi_payee_name="",
        )

        with patch.object(
            settings_runtime_validation,
            "get_global_settings",
            AsyncMock(return_value=settings),
        ):
            await settings_runtime_validation.validate_runtime_setting(
                None,
                "upi_id",
                "merchant@bank",
            )


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
