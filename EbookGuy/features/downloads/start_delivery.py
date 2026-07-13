import asyncio
import base64
import binascii
import logging
from dataclasses import dataclass

from pyrogram.errors import RPCError
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from Script import script
from database.ia_filterdb import get_file_details
from EbookGuy.features.downloads.callbacks import get_file_again_markup
from EbookGuy.features.downloads.limits import (
    check_and_increment_download,
    send_auto_delete_message,
    send_download_limit_message,
)
from EbookGuy.shared.formatting import format_file_caption
from info import FREE_DAILY_LIMIT
from utils import get_size, temp


logger = logging.getLogger(__name__)
FILE_PREFIXES = {"file", "filep"}
CONVERTIBLE_FORMATS = {"epub", "pdf", "mobi", "azw", "azw3"}


@dataclass(frozen=True)
class FileView:
    prefix: str
    file_id: str
    file: dict


DELIVERY_ERRORS = (
    binascii.Error,
    KeyError,
    RPCError,
    TypeError,
    UnicodeError,
    ValueError,
)


def _parse_payload(data):
    if "_" not in data:
        return "", data
    return tuple(data.split("_", 1))


def _download_count_text(is_premium, count):
    if is_premium:
        return script.DOWNLOAD_COUNT_PREMIUM
    return script.DOWNLOAD_COUNT.format(count, FREE_DAILY_LIMIT)


async def _download_permission(message):
    state = await check_and_increment_download(message.from_user.id)
    can_download, is_premium, count, cooldown = state
    if not can_download:
        await send_download_limit_message(message, is_premium, cooldown)
        return None
    return is_premium, count


async def send_bulk_files(client, message, payload):
    prefix, file_key = _parse_payload(payload)
    files = temp.GETALL.get(file_key)
    if not files:
        await message.reply(script.NO_FILE_EXIST)
        return
    permission = await _download_permission(message)
    if permission is None:
        return
    sent_messages = []
    for file in files:
        sent_messages.append(await client.send_cached_media(
            chat_id=message.from_user.id,
            file_id=file["file_id"],
            protect_content=prefix == "allfilesp",
            reply_markup=None,
        ))
    is_premium, count = permission
    await message.reply_text(_download_count_text(is_premium, count))
    await send_auto_delete_message(client, message.from_user.id, sent_messages)


def _decode_legacy_payload(payload):
    padded = payload + "=" * (-len(payload) % 4)
    decoded = base64.urlsafe_b64decode(padded).decode("ascii")
    return decoded.split("_", 1)


async def _send_legacy_file(client, message, payload):
    prefix, file_id = _decode_legacy_payload(payload)
    permission = await _download_permission(message)
    if permission is None:
        return
    sent = await client.send_cached_media(
        chat_id=message.from_user.id,
        file_id=file_id,
        protect_content=prefix == "filep",
        reply_markup=None,
    )
    media = getattr(sent, sent.media.value)
    caption = format_file_caption(media.file_name, get_size(media.file_size))
    await sent.edit_caption(caption=caption or f"<code>{media.file_name}</code>")
    is_premium, count = permission
    count_message = await sent.reply(
        _download_count_text(is_premium, count)
        + "\n\n"
        + script.IMPORTANT_DELETE_MSG
    )
    await asyncio.sleep(600)
    await sent.delete()
    await count_message.edit_text(
        script.FILE_DELETED_BTN,
        reply_markup=get_file_again_markup(file_id),
    )


def _file_action_markup(prefix, file_id, title):
    buttons = [[InlineKeyboardButton(
        "\U0001f4e5 Download",
        callback_data=f"download_book#{prefix}#{file_id}",
    )]]
    detected_format = next(
        (word for word in reversed(title.lower().split())
         if word in CONVERTIBLE_FORMATS),
        None,
    )
    if detected_format:
        buttons.append([InlineKeyboardButton(
            "\U0001f504 Convert Format",
            callback_data=f"convert_menu#{prefix}#{file_id}",
        )])
    return InlineKeyboardMarkup(buttons)


async def _show_file_details(message, view):
    title = view.file["file_name"]
    clean_title = " ".join(
        word for word in title.split()
        if not word.startswith("[") and not word.startswith("@")
    )
    await message.reply_text(
        text=(
            f"<b>\U0001f4d6 {clean_title}</b>\n"
            f"<b>\U0001f4e6 Size:</b> {get_size(view.file['file_size'])}"
        ),
        reply_markup=_file_action_markup(view.prefix, view.file_id, title),
    )


async def send_file_payload(client, message, payload):
    prefix, file_id = _parse_payload(payload)
    file = await get_file_details(file_id)
    if file:
        await _show_file_details(message, FileView(prefix, file_id, file))
        return
    try:
        await _send_legacy_file(client, message, payload)
    except DELIVERY_ERRORS:
        logger.exception("Legacy direct-download fallback failed")
        await message.reply(script.NO_FILE_EXIST)


async def handle_start_payload(client, message, payload):
    """Route a validated start payload to its download flow."""
    prefix, _ = _parse_payload(payload)
    if payload.startswith("all"):
        await send_bulk_files(client, message, payload)
    elif prefix in FILE_PREFIXES:
        await send_file_payload(client, message, payload)
