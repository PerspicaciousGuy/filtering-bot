import asyncio
import logging
import datetime

from pyrogram.errors import RPCError
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from Script import script
from database.users_chats_db import db
from info import FREE_DAILY_LIMIT, PREMIUM_DAILY_LIMIT, PREMIUM_DOWNLOAD_COOLDOWN


def _premium_upgrade_markup():
    return InlineKeyboardMarkup(
        [[
            InlineKeyboardButton(
                "\u2b50 Upgrade to Premium",
                callback_data="show_premium",
            )
        ]]
    )


async def send_download_limit_message(message, is_premium, cooldown):
    """Reply with the applicable rich download-denial message."""
    if is_premium and cooldown > 0:
        await message.reply_text(
            f"\u23f1\ufe0f <b>Rate Limited</b>\n\n"
            f"Please wait <b>{cooldown} seconds</b> before your next download.\n\n"
            f"<i>Premium users can download {PREMIUM_DAILY_LIMIT} books/day "
            f"with {PREMIUM_DOWNLOAD_COOLDOWN} second gaps.</i>"
        )
        return
    if is_premium:
        await message.reply_text(
            f"\U0001f4da <b>Daily Limit Reached</b>\n\n"
            f"You have reached your premium limit of {PREMIUM_DAILY_LIMIT} "
            "downloads today.\n\nLimit resets at midnight."
        )
        return
    await message.reply_text(
        text=(
            "\U0001f4da <b>Daily Limit Reached</b>\n\n"
            f"Free users can download <b>{FREE_DAILY_LIMIT} book(s) per day</b>.\n\n"
            f"Upgrade to premium for <b>{PREMIUM_DAILY_LIMIT} downloads/day</b>!"
        ),
        reply_markup=_premium_upgrade_markup(),
    )


async def answer_download_limit_callback(query, is_premium, cooldown):
    """Answer a callback with the applicable download-denial response."""
    if is_premium and cooldown > 0:
        await query.answer(
            f"\u23f1\ufe0f Wait {cooldown}s before next download.",
            show_alert=True,
        )
        return
    if is_premium:
        await query.answer(
            f"\U0001f4da Daily limit reached ({PREMIUM_DAILY_LIMIT}/day). "
            "Resets at midnight.",
            show_alert=True,
        )
        return
    await query.message.edit_text(
        text=(
            "\U0001f4da <b>Daily Limit Reached</b>\n\n"
            f"Free users can download <b>{FREE_DAILY_LIMIT} book(s) per day</b>.\n\n"
            f"Upgrade to premium for <b>{PREMIUM_DAILY_LIMIT} downloads/day</b>!"
        ),
        reply_markup=_premium_upgrade_markup(),
    )


async def check_and_increment_download(user_id):
    """Check the user's limits, increment an allowed download, and return its state."""
    is_premium, _ = await db.get_premium_status(user_id)

    if is_premium:
        last_download = await db.get_user_last_download_time(user_id)
        if last_download:
            time_since_download = (
                datetime.datetime.now() - last_download
            ).total_seconds()
            if time_since_download < PREMIUM_DOWNLOAD_COOLDOWN:
                remaining = PREMIUM_DOWNLOAD_COOLDOWN - int(time_since_download)
                return False, True, 0, remaining

        current_downloads = await db.get_daily_downloads(user_id)
        if current_downloads >= PREMIUM_DAILY_LIMIT:
            return False, True, current_downloads, 0

        new_count = await db.increment_downloads(user_id)
        await db.set_user_last_download_time(user_id)
        return True, True, new_count, 0

    current_downloads = await db.get_daily_downloads(user_id)
    if current_downloads >= FREE_DAILY_LIMIT:
        return False, False, current_downloads, 0

    new_count = await db.increment_downloads(user_id)
    return True, False, new_count, 0


async def send_auto_delete_message(client, user_id, filesarr):
    """Send auto-delete warning and delete files after 10 minutes."""
    warning_message = await client.send_message(
        chat_id=user_id,
        text=script.IMPORTANT_DELETE_MSG,
    )
    await asyncio.sleep(600)
    for message in filesarr:
        try:
            await message.delete()
        except RPCError:
            logging.getLogger(__name__).debug(
                "Auto-delete message was already unavailable",
                exc_info=True,
            )
    await warning_message.edit_text(
        "<b>\u2705 Your message is successfully deleted</b>"
    )
