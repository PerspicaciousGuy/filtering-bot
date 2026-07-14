import asyncio
import logging
import os
from dataclasses import dataclass

from pyrogram.errors import RPCError
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from pymongo.errors import PyMongoError

from database.ia_filterdb import get_file_details
from database.users_chats_db import db
from EbookGuy.features.downloads.limits import (
    auto_delete_notice,
    delete_delivered_messages,
)
from EbookGuy.shared.analytics import track_event
from EbookGuy.shared.formatting import format_file_caption
from EbookGuy.shared.global_settings import get_global_settings
from utils import get_size


logger = logging.getLogger(__name__)
CONVERTIBLE_FORMATS = ("epub", "pdf", "mobi")
PREVIEW_FORMATS = (*CONVERTIBLE_FORMATS, "azw", "azw3")
CONVERSION_TIMEOUT_SECONDS = 120
BYTES_PER_MB = 1024 * 1024


@dataclass(frozen=True)
class ConversionRequest:
    user_id: int
    file_id: str
    source_format: str
    target_format: str
    input_path: str
    output_path: str
    clean_title: str


def _track_conversion_failure(conversion, reason):
    track_event(
        "conversion.failed",
        conversion.user_id,
        reason=reason,
    )


def _detect_format(file_name, formats=PREVIEW_FORMATS):
    words = reversed(file_name.lower().split())
    return next((word for word in words if word in formats), None)


def _clean_title(file_name):
    return " ".join(
        part
        for part in file_name.split()
        if not part.startswith("[") and not part.startswith("@")
    )


async def _run_conversion(input_path, output_path):
    process = await asyncio.create_subprocess_exec(
        "ebook-convert",
        input_path,
        output_path,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    await asyncio.wait_for(
        process.communicate(),
        timeout=CONVERSION_TIMEOUT_SECONDS,
    )
    return os.path.exists(output_path)


async def _deliver_conversion(client, query, conversion):
    settings = await get_global_settings()
    file_name = f"{conversion.clean_title}.{conversion.target_format}"
    fallback_caption = (
        f"<code>{file_name}</code>\n"
        f"<b>Converted:</b> {conversion.source_format.upper()} "
        f"\u2192 {conversion.target_format.upper()}"
    )
    caption = format_file_caption(
        file_name,
        get_size(os.path.getsize(conversion.output_path)),
        fallback_caption,
    ) or fallback_caption
    await query.message.delete()
    sent_message = await client.send_document(
        chat_id=conversion.user_id,
        document=conversion.output_path,
        file_name=file_name,
        caption=caption,
        protect_content=bool(settings["protect_content"]),
    )
    await db.increment_conversions(conversion.user_id)
    track_event(
        "conversion.completed",
        conversion.user_id,
        source_format=conversion.source_format,
        target_format=conversion.target_format,
    )
    daily_limit = int(settings["premium_daily_conversion_limit"])
    remaining = await db.get_remaining_conversions(
        conversion.user_id,
        daily_limit,
    )
    count_text = (
        "\u2705 <b>Conversion complete!</b>\n"
        f"<i>({_remaining_conversion_text(remaining)})</i>"
    )
    if settings["auto_delete_enabled"]:
        count_text += "\n\n" + auto_delete_notice(
            int(settings["auto_delete_delay_seconds"])
        )
    count_message = await sent_message.reply(count_text)
    was_deleted = await delete_delivered_messages((sent_message,), settings)
    if was_deleted:
        await count_message.delete()


def _premium_conversion_markup(prefix, file_id):
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    "\u2b50 Upgrade to Premium",
                    callback_data="show_premium",
                )
            ],
            [
                InlineKeyboardButton(
                    "\u2b05\ufe0f Back",
                    callback_data=f"convert_back#{prefix}#{file_id}",
                )
            ],
        ]
    )


def _conversion_menu_markup(prefix, file_id, source_format):
    buttons = [
        [
            InlineKeyboardButton(
                f"\U0001f4c4 To {target.upper()}",
                callback_data=f"do_convert#{prefix}#{file_id}#{target}",
            )
        ]
        for target in CONVERTIBLE_FORMATS
        if target != source_format
    ]
    buttons.append(
        [
            InlineKeyboardButton(
                "\u2b05\ufe0f Back",
                callback_data=f"convert_back#{prefix}#{file_id}",
            )
        ]
    )
    return InlineKeyboardMarkup(buttons)


def _remaining_conversion_text(remaining):
    if remaining < 0:
        return "Unlimited conversions"
    return f"{remaining} conversion(s) remaining today"


async def _check_conversion_policy(query, file, settings):
    if not settings["downloads_enabled"]:
        await query.answer("Downloads are temporarily disabled.", show_alert=True)
        return False
    if not settings["conversion_enabled"]:
        await query.answer("Conversions are temporarily disabled.", show_alert=True)
        return False
    size_limit = int(settings["max_conversion_size_mb"])
    if size_limit and int(file.get("file_size") or 0) > size_limit * BYTES_PER_MB:
        await query.answer(
            f"Conversion files are limited to {size_limit} MB.",
            show_alert=True,
        )
        return False
    return True


