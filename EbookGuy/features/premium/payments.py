import logging
from dataclasses import dataclass

from pyrogram.errors import MessageNotModified, RPCError
from pyrogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    LabeledPrice,
    PreCheckoutQuery,
)
from pymongo.errors import PyMongoError
from database.users_chats_db import db
from EbookGuy.shared.global_settings import (
    describe_daily_limit,
    get_global_settings,
)
from EbookGuy.features.premium.plans import (
    PLAN_DAYS,
    get_inr_price,
    get_stars_price,
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
        payload=f"premium_{invoice.days}_{invoice.user_id}",
        currency="XTR",
        prices=[LabeledPrice(
            label=f"{invoice.days} Days Premium",
            amount=invoice.stars,
        )],
    )


def _payment_method_buttons(days, settings):
    buttons = [
        [InlineKeyboardButton(
            "⭐ Pay with Telegram Stars",
            callback_data=f"confirm_premium_{days}",
        )],
        [InlineKeyboardButton("💳 Go to Payment Portal", url=PAYMENT_WEBSITE)],
        [InlineKeyboardButton("« Back to Plans", callback_data="show_premium")],
    ]
    if not settings["stars_payments_enabled"]:
        buttons.pop(0)
    return buttons


async def handle_buy_premium_callback(client, query):
    """Handle premium purchase button click - show payment method options"""
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
    
    # Get INR price if available
    inr_price = get_inr_price(settings, days)
    plan_name = f"{days} Day" if days == 7 else f"{days} Day{'s' if days > 1 else ''}"
    stars_method = (
        "⭐ <b>Telegram Stars</b> - Instant payment within the bot"
        if settings["stars_payments_enabled"]
        else "Telegram Stars payments are temporarily unavailable."
    )
    
    text = f"""
<b>💳 Complete Your Payment</b>

📦 <b>Selected Plan:</b> {plan_name} Premium
⭐ <b>Price:</b> {stars} Telegram Stars (~${stars/100:.2f})
💰 <b>INR Price:</b> ₹{inr_price}

<b>Choose your preferred payment method:</b>

{stars_method}
💳 <b>Other Methods</b> - UPI, Crypto, Binance Pay on our portal
"""
    
    buttons = _payment_method_buttons(days, settings)
    try:
        await query.message.edit_text(
            text,
            reply_markup=InlineKeyboardMarkup(buttons),
            disable_web_page_preview=True
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
        await query.answer("Error creating payment. Please try again later.", show_alert=True)

async def handle_pre_checkout_handler(client, query: PreCheckoutQuery):
    """Handle pre-checkout query - approve the payment"""
    try:
        # Parse payload to verify
        payload = query.invoice_payload
        if payload.startswith("premium_"):
            parts = payload.split("_")
            if len(parts) >= 3:
                days = int(parts[1])
                user_id = int(parts[2])
                
                settings = await get_global_settings()
                expected_price = get_stars_price(settings, days)
                is_valid = (
                    settings["premium_purchases_enabled"]
                    and settings["stars_payments_enabled"]
                    and days in PLAN_DAYS
                    and user_id == query.from_user.id
                    and query.currency == "XTR"
                    and query.total_amount == expected_price
                )
                if is_valid:
                    await query.answer(ok=True)
                    return
        
        await query.answer(ok=False, error_message="Invalid payment request")
    except (KeyError, PyMongoError, RPCError, TypeError, ValueError):
        logger.exception("Failed during Telegram Stars pre-checkout")
        await query.answer(ok=False, error_message="Payment verification failed")

async def handle_successful_payment_handler(client, message):
    """Handle successful payment - activate premium"""
    try:
        payment = message.successful_payment
        payload = payment.invoice_payload
        
        if payload.startswith("premium_"):
            parts = payload.split("_")
            days = int(parts[1])
            user_id = message.from_user.id
            payload_user_id = int(parts[2])
            if days not in PLAN_DAYS or payload_user_id != user_id:
                raise ValueError("Invalid successful payment payload")
            
            # Activate/extend premium
            new_expiry = await db.set_premium(user_id, days)
            
            if new_expiry:
                settings = await get_global_settings()
                download_benefit = describe_daily_limit(
                    settings["premium_daily_limit"]
                )
                text = f"""
🎉 <b>Payment Successful!</b>

⭐ <b>Premium Activated!</b>
📅 <b>Duration:</b> {days} day{'s' if days > 1 else ''}
⏰ <b>Valid Until:</b> {new_expiry.strftime('%d %B %Y, %I:%M %p')}
💰 <b>Stars Paid:</b> {payment.total_amount} ⭐

<b>You now have:</b>
✅ {download_benefit}
✅ Direct access to all files

<i>Thank you for supporting us! ❤️</i>

Use /mystatus to check your premium status anytime.
"""
                await message.reply_text(text)
                
                # Log the payment
                logger.info(f"Premium activated: User {user_id}, {days} days, {payment.total_amount} stars")
            else:
                await message.reply_text("❌ Error activating premium. Please contact support.")
    except (KeyError, PyMongoError, RPCError, TypeError, ValueError):
        logger.exception("Failed to process successful premium payment")
        await message.reply_text("Error processing payment. Please contact support with your payment receipt.")
