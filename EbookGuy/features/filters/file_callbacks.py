import asyncio
import logging

from pyrogram.errors import PeerIdInvalid, RPCError, UserIsBlocked
from pymongo.errors import PyMongoError
from pyrogram.types import InlineKeyboardMarkup

from database.ia_filterdb import col, get_bad_files, get_file_details, sec_col
from info import AUTH_CHANNEL, CUSTOM_FILE_CAPTION
from utils import get_settings, get_size, is_subscribed, pub_is_subscribed, temp

logger = logging.getLogger(__name__)
logger.setLevel(logging.ERROR)
lock = asyncio.Lock()


async def maybe_handle_file_callback(client, query):
    if query.data.startswith("file"):
        clicked = query.from_user.id
        try:
            typed = query.message.reply_to_message.from_user.id
        except (AttributeError, KeyError, PyMongoError, RPCError, TypeError, ValueError):
            typed = query.from_user.id
        ident, file_id = query.data.split("#")
        files_ = await get_file_details(file_id)
        if not files_:
            return await query.answer('No such file exist.')
        files = files_
        title = files["file_name"]
        size = get_size(files["file_size"])
        f_caption = files["caption"]
        settings = await get_settings(query.message.chat.id)
        if CUSTOM_FILE_CAPTION:
            try:
                f_caption = CUSTOM_FILE_CAPTION.format(file_name='' if title is None else title,
                                                       file_size='' if size is None else size,
                                                       file_caption='' if f_caption is None else f_caption,
                                                       filename='' if title is None else title,
                                                       filesize='' if size is None else size,
                                                       duration='')
            except (AttributeError, KeyError, PyMongoError, RPCError, TypeError, ValueError):
                logger.exception("Failed to format custom file callback caption")
            f_caption = f_caption
        if f_caption is None:
            f_caption = f"{files['file_name']}"

        try:
            if clicked == typed:
                await query.answer(url=f"https://telegram.me/{temp.U_NAME}?start={ident}_{file_id}")
                return
            else:
                await query.answer(f"Hey {query.from_user.first_name}, This Is Not Your Movie Request. Request Your's !", show_alert=True)
        except UserIsBlocked:
            await query.answer('Unblock the bot mahn !', show_alert=True)
        except PeerIdInvalid:
            await query.answer(url=f"https://telegram.me/{temp.U_NAME}?start={ident}_{file_id}")
        except (AttributeError, KeyError, PyMongoError, RPCError, TypeError, ValueError):
            await query.answer(url=f"https://telegram.me/{temp.U_NAME}?start={ident}_{file_id}")
            
    elif query.data.startswith("sendfiles"):
        clicked = query.from_user.id
        ident, key = query.data.split("#")
        settings = await get_settings(query.message.chat.id)
        pre = 'allfilesp' if settings['file_secure'] else 'allfiles'
        try:
            await query.answer(url=f"https://telegram.me/{temp.U_NAME}?start={pre}_{key}")
        except UserIsBlocked:
            await query.answer('Unblock the bot mahn !', show_alert=True)
        except PeerIdInvalid:
            await query.answer(url=f"https://telegram.me/{temp.U_NAME}?start={pre}_{key}")
        except (AttributeError, KeyError, PyMongoError, RPCError, TypeError, ValueError):
            logger.exception("Failed to answer sendfiles callback")
            await query.answer(url=f"https://telegram.me/{temp.U_NAME}?start={pre}_{key}")

    elif query.data.startswith("unmuteme"):
        ident, userid = query.data.split("#")
        user_id = query.from_user.id
        settings = await get_settings(int(query.message.chat.id))
        if userid == 0:
            await query.answer("You are anonymous admin !", show_alert=True)
            return
        try:
            btn = await pub_is_subscribed(client, query, settings['fsub'])
            if btn:
                await query.answer("Kindly Join Given Channel Then Click On Unmute Button", show_alert=True)
            else:
                await client.unban_chat_member(query.message.chat.id, user_id)
                await query.answer("Unmuted Successfully !", show_alert=True)
                try:
                    await query.message.delete()
                except (AttributeError, KeyError, PyMongoError, RPCError, TypeError, ValueError):
                    return
        except (AttributeError, KeyError, PyMongoError, RPCError, TypeError, ValueError):
            await query.answer("Not For Your My Dear", show_alert=True)
       
    elif query.data.startswith("del"):
        ident, file_id = query.data.split("#")
        files_ = await get_file_details(file_id)
        if not files_:
            return await query.answer('No such file exist.')
        files = files_
        title = files['file_name']
        size = get_size(files['file_size'])
        f_caption = files['caption']
        settings = await get_settings(query.message.chat.id)
        if CUSTOM_FILE_CAPTION:
            try:
                f_caption = CUSTOM_FILE_CAPTION.format(file_name='' if title is None else title,
                                                       file_size='' if size is None else size,
                                                       file_caption='' if f_caption is None else f_caption,
                                                       filename='' if title is None else title,
                                                       filesize='' if size is None else size,
                                                       duration='')
            except (AttributeError, KeyError, PyMongoError, RPCError, TypeError, ValueError):
                logger.exception("Failed to format custom delete callback caption")
            f_caption = f_caption
        if f_caption is None:
            f_caption = f"{files['file_name']}"
        await query.answer(url=f"https://telegram.me/{temp.U_NAME}?start=file_{file_id}")

    elif query.data.startswith("checksub"):
        if AUTH_CHANNEL and not await is_subscribed(client, query):
            await query.answer("Join our Back-up channel mahn! 😒", show_alert=True)
            return
        ident, kk, file_id = query.data.split("#")
        await query.answer(url=f"https://t.me/{temp.U_NAME}?start={kk}_{file_id}")

    elif query.data == "pages":
        await query.answer()

    elif query.data.startswith("pages#"):
        ident, keyword = query.data.split("#")
        #await query.message.edit_text(f"<b>Fetching Files for your query {keyword} on DB... Please wait...</b>")
        files, total = await get_bad_files(keyword)
        await query.message.edit_text("<b>File deletion process will start in 5 seconds !</b>")
        await asyncio.sleep(5)
        deleted = 0
        async with lock:
            try:
                for file in files:
                    file_ids = file["file_id"]
                    file_name = file["file_name"]
                    result = col.delete_one({
                        'file_id': file_ids,
                    })
                    if not result.deleted_count:
                        result = sec_col.delete_one({
                            'file_id': file_ids,
                        })
                    if result.deleted_count:
                        logger.info(f'File Found for your query {keyword}! Successfully deleted {file_name} from database.')
                    deleted += 1
                    if deleted % 50 == 0:
                        await query.message.edit_text(f"<b>Process started for deleting files from DB. Successfully deleted {str(deleted)} files from DB for your query {keyword} !\n\nPlease wait...</b>")
            except (AttributeError, KeyError, PyMongoError, RPCError, TypeError, ValueError):
                logger.exception("Failed while deleting files from database")
                await query.message.edit_text("Error deleting files. Please try again later.")
            else:
                await query.message.edit_text(f"<b>Process Completed for file deletion !\n\nSuccessfully deleted {str(deleted)} files from database for your query {keyword}.</b>")
    else:
        return False
    return True
