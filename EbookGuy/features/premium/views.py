import datetime
import logging

from pyrogram.errors import MessageNotModified
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from database.users_chats_db import db
from info import FREE_DAILY_LIMIT, PREMIUM_PRICES


logger = logging.getLogger(__name__)


def get_readable_time(seconds):
    """Convert seconds to a compact readable duration."""
    if seconds < 60:
        return f"{int(seconds)} seconds"
    if seconds < 3600:
        return f"{int(seconds / 60)} minutes"
    if seconds < 86400:
        return f"{int(seconds / 3600)} hours"

    days = int(seconds / 86400)
    hours = int((seconds % 86400) / 3600)
    if hours > 0:
        return f"{days} days, {hours} hours"
    return f"{days} days"


def _premium_status_text(is_premium, expiry):
    if is_premium and expiry:
        time_left = (expiry - datetime.datetime.now()).total_seconds()
        return (
            "\u2b50 <b>Your Premium Status:</b> Active\n"
            f"\u23f0 <b>Expires:</b> {expiry.strftime('%d %B %Y, %I:%M %p')}\n"
            f"\u231b <b>Time Left:</b> {get_readable_time(time_left)}\n"
        )
    return (
        "\U0001f4ca <b>Your Status:</b> Free User\n"
        f"\U0001f4e5 <b>Daily Limit:</b> {FREE_DAILY_LIMIT} downloads/day\n"
    )


def _premium_plan_text(is_premium, expiry):
    status_text = _premium_status_text(is_premium, expiry)
    return f"""{status_text}
<b>\u2b50 Premium Benefits:</b>

\u2705 <b>Unlimited Downloads</b> - No daily limits
\u2705 <b>Direct Access</b> - No waiting or ads
\u2705 <b>Priority Support</b> - Faster responses
\u2705 <b>Support Development</b> - Help us keep the bot running

<b>\u2139\ufe0f Important Information:</b>

\U0001f4cb <b>Refund Policy:</b>
\u2022 Refund only if you sent payment screenshot and we couldn't activate premium
\u2022 Send your Telegram username or ID with payment proof
\u2022 UPI & Binance Pay eligible for refund
\u2022 Crypto payments: No refund but we'll activate your plan

\U0001f4da <b>About Premium:</b>
\u2022 Premium doesn't guarantee all books are available
\u2022 Some books may not be in our database
\u2022 Premium removes download limits, not book availability

\U0001f4a1 <i>If you already have a plan, buying again will extend it automatically</i>

<b>Select a plan to continue:</b>"""


def _plan_duration_label(days):
    if days == 30:
        return "1 Month"
    if days == 90:
        return "3 Months"
    return f"{days} Days"


def _premium_plan_markup():
    buttons = [
        [
            InlineKeyboardButton(
                f"\u2b50 {_plan_duration_label(days)} - {stars} Stars",
                callback_data=f"buy_premium_{days}",
            )
        ]
        for days, stars in sorted(PREMIUM_PRICES.items())
    ]
    buttons.append(
        [InlineKeyboardButton("\u274c Close", callback_data="close_data")]
    )
    return InlineKeyboardMarkup(buttons)


def _account_status_text(is_premium, expiry, daily_downloads):
    if is_premium and expiry:
        time_left = (expiry - datetime.datetime.now()).total_seconds()
        return f"""<b>\U0001f464 Your Account Status</b>

\u2b50 <b>Plan:</b> Premium User
\U0001f4c5 <b>Expires:</b> {expiry.strftime('%d %B %Y, %I:%M %p')}
\u231b <b>Time Left:</b> {get_readable_time(time_left)}
\U0001f4e5 <b>Today's Downloads:</b> Unlimited \u221e

<i>Thank you for supporting us! \u2764\ufe0f</i>"""

    remaining = max(0, FREE_DAILY_LIMIT - daily_downloads)
    return f"""<b>\U0001f464 Your Account Status</b>

\U0001f4ca <b>Plan:</b> Free User
\U0001f4e5 <b>Today's Downloads:</b> {daily_downloads}/{FREE_DAILY_LIMIT}
\U0001f4c8 <b>Remaining:</b> {remaining} downloads

<i>Upgrade to Premium for unlimited downloads!</i>"""


async def handle_premium_command(client, message):
    """Show premium plans and purchase options."""
    is_premium, expiry = await db.get_premium_status(message.from_user.id)
    await message.reply_text(
        _premium_plan_text(is_premium, expiry),
        reply_markup=_premium_plan_markup(),
        disable_web_page_preview=True,
    )


async def handle_my_status_command(client, message):
    """Show the user's premium status and daily download usage."""
    user_id = message.from_user.id
    is_premium, expiry = await db.get_premium_status(user_id)
    daily_downloads = await db.get_daily_downloads(user_id)
    reply_markup = None
    if not (is_premium and expiry):
        reply_markup = InlineKeyboardMarkup(
            [[
                InlineKeyboardButton(
                    "\u2b50 Upgrade to Premium",
                    callback_data="show_premium",
                )
            ]]
        )
    await message.reply_text(
        _account_status_text(is_premium, expiry, daily_downloads),
        reply_markup=reply_markup,
    )


async def handle_show_premium_callback(client, query):
    """Edit the current message to show premium plans."""
    is_premium, expiry = await db.get_premium_status(query.from_user.id)
    try:
        await query.message.edit_text(
            _premium_plan_text(is_premium, expiry),
            reply_markup=_premium_plan_markup(),
            disable_web_page_preview=True,
        )
    except MessageNotModified:
        logger.debug("Premium view is already current")
