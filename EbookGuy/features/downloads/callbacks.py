import asyncio

from Script import script
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from database.ia_filterdb import get_file_details
from info import FREE_DAILY_LIMIT
from EbookGuy.features.downloads.limits import (
    answer_download_limit_callback,
    check_and_increment_download,
)
from EbookGuy.shared.formatting import format_file_caption
from utils import get_size


def _fallback_caption(title):
    return " ".join(
        part
        for part in title.split()
        if not part.startswith("[") and not part.startswith("@")
    )


def _download_count_text(is_premium, count):
    if is_premium:
        prefix = script.DOWNLOAD_COUNT_PREMIUM
    else:
        prefix = script.DOWNLOAD_COUNT.format(count, FREE_DAILY_LIMIT)
    return prefix + "\n\n" + script.IMPORTANT_DELETE_MSG


def get_file_again_markup(file_id):
    return InlineKeyboardMarkup(
        [[
            InlineKeyboardButton(
                script.GET_FILE_AGAIN,
                callback_data=f"del#{file_id}",
            )
        ]]
    )


async def handle_download_book_callback(client, query):
    _, pre, file_id = query.data.split("#", 2)
    user_id = query.from_user.id
    can_download, is_premium, count, cooldown = (
        await check_and_increment_download(user_id)
    )
    if not can_download:
        await answer_download_limit_callback(query, is_premium, cooldown)
        return

    file = await get_file_details(file_id)
    if not file:
        return await query.answer("File not found.", show_alert=True)

    title = file["file_name"]
    caption = format_file_caption(
        title,
        get_size(file["file_size"]),
        file["caption"],
    )
    await query.message.delete()
    message = await client.send_cached_media(
        chat_id=user_id,
        file_id=file_id,
        caption=caption or _fallback_caption(title),
        protect_content=pre == "filep",
    )
    count_message = await message.reply(
        _download_count_text(is_premium, count)
    )
    await asyncio.sleep(600)
    await message.delete()
    await count_message.edit_text(
        script.FILE_DELETED_BTN,
        reply_markup=get_file_again_markup(file_id),
    )
