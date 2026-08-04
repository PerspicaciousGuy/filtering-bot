import logging
from dataclasses import dataclass

from pymongo.errors import PyMongoError
from pyrogram.errors import MessageNotModified, RPCError
from pyrogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    LabeledPrice,
    PreCheckoutQuery,
)

from database.users_chats_db import db
from EbookGuy.features.premium.manual_payment_options import (
    manual_payment_method_buttons,
    manual_payment_method_names,
)
from EbookGuy.features.premium.plans import (
    PLAN_DAYS,
    get_inr_price,
    get_stars_price,
)
from EbookGuy.shared.analytics import track_event
from EbookGuy.shared.global_settings import (
    describe_daily_limit,
    get_global_settings,
)
from info import PAYMENT_WEBSITE

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
last_invoice_messages = {}


@dataclass(frozen=True)
class PremiumInvoice:
    """Validated data needed to issue one Telegram Stars invoice."""

    user_id: int
    days: int
    stars: int
    download_benefit: str


@dataclass(frozen=True)
class PremiumPurchase:
    """Premium plan details encoded in an invoice payload."""

    user_id: int
    days: int
    stars: int | None


def _parse_premium_payload(payload):
    parts = str(payload).split("_")
    if len(parts) not in (3, 4) or parts[0] != "premium":
        raise ValueError("Invalid premium invoice payload")
    purchase = PremiumPurchase(
        user_id=int(parts[2]),
        days=int(parts[1]),
        stars=int(parts[3]) if len(parts) == 4 else None,
    )
    if purchase.days not in PLAN_DAYS:
        raise ValueError("Invalid premium plan")
    return purchase


def _track_payment_success(user_id, payment, days):
    track_event(
        "payment.completed",
        user_id,
        days=days,
        stars=int(payment.total_amount),
        currency=str(payment.currency),
    )


async def _clear_previous_invoice(client, query, user_id):
    if user_id in last_invoice_messages:
        try:
            await client.delete_messages(user_id, last_invoice_messages[user_id])
        except (KeyError, PyMongoError, RPCError, TypeError, ValueError):
            logger.debug("Previous invoice was already unavailable", exc_info=True)
    try:
        await query.message.delete()
    except (KeyError, PyMongoError, RPCError, TypeError, ValueError):
        logger.debug("Payment confirmation was already unavailable", exc_info=True)


async def _send_premium_invoice(client, invoice):
    return await client.send_invoice(
        chat_id=invoice.user_id,
        title=f"Premium - {invoice.days} Days",
        description=(
            f"Get {invoice.days} days of Premium access with "
            f"{invoice.download_benefit}. Existing Premium is extended."
        ),
        payload=(
            f"premium_{invoice.days}_{invoice.user_id}_{invoice.stars}"
        ),
        currency="XTR",
        prices=[LabeledPrice(
            label=f"{invoice.days} Days Premium",
            amount=invoice.stars,
        )],
    )


def _payment_method_buttons(days, settings):
    buttons = []
    if settings["stars_payments_enabled"]:
        buttons.append([
            InlineKeyboardButton(
                "⭐ Pay with Telegram Stars",
                callback_data=f"confirm_premium_{days}",
            )
        ])
    manual_buttons = manual_payment_method_buttons(days, settings)
    buttons.extend(manual_buttons)
    if (
        not manual_buttons
        and PAYMENT_WEBSITE.startswith(("https://", "http://"))
    ):
        buttons.append([
            InlineKeyboardButton(
                "Open Payment Portal",
                url=PAYMENT_WEBSITE,
            )
        ])
    buttons.append([
        InlineKeyboardButton(
            "Back to Plans",
            callback_data="show_premium",
        )
    ])
    return buttons


def _payment_method_text(days, stars, inr_price, settings):
    manual_methods = manual_payment_method_names(days, settings)
    methods = []
    if settings["stars_payments_enabled"]:
        methods.append(
            f"Telegram Stars - {stars} Stars, activated instantly"
        )
    methods.extend(manual_methods)
    if (
        not manual_methods
        and PAYMENT_WEBSITE.startswith(("https://", "http://"))
    ):
        methods.append("External payment portal - manual verification")
    method_text = "\n".join(f"• {method}" for method in methods)
    return (
        "<b>Complete Your Payment</b>\n\n"
        f"<b>Selected plan:</b> {days} days Premium\n"
        f"<b>Telegram Stars:</b> {stars}\n"
        f"<b>UPI price:</b> INR {inr_price}\n\n"
        "<b>Choose a payment method:</b>\n"
        f"{method_text}"
    )


async def handle_buy_premium_callback(client, query):
    """Show available payment methods for the selected Premium plan."""
    days = int(query.data.split("_")[2])
    settings = await get_global_settings()
    if not settings["premium_purchases_enabled"]:
        await query.answer(
            "Premium purchases are temporarily disabled.",
            show_alert=True,
        )
        return
    stars = get_stars_price(settings, days)

    if not stars:
        return await query.answer("Invalid plan!", show_alert=True)

    inr_price = get_inr_price(settings, days)
    buttons = _payment_method_buttons(days, settings)
    try:
        await query.message.edit_text(
            _payment_method_text(days, stars, inr_price, settings),
            reply_markup=InlineKeyboardMarkup(buttons),
            disable_web_page_preview=True,
        )
    except MessageNotModified:
        logger.debug("Premium view is already current")