async def _load_conversion(query):
    _, _prefix, file_id, target_format = query.data.split("#", 3)
    file = await get_file_details(file_id)
    if not file:
        await query.answer("File not found.", show_alert=True)
        return None
    settings = await get_global_settings()
    if not await _check_conversion_policy(query, file, settings):
        return None
    source_format = _detect_format(
        file["file_name"],
        CONVERTIBLE_FORMATS,
    )
    if not source_format:
        await query.answer(
            "Could not detect source format.",
            show_alert=True,
        )
        return None
    return ConversionRequest(
        user_id=query.from_user.id,
        file_id=file_id,
        source_format=source_format,
        target_format=target_format,
        input_path=f"/tmp/{file_id}.{source_format}",
        output_path=f"/tmp/{file_id}.{target_format}",
        clean_title=_clean_title(file["file_name"]),
    )


async def _load_conversion_menu_file(query, file_id):
    settings = await get_global_settings()
    file = await get_file_details(file_id)
    if not file:
        await query.answer("File not found.", show_alert=True)
        return None, settings
    if not await _check_conversion_policy(query, file, settings):
        return None, settings
    return file, settings


async def handle_convert_menu_callback(client, query):
    _, prefix, file_id = query.data.split("#", 2)
    file, settings = await _load_conversion_menu_file(query, file_id)
    if file is None:
        return
    is_premium, _ = await db.get_premium_status(query.from_user.id)
    if not is_premium:
        await query.message.edit_text(
            "<b>\U0001f512 Premium Feature</b>\n\n"
            "Converting books between formats is available for "
            "<b>Premium subscribers</b> only.\n\nUpgrade to unlock!",
            reply_markup=_premium_conversion_markup(prefix, file_id),
        )
        return
    daily_limit = int(settings["premium_daily_conversion_limit"])
    remaining = await db.get_remaining_conversions(
        query.from_user.id,
        daily_limit,
    )
    if remaining == 0:
        await query.answer(
            f"Daily conversion limit reached ({daily_limit}/day). "
            "Try again tomorrow!",
            show_alert=True,
        )
        return
    source_format = _detect_format(
        file["file_name"],
        CONVERTIBLE_FORMATS,
    )
    if not source_format:
        await query.answer(
            "Could not detect file format for conversion.",
            show_alert=True,
        )
        return
    await query.message.edit_text(
        "<b>\U0001f504 Convert Format</b>\n\n"
        f"\U0001f4d6 <b>{_clean_title(file['file_name'])}</b>\n"
        f"Source format: <code>{source_format.upper()}</code>\n\n"
        "Choose target format:\n"
        f"<i>({_remaining_conversion_text(remaining)})</i>",
        reply_markup=_conversion_menu_markup(
            prefix,
            file_id,
            source_format,
        ),
    )


async def handle_do_convert_callback(client, query):
    conversion = await _load_conversion(query)
    if conversion is None:
        return
    await query.message.edit_text(
        f"\u23f3 <b>Converting {conversion.source_format.upper()} "
        f"\u2192 {conversion.target_format.upper()}...</b>\n\n"
        "This may take up to 30 seconds."
    )
    try:
        await client.download_media(
            conversion.file_id,
            file_name=conversion.input_path,
        )
        converted = await _run_conversion(
            conversion.input_path,
            conversion.output_path,
        )
        if not converted:
            _track_conversion_failure(conversion, "converter_rejected_file")
            await query.message.edit_text(
                "\u274c <b>Conversion failed.</b> The file may be "
                "DRM-protected or corrupted."
            )
            return
        await _deliver_conversion(client, query, conversion)
    except asyncio.TimeoutError:
        _track_conversion_failure(conversion, "timeout")
        await query.message.edit_text(
            "\u274c <b>Conversion timed out.</b> Please try again."
        )
    except (OSError, PyMongoError, RPCError):
        _track_conversion_failure(conversion, "runtime_error")
        logger.exception("Failed to convert file")
        await query.message.edit_text(
            "<b>Conversion failed.</b> Please try again later."
        )
    finally:
        for path in (conversion.input_path, conversion.output_path):
            if os.path.exists(path):
                os.remove(path)


async def handle_convert_back_callback(client, query):
    _, prefix, file_id = query.data.split("#", 2)
    file = await get_file_details(file_id)
    if not file:
        await query.answer("File not found.", show_alert=True)
        return

    title = file["file_name"]
    buttons = [
        [
            InlineKeyboardButton(
                "\U0001f4e5 Download",
                callback_data=f"download_book#{prefix}#{file_id}",
            )
        ]
    ]
    settings = await get_global_settings()
    if _detect_format(title) and settings["conversion_enabled"]:
        buttons.append(
            [
                InlineKeyboardButton(
                    "\U0001f504 Convert Format",
                    callback_data=f"convert_menu#{prefix}#{file_id}",
                )
            ]
        )
    await query.message.edit_text(
        text=(
            f"<b>\U0001f4d6 {_clean_title(title)}</b>\n"
            f"<b>\U0001f4e6 Size:</b> {get_size(file['file_size'])}"
        ),
        reply_markup=InlineKeyboardMarkup(buttons),
    )
