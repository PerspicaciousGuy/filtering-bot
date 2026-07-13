import binascii

from pyrogram import enums
from pyrogram.errors import RPCError
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from Script import script
from database.users_chats_db import db
from info import (
    AUTH_CHANNEL,
    REQUEST_TO_JOIN_MODE,
    TRY_AGAIN_BTN,
)
from utils import is_subscribed, temp


SUBSCRIPTION_ERRORS = (
    binascii.Error,
    KeyError,
    RPCError,
    TypeError,
    UnicodeError,
    ValueError,
)


async def _invite_link(client):
    if REQUEST_TO_JOIN_MODE:
        return await client.create_chat_invite_link(
            chat_id=int(AUTH_CHANNEL),
            creates_join_request=True,
        )
    return await client.create_chat_invite_link(int(AUTH_CHANNEL))


def _retry_button(payload):
    try:
        prefix, file_id = payload.split("_", 1)
        return InlineKeyboardButton(
            script.TRY_AGAIN_BTN,
            callback_data=f"checksub#{prefix}#{file_id}",
        )
    except (IndexError, ValueError):
        return InlineKeyboardButton(
            script.TRY_AGAIN_BTN,
            url=f"https://t.me/{temp.U_NAME}?start={payload}",
        )


def _subscription_buttons(invite_link, payload):
    buttons = [[InlineKeyboardButton(
        script.BACKUP_CHANNEL_BTN,
        url=invite_link.invite_link,
    )]]
    if payload == "subscribe":
        return buttons
    if not REQUEST_TO_JOIN_MODE or TRY_AGAIN_BTN:
        buttons.append([_retry_button(payload)])
    return buttons


async def _subscription_text(message, payload):
    if not REQUEST_TO_JOIN_MODE or TRY_AGAIN_BTN:
        return script.BACKUP_CHANNEL_NOT_JOINED
    await db.set_msg_command(message.from_user.id, com=payload)
    return script.BACKUP_CHANNEL_NOT_JOINED_2


async def enforce_subscription(client, message):
    """Return true after handling an unsubscribed deep-link request."""
    if not AUTH_CHANNEL or await is_subscribed(client, message):
        return False
    try:
        invite_link = await _invite_link(client)
    except SUBSCRIPTION_ERRORS:
        await message.reply_text(script.FORCE_SUB_ADMIN_ERROR)
        return True

    payload = message.command[1]
    try:
        await client.send_message(
            chat_id=message.from_user.id,
            text=await _subscription_text(message, payload),
            reply_markup=InlineKeyboardMarkup(
                _subscription_buttons(invite_link, payload)
            ),
            parse_mode=enums.ParseMode.MARKDOWN,
        )
    except SUBSCRIPTION_ERRORS:
        await message.reply_text(script.FORCE_SUB_ERROR)
    return True
