import asyncio
import datetime
import logging
from dataclasses import dataclass

from pyrogram.errors import RPCError
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from Script import script
from database.users_chats_db import db
from EbookGuy.shared.global_settings import get_global_settings


BYTES_PER_MB = 1024 * 1024


@dataclass(frozen=True)
class DownloadAccess:
    """Result of evaluating and optionally consuming a download allowance."""

    is_allowed: bool
    is_premium: bool
    count: int
    daily_limit: int
    cooldown_remaining: int = 0
    file_size_limit_mb: int = 0
    denial_reason: str = ""


def _premium_upgrade_markup():
    return InlineKeyboardMarkup(
        [[
            InlineKeyboardButton(
                "\u2b50 Upgrade to Premium",
                callback_data="show_premium",
            )
        ]]
    )


def _limit_message(access):
    if access.denial_reason == "file_size":
        return (
            "<b>File Too Large</b>\n\n"
            f"Your maximum file size is <b>{access.file_size_limit_mb} MB</b>."
        )
    if access.cooldown_remaining > 0:
        return (
            "<b>Rate Limited</b>\n\n"
            f"Please wait <b>{access.cooldown_remaining} seconds</b> "
            "before your next download."
        )
    plan = "premium" if access.is_premium else "free"
    return (
        "<b>Daily Limit Reached</b>\n\n"
        f"You have reached the {plan} limit of "
        f"<b>{access.daily_limit} download(s) per day</b>."
    )


async def send_download_limit_message(message, access):
    """Reply with the applicable rich download-denial message."""
    await message.reply_text(
        text=_limit_message(access),
        reply_markup=(
            None if access.is_premium else _premium_upgrade_markup()
        ),
    )


async def answer_download_limit_callback(query, access):
    """Answer a callback with the applicable download-denial response."""
    await query.answer(
        _limit_message(access).replace("<b>", "").replace("</b>", ""),
        show_alert=True,
    )


def _size_denial(is_premium, file_size, limits):
    daily_limit, size_limit = limits
    if size_limit <= 0 or file_size <= size_limit * BYTES_PER_MB:
        return None
    return DownloadAccess(
        False,
        is_premium,
        0,
        daily_limit,
        file_size_limit_mb=size_limit,
        denial_reason="file_size",
    )


async def _check_premium_download(user_id, file_size, settings):
    daily_limit = int(settings["premium_daily_limit"])
    size_limit = int(settings["premium_max_file_size_mb"])
    denied = _size_denial(True, file_size, (daily_limit, size_limit))
    if denied:
        return denied
    cooldown = int(settings["premium_download_cooldown_seconds"])
    last_download = await db.get_user_last_download_time(user_id)
    if last_download and cooldown > 0:
        elapsed = (datetime.datetime.now() - last_download).total_seconds()
        if elapsed < cooldown:
            return DownloadAccess(
                False, True, 0, daily_limit, cooldown - int(elapsed)
            )
    current = await db.get_daily_downloads(user_id)
    if daily_limit > 0 and current >= daily_limit:
        return DownloadAccess(False, True, current, daily_limit)
    count = await db.increment_downloads(user_id)
    await db.set_user_last_download_time(user_id)
    return DownloadAccess(True, True, count, daily_limit)


async def _check_free_download(user_id, file_size, settings):
    daily_limit = int(settings["free_daily_limit"])
    size_limit = int(settings["free_max_file_size_mb"])
    denied = _size_denial(False, file_size, (daily_limit, size_limit))
    if denied:
        return denied
    current = await db.get_daily_downloads(user_id)
    if daily_limit > 0 and current >= daily_limit:
        return DownloadAccess(False, False, current, daily_limit)
    count = await db.increment_downloads(user_id)
    return DownloadAccess(True, False, count, daily_limit)


async def check_and_increment_download(user_id, file_size=0):
    """Check the user's limits, increment an allowed download, and return its state."""
    settings = await get_global_settings()
    is_premium, _ = await db.get_premium_status(user_id)
    if is_premium:
        return await _check_premium_download(user_id, file_size, settings)
    return await _check_free_download(user_id, file_size, settings)


def download_count_text(access):
    """Format the consumed daily allowance after a successful download."""
    limit = access.daily_limit or "Unlimited"
    return f"<b>Downloads today:</b> <code>{access.count}/{limit}</code>"


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
