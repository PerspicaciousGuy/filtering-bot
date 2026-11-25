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


from pyrogram import raw
from pyrogram.errors import BadRequest
from pyrogram.types import InlineKeyboardButton

from EbookGuy.features.premium import manual_payments, message_effects
from EbookGuy.features.premium.manual_payment_options import (
    ManualPaymentDetails,
)
from EbookGuy.features.search import rendering
from EbookGuy.features.search.pagination import (
    NO_MORE_PAGES_TEXT,
    PaginationState,
    build_pagination_row,
)
from EbookGuy.shared.bot_api import BotApiError


def _details(copy_value):
    return ManualPaymentDetails(
        provider="upi",
        provider_label="Google Pay / UPI",
        days=30,
        amount_label="INR 99",
        destination_label="UPI ID",
        destination_value=copy_value or "Open the payment link",
        payment_url="upi://pay?pa=x",
        copy_value=copy_value,
    )


class CopyButtonTests(unittest.TestCase):
    def test_adds_copy_button_for_payment_id(self):
        markup = manual_payments._payment_markup(_details("name@upi"))
        copy_buttons = [
            button
            for row in markup.inline_keyboard
            for button in row
            if button.copy_text
        ]
        self.assertEqual(len(copy_buttons), 1)
        self.assertEqual(copy_buttons[0].text, "Copy UPI ID")
        self.assertEqual(copy_buttons[0].copy_text, "name@upi")

    def test_skips_copy_button_without_payment_id(self):
        markup = manual_payments._payment_markup(_details(""))
        self.assertFalse(any(
            button.copy_text
            for row in markup.inline_keyboard
            for button in row
        ))

    def test_skips_copy_button_over_telegram_limit(self):
        markup = manual_payments._payment_markup(_details("x" * 257))
        self.assertFalse(any(
            button.copy_text
            for row in markup.inline_keyboard
            for button in row
        ))


class DisabledLastPageTests(unittest.IsolatedAsyncioTestCase):
    def _buttons(self, next_offset=0):
        row = build_pagination_row(
            PaginationState("1", "k", 0, next_offset, 5, 10),
            is_initial=True,
        )
        return [
            [InlineKeyboardButton("[1 KB] Book", callback_data="file#abc")],
            row,
        ]

    def test_builds_disabled_last_row(self):
        keyboard = rendering._disabled_last_page_keyboard(self._buttons())
        self.assertEqual(
            keyboard,
            [
                [{"text": "[1 KB] Book", "callback_data": "file#abc"}],
                [{"text": NO_MORE_PAGES_TEXT, "disabled": {}}],
            ],
        )

    def test_leaves_multi_page_results_alone(self):
        self.assertIsNone(
            rendering._disabled_last_page_keyboard(self._buttons(10))
        )

    async def test_falls_back_when_bot_api_fails(self):
        message = SimpleNamespace(chat=SimpleNamespace(id=1), id=2)
        with patch.object(
            rendering,
            "call_bot_api",
            AsyncMock(side_effect=BotApiError("rejected")),
        ):
            edited = await rendering._edit_with_disabled_last_page(
                message, "text", self._buttons()
            )
        self.assertFalse(edited)

    async def test_sends_disabled_button_edit(self):
        message = SimpleNamespace(chat=SimpleNamespace(id=1), id=2)
        call = AsyncMock(return_value={})
        with patch.object(rendering, "call_bot_api", call):
            edited = await rendering._edit_with_disabled_last_page(
                message, "<b>text</b>", self._buttons()
            )
        self.assertTrue(edited)
        method, payload = call.await_args.args
        self.assertEqual(method, "editMessageText")
        self.assertEqual(payload["chat_id"], 1)
        self.assertEqual(payload["message_id"], 2)
        self.assertEqual(payload["parse_mode"], "HTML")
        self.assertEqual(
            payload["reply_markup"]["inline_keyboard"][-1],
            [{"text": NO_MORE_PAGES_TEXT, "disabled": {}}],
        )


def _effect(effect_id, emoticon, premium=False):
    return raw.types.AvailableEffect(
        id=effect_id,
        emoticon=emoticon,
        effect_sticker_id=1,
        premium_required=premium,
    )


class CelebrationEffectTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        message_effects._effect_cache.clear()

    async def test_picks_free_party_popper_effect(self):
        client = SimpleNamespace(invoke=AsyncMock(return_value=SimpleNamespace(
            effects=[
                _effect(1, "\U0001f389", premium=True),
                _effect(2, "\U0001f525"),
                _effect(3, "\U0001f389"),
            ]
        )))
        self.assertEqual(
            await message_effects.get_celebration_effect_id(client), 3
        )

    async def test_reply_uses_effect(self):
        client = SimpleNamespace(invoke=AsyncMock(return_value=SimpleNamespace(
            effects=[_effect(3, "\U0001f389")]
        )))
        message = SimpleNamespace(reply_text=AsyncMock())
        await message_effects.reply_with_celebration(client, message, "Paid")
        message.reply_text.assert_awaited_once_with(
            "Paid", message_effect_id=3
        )

    async def test_reply_without_effect_when_lookup_fails(self):
        client = SimpleNamespace(
            invoke=AsyncMock(side_effect=BadRequest("BOT_METHOD_INVALID"))
        )
        message = SimpleNamespace(reply_text=AsyncMock())
        await message_effects.reply_with_celebration(client, message, "Paid")
        message.reply_text.assert_awaited_once_with("Paid")

    async def test_reply_retries_plainly_when_effect_rejected(self):
        client = SimpleNamespace(invoke=AsyncMock(return_value=SimpleNamespace(
            effects=[_effect(3, "\U0001f389")]
        )))
        message = SimpleNamespace(reply_text=AsyncMock(
            side_effect=[BadRequest("EFFECT_INVALID"), None]
        ))
        await message_effects.reply_with_celebration(client, message, "Paid")
        self.assertEqual(message.reply_text.await_count, 2)
        self.assertEqual(
            message.reply_text.await_args_list[1].args, ("Paid",)
        )
        self.assertEqual(message.reply_text.await_args_list[1].kwargs, {})


if __name__ == "__main__":
    unittest.main()