async def handle_confirm_premium_callback(client, query):
    """Handle confirmed premium purchase - send Telegram Stars invoice"""
    days = int(query.data.split("_")[2])
    settings = await get_global_settings()
    if not settings["premium_purchases_enabled"]:
        await query.answer(
            "Premium purchases are temporarily disabled.",
            show_alert=True,
        )
        return
    if not settings["stars_payments_enabled"]:
        await query.answer(
            "Telegram Stars payments are disabled.",
            show_alert=True,
        )
        return
    stars = get_stars_price(settings, days)
    user_id = query.from_user.id
    download_benefit = describe_daily_limit(
        settings["premium_daily_limit"]
    ).lower()
    
    if not stars:
        return await query.answer("Invalid plan!", show_alert=True)
    
    await _clear_previous_invoice(client, query, user_id)
    invoice = PremiumInvoice(user_id, days, stars, download_benefit)
    try:
        invoice_msg = await _send_premium_invoice(client, invoice)
        last_invoice_messages[user_id] = invoice_msg.id
        await query.answer()
    except (KeyError, PyMongoError, RPCError, TypeError, ValueError):
        logger.exception("Failed to create Telegram Stars invoice")
        await query.answer(
            "Error creating payment. Please try again later.",
            show_alert=True,
        )

async def handle_pre_checkout_handler(client, query: PreCheckoutQuery):
    """Handle pre-checkout query - approve the payment"""
    try:
        purchase = _parse_premium_payload(query.invoice_payload)
        settings = await get_global_settings()
        configured_price = get_stars_price(settings, purchase.days)
        expected_price = purchase.stars or configured_price
        payload_price_is_current = (
            purchase.stars is None or purchase.stars == configured_price
        )
        is_valid = (
            settings["premium_purchases_enabled"]
            and settings["stars_payments_enabled"]
            and payload_price_is_current
            and purchase.user_id == query.from_user.id
            and query.currency == "XTR"
            and query.total_amount == expected_price
        )
        await query.answer(
            ok=is_valid,
            error_message=None if is_valid else "Invalid payment request",
        )
    except (KeyError, PyMongoError, RPCError, TypeError, ValueError):
        logger.exception("Failed during Telegram Stars pre-checkout")
        await query.answer(ok=False, error_message="Payment verification failed")

def _validate_successful_payment(payment, purchase, user_id):
    expected_stars = purchase.stars
    charge_id = str(payment.telegram_payment_charge_id).strip()
    is_valid = (
        purchase.user_id == user_id
        and payment.currency == "XTR"
        and expected_stars is not None
        and payment.total_amount == expected_stars
        and bool(charge_id)
    )
    if not is_valid:
        raise ValueError("Invalid successful Telegram Stars payment")
    return charge_id


def _payment_success_text(purchase, activation, download_benefit):
    return f"""
🎉 <b>Payment Successful!</b>

⭐ <b>Premium Activated!</b>
📅 <b>Duration:</b> {purchase.days} day{'s' if purchase.days > 1 else ''}
⏰ <b>Valid Until:</b> {activation.expires_at.strftime('%d %B %Y, %I:%M %p')}
💰 <b>Stars Paid:</b> {purchase.stars} ⭐

<b>You now have:</b>
✅ {download_benefit}
✅ Direct access to all files

<i>Thank you for supporting us! ❤️</i>

Use /mystatus to check your premium status anytime.
"""


async def handle_successful_payment_handler(client, message):
    """Validate and idempotently fulfill a Telegram Stars payment."""
    try:
        payment = message.successful_payment
        purchase = _parse_premium_payload(payment.invoice_payload)
        user_id = message.from_user.id
        if purchase.stars is None:
            settings = await get_global_settings()
            purchase = PremiumPurchase(
                purchase.user_id,
                purchase.days,
                get_stars_price(settings, purchase.days),
            )
        charge_id = _validate_successful_payment(payment, purchase, user_id)
        activation = await db.activate_star_payment({
            "telegram_payment_charge_id": charge_id,
            "provider_payment_charge_id": str(
                getattr(payment, "provider_payment_charge_id", "") or ""
            ),
            "user_id": user_id,
            "days": purchase.days,
            "stars": int(payment.total_amount),
            "currency": str(payment.currency),
            "invoice_payload": str(payment.invoice_payload),
        })
        if activation.was_applied:
            _track_payment_success(user_id, payment, purchase.days)
        settings = await get_global_settings()
        text = _payment_success_text(
            purchase,
            activation,
            describe_daily_limit(settings["premium_daily_limit"]),
        )
        await message.reply_text(text)
        logger.info(
            "Premium payment fulfilled: user=%s days=%s newly_applied=%s",
            user_id,
            purchase.days,
            activation.was_applied,
        )
    except (KeyError, PyMongoError, RPCError, TypeError, ValueError):
        logger.exception("Failed to process successful premium payment")
        await message.reply_text(
            "Error processing payment. Please contact support with your "
            "payment receipt."
        )
