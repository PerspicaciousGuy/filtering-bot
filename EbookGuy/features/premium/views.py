import datetime
import logging

from pyrogram.errors import MessageNotModified
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from database.users_chats_db import db
from info import FREE_DAILY_LIMIT

def get_readable_time(seconds):
    """Convert seconds to readable time format"""
    if seconds < 60:
        return f"{int(seconds)} seconds"
    elif seconds < 3600:
        return f"{int(seconds / 60)} minutes"
    elif seconds < 86400:
        return f"{int(seconds / 3600)} hours"
    else:
        days = int(seconds / 86400)
        hours = int((seconds % 86400) / 3600)
        if hours > 0:
            return f"{days} days, {hours} hours"
        return f"{days} days"

async def handle_premium_command(client, message):
    """Show premium plans and purchase options"""
    user_id = message.from_user.id
    is_premium, expiry = await db.get_premium_status(user_id)
    
    # Build the premium message
    if is_premium and expiry:
        time_left = (expiry - datetime.datetime.now()).total_seconds()
        status_text = f"⭐ <b>Your Premium Status:</b> Active\n⏰ <b>Expires:</b> {expiry.strftime('%d %B %Y, %I:%M %p')}\n⌛ <b>Time Left:</b> {get_readable_time(time_left)}\n\n"
    else:
        status_text = f"📊 <b>Your Status:</b> Free User\n📥 <b>Daily Limit:</b> {FREE_DAILY_LIMIT} downloads/day\n\n"
    
    text = f"""
{status_text}
<b>⭐ Premium Benefits:</b>

✅ <b>Unlimited Downloads</b> - No daily limits
✅ <b>Direct Access</b> - No waiting or ads
✅ <b>Priority Support</b> - Faster responses
✅ <b>Support Development</b> - Help us keep the bot running

<b>ℹ️ Important Information:</b>

📋 <b>Refund Policy:</b>
• Refund only if you sent payment screenshot and we couldn't activate premium
• Send your Telegram username or ID with payment proof
• UPI & Binance Pay eligible for refund
• Crypto payments: No refund but we'll activate your plan

📚 <b>About Premium:</b>
• Premium doesn't guarantee all books are available
• Some books may not be in our database
• Premium removes download limits, not book availability

💡 <i>If you already have a plan, buying again will extend it automatically</i>

<b>Select a plan to continue:</b>
"""
    
    # Create payment buttons - 2 tier pricing
    buttons = [
        [InlineKeyboardButton("🌟 1 Month - $1.99", callback_data="buy_premium_30")],
        [InlineKeyboardButton("⭐ 3 Months - $4.99", callback_data="buy_premium_90")],
        [InlineKeyboardButton("❌ Close", callback_data="close_data")]
    ]
    
    await message.reply_text(
        text,
        reply_markup=InlineKeyboardMarkup(buttons),
        disable_web_page_preview=True
    )

async def handle_my_status_command(client, message):
    """Check user's premium status and download stats"""
    user_id = message.from_user.id
    is_premium, expiry = await db.get_premium_status(user_id)
    daily_downloads = await db.get_daily_downloads(user_id)
    
    if is_premium and expiry:
        time_left = (expiry - datetime.datetime.now()).total_seconds()
        text = f"""
<b>👤 Your Account Status</b>

⭐ <b>Plan:</b> Premium User
📅 <b>Expires:</b> {expiry.strftime('%d %B %Y, %I:%M %p')}
⌛ <b>Time Left:</b> {get_readable_time(time_left)}
📥 <b>Today's Downloads:</b> Unlimited ∞

<i>Thank you for supporting us! ❤️</i>
"""
    else:
        text = f"""
<b>👤 Your Account Status</b>

📊 <b>Plan:</b> Free User
📥 <b>Today's Downloads:</b> {daily_downloads}/{FREE_DAILY_LIMIT}
📈 <b>Remaining:</b> {max(0, FREE_DAILY_LIMIT - daily_downloads)} downloads

<i>Upgrade to Premium for unlimited downloads!</i>
"""
    
    buttons = [[InlineKeyboardButton("⭐ Upgrade to Premium", callback_data="show_premium")]]
    
    if not is_premium:
        await message.reply_text(text, reply_markup=InlineKeyboardMarkup(buttons))
    else:
        await message.reply_text(text)

async def handle_show_premium_callback(client, query):
    """Show premium plans from callback"""
    user_id = query.from_user.id
    is_premium, expiry = await db.get_premium_status(user_id)
    
    if is_premium and expiry:
        time_left = (expiry - datetime.datetime.now()).total_seconds()
        status_text = f"⭐ <b>Your Premium Status:</b> Active\n⏰ <b>Expires:</b> {expiry.strftime('%d %B %Y, %I:%M %p')}\n⌛ <b>Time Left:</b> {get_readable_time(time_left)}\n\n"
    else:
        status_text = f"📊 <b>Your Status:</b> Free User\n📥 <b>Daily Limit:</b> {FREE_DAILY_LIMIT} downloads/day\n\n"
    
    text = f"""
{status_text}
<b>⭐ Premium Benefits:</b>

✅ <b>Unlimited Downloads</b> - No daily limits
✅ <b>Direct Access</b> - No waiting or ads
✅ <b>Priority Support</b> - Faster responses
✅ <b>Support Development</b> - Help us keep the bot running

<b>ℹ️ Important Information:</b>

📋 <b>Refund Policy:</b>
• Refund only if you sent payment screenshot and we couldn't activate premium
• Send your Telegram username or ID with payment proof
• UPI & Binance Pay eligible for refund
• Crypto payments: No refund but we'll activate your plan

📚 <b>About Premium:</b>
• Premium doesn't guarantee all books are available
• Some books may not be in our database
• Premium removes download limits, not book availability

💡 <i>If you already have a plan, buying again will extend it automatically</i>

<b>Choose your plan:</b>
"""
    
    buttons = [
        [InlineKeyboardButton("🌟 1 Month - $1.99", callback_data="buy_premium_30")],
        [InlineKeyboardButton("⭐ 3 Months - $4.99", callback_data="buy_premium_90")],
        [InlineKeyboardButton("❌ Close", callback_data="close_data")]
    ]
    
    try:
        await query.message.edit_text(
            text,
            reply_markup=InlineKeyboardMarkup(buttons),
            disable_web_page_preview=True
        )
    except MessageNotModified:
        logging.getLogger(__name__).debug("Premium view is already current")
