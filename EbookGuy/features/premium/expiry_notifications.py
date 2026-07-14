"""Background notifications for premium subscriptions nearing expiry."""

import asyncio
import datetime
import logging

from pyrogram.errors import PeerIdInvalid, RPCError, UserIsBlocked
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from pymongo.errors import PyMongoError

from database.users_chats_db import db
from EbookGuy.shared.global_settings import get_global_settings


logger = logging.getLogger(__name__)
EXPIRY_WARNING_HOURS = 24
EXPIRY_POLL_SECONDS = 3600


def _expiry_markup(support_url):
    return InlineKeyboardMarkup(
        [
            [InlineKeyboardButton("Renew Premium", callback_data="show_premium")],
            [InlineKeyboardButton("Contact Support", url=str(support_url))],
        ]
    )


async def _notify_expiring_user(client, user, settings):
    expiry = user.get("premium_expiry")
    if not expiry or user.get("premium_expiry_notified_for") == expiry:
        return
    try:
        await client.send_message(
            chat_id=int(user["id"]),
            text=(
                "<b>Your Premium access expires soon.</b>\n\n"
                f"Expiry: <code>{expiry.strftime('%d %B %Y, %I:%M %p')}</code>"
            ),
            reply_markup=_expiry_markup(settings["support_url"]),
        )
    except (PeerIdInvalid, UserIsBlocked):
        await db.mark_premium_expiry_notified(user["id"], expiry)
        return
    except RPCError:
        logger.exception("Failed to send premium expiry notification")
        return
    await db.mark_premium_expiry_notified(user["id"], expiry)


async def _send_expiry_notifications(client):
    settings = await get_global_settings()
    if not settings["premium_expiry_notifications_enabled"]:
        return
    cutoff = datetime.datetime.now() + datetime.timedelta(
        hours=EXPIRY_WARNING_HOURS
    )
    async for user in db.get_expiring_premium_users(cutoff):
        await _notify_expiring_user(client, user, settings)


async def run_premium_expiry_notifier(client):
    """Poll for expiring premium subscriptions until the bot stops."""
    is_index_ready = False
    while True:
        try:
            if not is_index_ready:
                await db.ensure_premium_expiry_index()
                is_index_ready = True
            await _send_expiry_notifications(client)
        except PyMongoError:
            logger.exception("Failed to query premium expiry notifications")
        await asyncio.sleep(EXPIRY_POLL_SECONDS)


__all__ = ["run_premium_expiry_notifier"]
