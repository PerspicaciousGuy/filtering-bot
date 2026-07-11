import logging

from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, PreCheckoutQuery, LabeledPrice
from pyrogram.errors import MessageNotModified
from database.users_chats_db import db
from info import PREMIUM_PRICES, PREMIUM_PRICES_INR, PAYMENT_WEBSITE
from Script import script

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
last_invoice_messages = {}

async def handle_buy_premium_callback(client, query):
    """Handle premium purchase button click - show payment method options"""
    days = int(query.data.split("_")[2])
    stars = PREMIUM_PRICES.get(days)
    
    if not stars:
        return await query.answer("Invalid plan!", show_alert=True)
    
    # Get INR price if available
    inr_price = PREMIUM_PRICES_INR.get(days, "")
    plan_name = f"{days} Day" if days == 7 else f"{days} Day{'s' if days > 1 else ''}"
    
    text = f"""
<b>💳 Complete Your Payment</b>

📦 <b>Selected Plan:</b> {plan_name} Premium
⭐ <b>Price:</b> {stars} Telegram Stars (~${stars/100:.2f})
💰 <b>INR Price:</b> ₹{inr_price}

<b>Choose your preferred payment method:</b>

⭐ <b>Telegram Stars</b> - Instant payment within the bot
💳 <b>Other Methods</b> - UPI, Crypto, Binance Pay on our portal
"""
    
    buttons = [
        [InlineKeyboardButton(f"⭐ Pay with Telegram Stars", callback_data=f"confirm_premium_{days}")],
        [InlineKeyboardButton("💳 Go to Payment Portal", url=PAYMENT_WEBSITE)],
        [InlineKeyboardButton("« Back to Plans", callback_data="show_premium")]
    ]
    
    try:
        await query.message.edit_text(
            text,
            reply_markup=InlineKeyboardMarkup(buttons),
            disable_web_page_preview=True
        )
    except MessageNotModified:
        pass

async def handle_confirm_premium_callback(client, query):
    """Handle confirmed premium purchase - send Telegram Stars invoice"""
    days = int(query.data.split("_")[2])
    stars = PREMIUM_PRICES.get(days)
    user_id = query.from_user.id
    
    if not stars:
        return await query.answer("Invalid plan!", show_alert=True)
    
    # Delete previous invoice message if exists
    if user_id in last_invoice_messages:
        try:
            await client.delete_messages(user_id, last_invoice_messages[user_id])
        except Exception:
            pass
    
    # Delete the confirmation message
    try:
        await query.message.delete()
    except Exception:
        pass
    
    # Create invoice for Telegram Stars payment
    try:
        invoice_msg = await client.send_invoice(
            chat_id=user_id,
            title=f"Premium - {days} Day{'s' if days > 1 else ''}",
            description=f"Get {days} day{'s' if days > 1 else ''} of Premium access with unlimited downloads. If you already have Premium, this will extend your existing plan.",
            payload=f"premium_{days}_{user_id}",
            currency="XTR",  # Telegram Stars
            prices=[LabeledPrice(label=f"{days} Day{'s' if days > 1 else ''} Premium", amount=stars)]
        )
        # Track this invoice message
        last_invoice_messages[user_id] = invoice_msg.id
        await query.answer()
    except Exception:
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
                
                if days in PREMIUM_PRICES and user_id == query.from_user.id:
                    await query.answer(ok=True)
                    return
        
        await query.answer(ok=False, error_message="Invalid payment request")
    except Exception:
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
            
            # Activate/extend premium
            new_expiry = await db.set_premium(user_id, days)
            
            if new_expiry:
                text = f"""
🎉 <b>Payment Successful!</b>

⭐ <b>Premium Activated!</b>
📅 <b>Duration:</b> {days} day{'s' if days > 1 else ''}
⏰ <b>Valid Until:</b> {new_expiry.strftime('%d %B %Y, %I:%M %p')}
💰 <b>Stars Paid:</b> {payment.total_amount} ⭐

<b>You now have:</b>
✅ Unlimited downloads
✅ No daily limits
✅ Direct access to all files

<i>Thank you for supporting us! ❤️</i>

Use /mystatus to check your premium status anytime.
"""
                await message.reply_text(text)
                
                # Log the payment
                logger.info(f"Premium activated: User {user_id}, {days} days, {payment.total_amount} stars")
            else:
                await message.reply_text("❌ Error activating premium. Please contact support.")
    except Exception:
        logger.exception("Failed to process successful premium payment")
        await message.reply_text("Error processing payment. Please contact support with your payment receipt.")
