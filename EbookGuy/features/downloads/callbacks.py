import asyncio

from Script import script
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from database.ia_filterdb import get_file_details
from info import CUSTOM_FILE_CAPTION, FREE_DAILY_LIMIT, PREMIUM_DAILY_LIMIT
from EbookGuy.features.downloads.limits import check_and_increment_download
from utils import get_size


async def handle_download_book_callback(client, query):
    _, pre, file_id = query.data.split("#", 2)
    user_id = query.from_user.id

    can_download, is_premium, count, cooldown = await check_and_increment_download(user_id)
    if not can_download:
        btn = [[InlineKeyboardButton("⭐ Upgrade to Premium", callback_data="show_premium")]]
        if is_premium and cooldown > 0:
            return await query.answer(f"⏱️ Wait {cooldown}s before next download.", show_alert=True)
        elif is_premium:
            return await query.answer(f"📚 Daily limit reached ({PREMIUM_DAILY_LIMIT}/day). Resets at midnight.", show_alert=True)
        else:
            await query.message.edit_text(
                text=f"📚 <b>Daily Limit Reached</b>\n\nFree users can download <b>1 book per day</b>.\n\nUpgrade to premium for <b>20 downloads/day</b>!",
                reply_markup=InlineKeyboardMarkup(btn)
            )
            return

    files_ = await get_file_details(file_id)
    if not files_:
        return await query.answer("File not found.", show_alert=True)

    title = files_["file_name"]
    size = get_size(files_["file_size"])
    f_caption = files_["caption"]
    if CUSTOM_FILE_CAPTION:
        try:
            f_caption = CUSTOM_FILE_CAPTION.format(file_name=title or '', file_size=size or '', file_caption=f_caption or '')
        except Exception:
            pass
    if not f_caption:
        f_caption = ' '.join(filter(lambda x: not x.startswith('[') and not x.startswith('@'), title.split()))

    await query.message.delete()
    msg = await client.send_cached_media(
        chat_id=user_id,
        file_id=file_id,
        caption=f_caption,
        protect_content=True if pre == 'filep' else False,
    )
    if is_premium:
        count_msg = await msg.reply(script.DOWNLOAD_COUNT_PREMIUM + "\n\n" + script.IMPORTANT_DELETE_MSG)
    else:
        count_msg = await msg.reply(script.DOWNLOAD_COUNT.format(count, FREE_DAILY_LIMIT) + "\n\n" + script.IMPORTANT_DELETE_MSG)
    btn = [[InlineKeyboardButton(script.GET_FILE_AGAIN, callback_data=f'del#{file_id}')]]
    await asyncio.sleep(600)
    await msg.delete()
    await count_msg.edit_text(script.FILE_DELETED_BTN, reply_markup=InlineKeyboardMarkup(btn))
