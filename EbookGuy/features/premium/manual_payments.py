"""Manual Google Pay and Binance Pay views for Premium purchases."""

import logging

from pyrogram.errors import ButtonUrlInvalid, MessageNotModified
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from EbookGuy.features.premium.manual_payment_options import (
    ManualPaymentDetails,
    get_manual_payment_details,
    is_http_url,
)
from EbookGuy.features.premium.plans import PLAN_DAYS
from EbookGuy.shared.global_settings import get_global_settings

logger = logging.getLogger(__name__)

MANUAL_PROVIDERS = ("upi", "binance")


def _payment_text(details: ManualPaymentDetails, direct_link_failed=False) -> str:
    direct_link_note = ""
    if direct_link_failed:
        direct_link_note = (
            "\n\n<b>Direct UPI link unavailable:</b> Copy the UPI ID and "
            "amount into your payment app."
        )
    return (
        f"<b>Pay with {details.provider_label}</b>\n\n"
        f"<b>Plan:</b> {details.days} days Premium\n"
        f"<b>Amount:</b> {details.amount_label}\n"
        f"<b>{details.destination_label}:</b> "
        f"<code>{details.destination_value}</code>\n\n"
        "Complete the payment using the button below. Premium is activated "
        "only after an administrator verifies your payment proof."
        f"{direct_link_note}"
    )


def _payment_markup(
    details: ManualPaymentDetails,
    include_payment_link: bool = True,
) -> InlineKeyboardMarkup:
    buttons = []
    if include_payment_link:
        buttons.append(
            [
                InlineKeyboardButton(
                    f"Pay {details.amount_label}",
                    url=details.payment_url,
                )
            ]
        )
    buttons.extend(
        [
            [
                InlineKeyboardButton(
                    "I Have Paid",
                    callback_data=(f"manual_paid_{details.provider}_{details.days}"),
                )
            ],
            [
                InlineKeyboardButton(
                    "Back",
                    callback_data=f"buy_premium_{details.days}",
                ),
                InlineKeyboardButton(
                    "All Plans",
                    callback_data="show_premium",
                ),
            ],
        ]
    )
    return InlineKeyboardMarkup(buttons)


def _parse_manual_callback(data: str, prefix: str) -> tuple[str, int]:
    parts = data.split("_")
    if len(parts) != 4 or "_".join(parts[:2]) != prefix:
        raise ValueError("Invalid manual payment callback")
    provider = parts[2]
    days = int(parts[3])
    if provider not in MANUAL_PROVIDERS or days not in PLAN_DAYS:
        raise ValueError("Unknown manual payment option")
    return provider, days


async def handle_manual_payment_callback(client, query) -> None:
    """Show the selected manual payment method and its direct link."""
    try:
        provider, days = _parse_manual_callback(
            query.data,
            "manual_payment",
        )
    except (TypeError, ValueError):
        await query.answer("Invalid payment option.", show_alert=True)
        return

    settings = await get_global_settings()
    if not settings["premium_purchases_enabled"]:
        await query.answer(
            "Premium purchases are temporarily disabled.",
            show_alert=True,
        )
        return

    details = get_manual_payment_details(provider, days, settings)
    if details is None:
        await query.answer(
            "This payment method is not configured.",
            show_alert=True,
        )
        return

    await query.answer()
    try:
        await query.message.edit_text(
            _payment_text(details),
            reply_markup=_payment_markup(details),
            disable_web_page_preview=True,
        )
    except ButtonUrlInvalid:
        logger.warning("Telegram rejected the direct %s URL", provider)
        await query.message.edit_text(
            _payment_text(details, direct_link_failed=True),
            reply_markup=_payment_markup(
                details,
                include_payment_link=False,
            ),
            disable_web_page_preview=True,
        )
    except MessageNotModified:
        logger.debug("Manual payment view is already current")


async def handle_manual_paid_callback(client, query) -> None:
    """Show proof instructions after a user reports manual payment."""
    try:
        provider, days = _parse_manual_callback(
            query.data,
            "manual_paid",
        )
    except (TypeError, ValueError):
        await query.answer("Invalid payment option.", show_alert=True)
        return

    settings = await get_global_settings()
    details = get_manual_payment_details(provider, days, settings)
    if details is None:
        await query.answer(
            "This payment method is not configured.",
            show_alert=True,
        )
        return

    await query.answer()
    support_url = str(settings.get("support_url") or "")
    buttons = []
    if is_http_url(support_url):
        buttons.append([InlineKeyboardButton("Send Payment Proof", url=support_url)])
    buttons.append(
        [
            InlineKeyboardButton(
                "Back to Payment",
                callback_data=f"manual_payment_{provider}_{days}",
            ),
            InlineKeyboardButton("All Plans", callback_data="show_premium"),
        ]
    )
    await query.message.edit_text(
        (
            "<b>Payment Proof Required</b>\n\n"
            f"<b>Method:</b> {details.provider_label}\n"
            f"<b>Plan:</b> {days} days\n"
            f"<b>Amount:</b> {details.amount_label}\n"
            f"<b>Your Telegram ID:</b> "
            f"<code>{query.from_user.id}</code>\n\n"
            "Send the payment screenshot, transaction ID, and your Telegram "
            "ID to support. Premium will be activated after verification."
        ),
        reply_markup=InlineKeyboardMarkup(buttons),
        disable_web_page_preview=True,
    )


__all__ = [
    "handle_manual_paid_callback",
    "handle_manual_payment_callback",
]
