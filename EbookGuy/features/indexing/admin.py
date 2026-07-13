import logging

from pyrogram.errors import RPCError

from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from database.indexing_checkpoints import (
    delete_checkpoint,
    get_all_checkpoints,
    get_checkpoint,
)
from info import ADMINS
from EbookGuy.features.indexing.models import IndexRequest
from EbookGuy.features.indexing.worker import index_files_to_db, lock
from utils import temp

logger = logging.getLogger(__name__)

async def handle_set_skip_number(bot, message):
    if ' ' in message.text:
        _, skip = message.text.split(" ", 1)
        try:
            skip = int(skip)
        except (RPCError, TypeError, ValueError):
            return await message.reply("Skip number should be an integer.")
        await message.reply(f"✅ Successfully set SKIP number to **{skip}**\n\nIndexing will start from message #{skip}")
        temp.CURRENT = int(skip)
    else:
        await message.reply(f"**Current skip value:** `{temp.CURRENT}`\n\nUsage: `/setskip <number>`")


async def _reply_single_checkpoint(bot, message, checkpoint):
    chat_id = checkpoint["chat_id"]
    try:
        chat = await bot.get_chat(chat_id)
        chat_name = chat.title or chat_id
    except (RPCError, TypeError, ValueError):
        chat_name = chat_id

    buttons = [
        [
            InlineKeyboardButton(
                "\u25b6\ufe0f Resume",
                callback_data=f"resume_idx#{chat_id}",
            ),
            InlineKeyboardButton(
                "\U0001f5d1\ufe0f Delete",
                callback_data=f"delete_cp#{chat_id}",
            ),
        ]
    ]
    stats = checkpoint.get("stats", {})
    await message.reply(
        "\U0001f4e5 **Saved Indexing Progress**\n\n"
        f"\U0001f4cb Channel: \x60{chat_name}\x60\n"
        f"\U0001f4cd Paused at: Message #{checkpoint['current_msg']}\n"
        f"\u2705 Saved: {stats.get('total', 0)} files\n"
        f"\U0001f504 Duplicates: {stats.get('duplicate', 0)}\n\n"
        "Choose an action:",
        reply_markup=InlineKeyboardMarkup(buttons),
    )


async def _reply_checkpoint_list(message, checkpoints):
    text = "\U0001f4e5 **Saved Indexing Progress**\n\n"
    buttons = []
    for index, checkpoint in enumerate(checkpoints[:10], 1):
        chat_id = checkpoint["chat_id"]
        saved = checkpoint.get("stats", {}).get("total", 0)
        text += (
            f"{index}. Chat \x60{chat_id}\x60 - Message "
            f"#{checkpoint['current_msg']} ({saved} saved)\n"
        )
        buttons.append(
            [
                InlineKeyboardButton(
                    f"\u25b6\ufe0f Resume #{index}",
                    callback_data=f"resume_idx#{chat_id}",
                ),
                InlineKeyboardButton(
                    "\U0001f5d1\ufe0f",
                    callback_data=f"delete_cp#{chat_id}",
                ),
            ]
        )
    await message.reply(
        text,
        reply_markup=InlineKeyboardMarkup(buttons),
    )


async def handle_resume_indexing(bot, message):
    """Show actions for saved indexing checkpoints."""
    checkpoints = await get_all_checkpoints()
    if not checkpoints:
        await message.reply(
            "\u274c No saved indexing progress found.\n\n"
            "Use /index to start indexing a new channel."
        )
        return
    if len(checkpoints) == 1:
        if lock.locked():
            await message.reply(
                "\u23f3 Wait until current indexing completes."
            )
            return
        await _reply_single_checkpoint(bot, message, checkpoints[0])
        return
    await _reply_checkpoint_list(message, checkpoints)


async def handle_resume_callback(bot, query):
    if query.from_user.id not in ADMINS:
        return await query.answer("Only admins can do this!", show_alert=True)
    
    chat_id = query.data.split('#')[1]
    try:
        chat_id = int(chat_id)
    except (RPCError, TypeError, ValueError):
        logger.debug("Using non-numeric checkpoint chat identifier: %s", chat_id)
    
    cp = await get_checkpoint(chat_id)
    if not cp:
        return await query.answer("Checkpoint not found!", show_alert=True)
    
    if lock.locked():
        return await query.answer('Wait until current indexing completes.', show_alert=True)
    
    await query.answer("Resuming indexing...")
    
    # Get the last message ID (we need to find it)
    try:
        # Try to get recent messages to find last_msg_id
        async for msg in bot.get_chat_history(chat_id, limit=1):
            last_msg_id = msg.id
            break
    except (RPCError, TypeError, ValueError):
        logger.exception("Failed to access channel while resuming indexing")
        return await query.message.edit("Could not access that channel. Please check the bot permissions and try again.")
    
    await query.message.edit(
        f"▶️ **Resuming indexing from message #{cp['current_msg']}...**",
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton('⏸️ Pause', callback_data='index_cancel')]])
    )
    
    await index_files_to_db(IndexRequest(
        last_message_id=last_msg_id,
        chat_id=chat_id,
        status_message=query.message,
        bot=bot,
        should_resume=True,
    ))


async def handle_delete_checkpoint_callback(bot, query):
    if query.from_user.id not in ADMINS:
        return await query.answer("Only admins can do this!", show_alert=True)
    
    chat_id = query.data.split('#')[1]
    try:
        chat_id = int(chat_id)
    except (RPCError, TypeError, ValueError):
        logger.debug("Using non-numeric checkpoint chat identifier: %s", chat_id)
    
    await delete_checkpoint(chat_id)
    await query.answer("Checkpoint deleted!")
    await query.message.edit("🗑️ Checkpoint deleted successfully.")
