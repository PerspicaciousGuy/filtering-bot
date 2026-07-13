import asyncio, logging, os, sys

from pyrogram.errors import RPCError
from pymongo.errors import PyMongoError

from pyrogram import enums
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from database.ia_filterdb import col, delete_file_record, sec_col, unpack_new_file_id, get_bad_files
from database.users_chats_db import db
from info import CHANNELS
from utils import get_size

logger = logging.getLogger(__name__)

async def handle_channel_info(bot, message):
    text = '📑 **Indexed channels/groups**\n'
    for channel in CHANNELS:
        chat = await bot.get_chat(channel)
        if chat.username:
            text += '\n@' + chat.username
        else:
            text += '\n' + chat.title or chat.first_name

    text += f'\n\n**Total:** {len(CHANNELS)}'

    if len(text) < 4096:
        await message.reply(text)
    else:
        file = 'Indexed channels.txt'
        with open(file, 'w') as f:
            f.write(text)
        await message.reply_document(file)
        os.remove(file)

async def handle_log_file(bot, message):
    try:
        await message.reply_document('TELEGRAM BOT.LOG')
    except (AttributeError, IndexError, KeyError, OSError, PyMongoError, RPCError, TypeError, ValueError):
        logger.exception("Failed to send log file")
        await message.reply("Could not send the log file right now.")

async def handle_delete(bot, message):
    reply = await bot.ask(message.from_user.id, "Now Send Me Media Which You Want to delete")
    if reply.media:
        msg = await message.reply("Processing...⏳", quote=True)
    else:
        await message.reply('Send Me Video, File Or Document.', quote=True)
        return

    for file_type in ("document", "video", "audio"):
        media = getattr(reply, file_type, None)
        if media is not None:
            break
    else:
        await msg.edit('This is not supported file format')
        return
    
    file_id = unpack_new_file_id(media.file_id)
    deleted_count = await delete_file_record(
        file_id,
        media.file_name,
        media.file_size,
    )
    if deleted_count:
        await msg.edit('File is successfully deleted from database')
    else:
        await msg.edit('File not found in database')

async def handle_delete_all_index(bot, message):
    await message.reply_text(
        'This will delete all indexed files.\nDo you want to continue??',
        reply_markup=InlineKeyboardMarkup(
            [[
                InlineKeyboardButton(text="YES", callback_data="autofilter_delete")
            ],[
                InlineKeyboardButton(text="CANCEL", callback_data="close_data")
            ]]
        ),
        quote=True,
    )

async def handle_delete_all_index_confirm(bot, query):
    await col.drop()
    await sec_col.drop()
    await query.answer('Piracy Is Crime')
    await query.message.edit('Succesfully Deleted All The Indexed Files.')

async def handle_send_msg(bot, message):
    if message.reply_to_message:
        target_id = message.text.split(" ", 1)[1]
        out = "Users Saved In DB Are:\n\n"
        success = False
        try:
            user = await bot.get_users(target_id)
            users = await db.get_all_users()
            async for usr in users:
                out += f"{usr['id']}"
                out += '\n'
            if str(user.id) in str(out):
                await message.reply_to_message.copy(int(user.id))
                success = True
            else:
                success = False
            if success:
                await message.reply_text(f"<b>Your message has been successfully send to {user.mention}.</b>")
            else:
                await message.reply_text("<b>This user didn't started this bot yet !</b>")
        except (AttributeError, IndexError, KeyError, OSError, PyMongoError, RPCError, TypeError, ValueError):
            logger.exception("Failed to send admin message")
            await message.reply_text("<b>Could not send that message right now.</b>")
    else:
        await message.reply_text("<b>Use this command as a reply to any message using the target chat id. For eg: /send userid</b>")

async def handle_deletemultiplefiles(bot, message):
    try:
        keyword = message.text.split(" ", 1)[1]
    except (AttributeError, IndexError, KeyError, OSError, PyMongoError, RPCError, TypeError, ValueError):
        return await message.reply_text(f"<b>Hey {message.from_user.mention}, Give me a keyword along with the command to delete files.</b>")
    k = await bot.send_message(chat_id=message.chat.id, text=f"<b>Fetching Files for your query {keyword} on DB... Please wait...</b>")
    _, total = await get_bad_files(keyword)
    await k.delete()
    btn = [[
       InlineKeyboardButton("Yes, Continue !", callback_data=f"killfilesdq#{keyword}")
    ],[
       InlineKeyboardButton("No, Abort operation !", callback_data="close_data")
    ]]
    await message.reply_text(
        text=f"<b>Found {total} files for your query {keyword} !\n\nDo you want to delete?</b>",
        reply_markup=InlineKeyboardMarkup(btn),
        parse_mode=enums.ParseMode.HTML
    )

async def handle_stats(client, message):
    msg = await message.reply_text("<b>📊 Fetching stats...</b>")
    try:
        # Users
        total_users = await db.total_users_count()
        total_premium = await db.get_premium_stats()
        total_banned = await db.get_banned_users_count()

        # Files
        total_files = await col.count_documents({}) + await sec_col.count_documents({})
        size_pipeline = [{'$group': {'_id': None, 'total': {'$sum': '$file_size'}}}]
        size_result = await col.aggregate(size_pipeline).to_list(length=1)
        sec_size_result = await sec_col.aggregate(size_pipeline).to_list(length=1)
        total_size = (size_result[0]['total'] if size_result else 0) + (sec_size_result[0]['total'] if sec_size_result else 0)

        # Downloads today
        today_downloads = await db.get_today_total_downloads()

        # DB storage stats
        try:
            db_stats = await db.db.command('dbStats')
            used_mb = round(db_stats.get('dataSize', 0) / (1024 * 1024), 2)
            storage_mb = round(db_stats.get('storageSize', 0) / (1024 * 1024), 2)
            db_info = f"\n💾 <b>Data Size:</b> {used_mb} MB\n🗜️ <b>Storage Size:</b> {storage_mb} MB"
        except (AttributeError, IndexError, KeyError, OSError, PyMongoError, RPCError, TypeError, ValueError):
            db_info = "\n⚠️ DB stats unavailable"

        text = (
            f"<b>📊 Bot Statistics</b>\n"
            f"{'─' * 28}\n"
            f"👥 <b>Users</b>\n"
            f"  • Total: <code>{total_users}</code>\n"
            f"  • Premium: <code>{total_premium}</code>\n"
            f"  • Banned: <code>{total_banned}</code>\n\n"
            f"📚 <b>Library</b>\n"
            f"  • Total Files: <code>{total_files}</code>\n"
            f"  • Total Size: <code>{get_size(total_size)}</code>\n\n"
            f"📥 <b>Downloads Today</b>: <code>{today_downloads}</code>\n\n"
            f"🗄️ <b>Database</b>{db_info}"
        )
        await msg.edit_text(text)
    except (AttributeError, IndexError, KeyError, OSError, PyMongoError, RPCError, TypeError, ValueError):
        logger.exception("Failed to fetch admin stats")
        await msg.edit_text("<b>Error fetching stats. Please try again later.</b>")

async def handle_stop_button(bot, message):
    msg = await bot.send_message(
        text="**\U0001f504 Process stopped. Bot is restarting...**",
        chat_id=message.chat.id,
    )
    await asyncio.sleep(3)
    await msg.edit(
        "**\u2705 Bot restarted. You can use it again.**"
    )
    os.execl(sys.executable, sys.executable, *sys.argv)
