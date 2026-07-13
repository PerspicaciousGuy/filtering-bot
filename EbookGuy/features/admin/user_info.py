import logging
import os

from pyrogram import enums
from pyrogram.errors import RPCError
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from utils import extract_user


logger = logging.getLogger(__name__)


def _close_markup():
    return InlineKeyboardMarkup([[
        InlineKeyboardButton(
            "\U0001f510 Close",
            callback_data="close_data",
        )
    ]])


def _user_info_text(user):
    last_name = user.last_name or "<b>None</b>"
    username = user.username or "<b>None</b>"
    dc_id = user.dc_id or "[User Doesn't Have A Valid DP]"
    return (
        f"<b>\u27b2First Name:</b> {user.first_name}\n"
        f"<b>\u27b2Last Name:</b> {last_name}\n"
        f"<b>\u27b2Telegram ID:</b> <code>{user.id}</code>\n"
        f"<b>\u27b2Data Centre:</b> <code>{dc_id}</code>\n"
        f"<b>\u27b2User Name:</b> @{username}\n"
        f"<b>\u27b2User Link:</b> "
        f"<a href='tg://user?id={user.id}'><b>Click Here</b></a>\n"
    )


async def _send_user_info(client, message, user):
    text = _user_info_text(user)
    reply_markup = _close_markup()
    if not user.photo:
        await message.reply_text(
            text=text,
            reply_markup=reply_markup,
            quote=True,
            parse_mode=enums.ParseMode.HTML,
            disable_notification=True,
        )
        return
    local_photo = await client.download_media(message=user.photo.big_file_id)
    try:
        await message.reply_photo(
            photo=local_photo,
            quote=True,
            reply_markup=reply_markup,
            caption=text,
            parse_mode=enums.ParseMode.HTML,
            disable_notification=True,
        )
    finally:
        os.remove(local_photo)


async def handle_show_id(client, message):
    user = message.from_user
    await message.reply_text(
        f"<b>\u27b2 First Name:</b> {user.first_name}\n"
        f"<b>\u27b2 Last Name:</b> {user.last_name or ''}\n"
        f"<b>\u27b2 Username:</b> {user.username}\n"
        f"<b>\u27b2 Telegram ID:</b> <code>{message.chat.id}</code>\n"
        f"<b>\u27b2 Data Centre:</b> <code>{user.dc_id or ''}</code>",
        quote=True,
    )


async def handle_user_info(client, message):
    status_message = await message.reply_text("\x60Fetching user info...\x60")
    await status_message.edit("\x60Processing user info...\x60")
    user_id, _ = extract_user(message)
    try:
        user = await client.get_users(user_id)
    except (RPCError, TypeError, ValueError):
        logger.exception("Failed to fetch user info")
        await status_message.edit("Could not fetch user info right now.")
        return
    if user is None:
        await status_message.edit("no valid user_id / message specified")
        return
    await _send_user_info(client, message, user)
    await status_message.delete()
