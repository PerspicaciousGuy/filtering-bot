from Script import script
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from database.ia_filterdb import get_file_details
from EbookGuy.features.downloads.limits import (
    answer_download_limit_callback,
    auto_delete_notice,
    check_and_increment_download,
    delete_delivered_messages,
    download_count_text,
)
from EbookGuy.shared.formatting import format_file_caption
from EbookGuy.shared.global_settings import get_global_settings
from utils import get_size


def _fallback_caption(title):
    return " ".join(
        part
        for part in title.split()
        if not part.startswith("[") and not part.startswith("@")
    )


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
    _, _prefix, file_id = query.data.split("#", 2)
    user_id = query.from_user.id
    file = await get_file_details(file_id)
    if not file:
        return await query.answer("File not found.", show_alert=True)
    access = await check_and_increment_download(user_id, file["file_size"])
    if not access.is_allowed:
        await answer_download_limit_callback(query, access)
        return

    settings = await get_global_settings()
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
        protect_content=bool(settings["protect_content"]),
    )
    count_text = download_count_text(access)
    if settings["auto_delete_enabled"]:
        count_text += "\n\n" + auto_delete_notice(
            int(settings["auto_delete_delay_seconds"])
        )
    count_message = await message.reply(count_text)
    was_deleted = await delete_delivered_messages((message,), settings)
    if not was_deleted:
        return
    await count_message.edit_text(
        script.FILE_DELETED_BTN,
        reply_markup=get_file_again_markup(file_id),
    )
