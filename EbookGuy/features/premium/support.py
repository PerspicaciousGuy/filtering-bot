"""User-facing terms and support commands for Premium payments."""

from html import escape
from urllib.parse import urlparse

from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from EbookGuy.shared.global_settings import get_global_settings


TERMS_TEXT = """<b>Premium Terms and Conditions</b>

<b>1. Digital service</b>
Premium increases your bot usage limits for the purchased plan duration. It does
not guarantee that every requested file is available.

<b>2. Activation and duration</b>
Telegram Stars purchases are activated only after Telegram confirms a successful
payment. Buying another plan extends an existing active subscription.

<b>3. Refunds and payment issues</b>
Refund requests are reviewed using the Telegram payment receipt and transaction
details. Use /paysupport to contact us. Approved Stars refunds are returned
through Telegram's payment system.

<b>4. User responsibility</b>
Provide accurate payment information and keep your Telegram account secure.
Abuse, automated misuse, or attempts to bypass limits may result in restricted
access.

<b>5. Support responsibility</b>
Payments are made to this bot. The bot operator, not Telegram Support, handles
purchase questions, delivery issues, and refund requests.

By purchasing Premium, you confirm that you have read and accepted these terms."""


def _is_https_url(value: str) -> bool:
    parsed = urlparse(value)
    return parsed.scheme == "https" and bool(parsed.netloc)


async def handle_terms_command(client, message) -> None:
    """Show the terms that apply to Premium purchases."""
    await message.reply_text(TERMS_TEXT)


async def handle_payment_support_command(client, message) -> None:
    """Show payment support instructions and the configured contact button."""
    settings = await get_global_settings()
    support_url = str(settings.get("support_url") or "")
    markup = None
    if _is_https_url(support_url):
        markup = InlineKeyboardMarkup(
            [[InlineKeyboardButton("Contact Payment Support", url=support_url)]]
        )

    user_id = escape(str(message.from_user.id))
    await message.reply_text(
        (
            "<b>Premium Payment Support</b>\n\n"
            f"<b>Your Telegram ID:</b> <code>{user_id}</code>\n\n"
            "When contacting support, include:\n"
            "\u2022 Your Telegram ID\n"
            "\u2022 Selected Premium plan\n"
            "\u2022 Payment date and approximate time\n"
            "\u2022 Telegram Stars receipt or transaction ID\n"
            "\u2022 A screenshot of the error or receipt\n\n"
            "<b>Security:</b> Never send your password, OTP, card PIN, "
            "recovery phrase, or complete card details.\n\n"
            "Telegram Support cannot resolve purchases made through this bot."
        ),
        reply_markup=markup,
        disable_web_page_preview=True,
    )


__all__ = [
    "handle_payment_support_command",
    "handle_terms_command",
]
