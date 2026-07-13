from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from info import ADMINS
from EbookGuy.features.indexing.models import IndexRequest
from EbookGuy.features.indexing.worker import index_files_to_db, lock
from utils import temp

async def handle_index_files(bot, query):
    if query.data.startswith('index_cancel'):
        temp.CANCEL = True
        return await query.answer("Cancelling Indexing... Progress will be saved.")
    _, moderation_action, chat, lst_msg_id, from_user = query.data.split("#")
    if moderation_action == 'reject':
        await query.message.delete()
        await bot.send_message(
            int(from_user),
            f'Your Submission for indexing {chat} has been declined by our moderators.',
            reply_to_message_id=int(lst_msg_id)
        )
        return

    if lock.locked():
        return await query.answer('Wait until previous process complete.', show_alert=True)
    msg = query.message

    await query.answer('Processing...⏳', show_alert=True)
    if int(from_user) not in ADMINS:
        await bot.send_message(
            int(from_user),
            f'Your Submission for indexing {chat} has been accepted by our moderators and will be added soon.',
            reply_to_message_id=int(lst_msg_id)
        )
    await msg.edit(
        "Starting Indexing",
        reply_markup=InlineKeyboardMarkup(
            [[InlineKeyboardButton('⏸️ Pause', callback_data='index_cancel')]]
        )
    )
    try:
        chat_id = int(chat)
    except ValueError:
        chat_id = chat
    await index_files_to_db(IndexRequest(
        last_message_id=int(lst_msg_id),
        chat_id=chat_id,
        status_message=msg,
        bot=bot,
    ))
