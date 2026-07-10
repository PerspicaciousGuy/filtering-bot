from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from database.ia_filterdb import delete_checkpoint, get_all_checkpoints, get_checkpoint
from info import ADMINS
from EbookGuy.features.indexing.worker import index_files_to_db, lock
from utils import temp

async def handle_set_skip_number(bot, message):
    if ' ' in message.text:
        _, skip = message.text.split(" ", 1)
        try:
            skip = int(skip)
        except:
            return await message.reply("Skip number should be an integer.")
        await message.reply(f"✅ Successfully set SKIP number to **{skip}**\n\nIndexing will start from message #{skip}")
        temp.CURRENT = int(skip)
    else:
        await message.reply(f"**Current skip value:** `{temp.CURRENT}`\n\nUsage: `/setskip <number>`")


async def handle_resume_indexing(bot, message):
    """Resume paused/interrupted indexing from checkpoint."""
    checkpoints = get_all_checkpoints()
    
    if not checkpoints:
        return await message.reply("❌ No saved indexing progress found.\n\nUse /index to start indexing a new channel.")
    
    if len(checkpoints) == 1:
        # Auto-resume single checkpoint
        cp = checkpoints[0]
        chat_id = cp['chat_id']
        current_msg = cp['current_msg']
        stats = cp.get('stats', {})
        
        if lock.locked():
            return await message.reply('⏳ Wait until current indexing completes.')
        
        try:
            chat = await bot.get_chat(chat_id)
            chat_name = chat.title or chat_id
        except:
            chat_name = chat_id
        
        buttons = [[
            InlineKeyboardButton('▶️ Resume', callback_data=f'resume_idx#{chat_id}'),
            InlineKeyboardButton('🗑️ Delete', callback_data=f'delete_cp#{chat_id}')
        ]]
        
        return await message.reply(
            f"📥 **Saved Indexing Progress**\n\n"
            f"📋 Channel: `{chat_name}`\n"
            f"📍 Paused at: Message #{current_msg}\n"
            f"✅ Saved: {stats.get('total', 0)} files\n"
            f"🔄 Duplicates: {stats.get('duplicate', 0)}\n\n"
            f"Choose an action:",
            reply_markup=InlineKeyboardMarkup(buttons)
        )
    else:
        # Multiple checkpoints - show list
        text = "📥 **Saved Indexing Progress**\n\n"
        buttons = []
        for i, cp in enumerate(checkpoints[:10], 1):
            chat_id = cp['chat_id']
            current_msg = cp['current_msg']
            stats = cp.get('stats', {})
            text += f"{i}. Chat `{chat_id}` - Message #{current_msg} ({stats.get('total', 0)} saved)\n"
            buttons.append([
                InlineKeyboardButton(f'▶️ Resume #{i}', callback_data=f'resume_idx#{chat_id}'),
                InlineKeyboardButton(f'🗑️', callback_data=f'delete_cp#{chat_id}')
            ])
        
        return await message.reply(text, reply_markup=InlineKeyboardMarkup(buttons))


async def handle_resume_callback(bot, query):
    if query.from_user.id not in ADMINS:
        return await query.answer("Only admins can do this!", show_alert=True)
    
    chat_id = query.data.split('#')[1]
    try:
        chat_id = int(chat_id)
    except:
        pass
    
    cp = get_checkpoint(chat_id)
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
    except Exception as e:
        return await query.message.edit(f"❌ Error accessing channel: {e}")
    
    await query.message.edit(
        f"▶️ **Resuming indexing from message #{cp['current_msg']}...**",
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton('⏸️ Pause', callback_data='index_cancel')]])
    )
    
    await index_files_to_db(last_msg_id, chat_id, query.message, bot, resume=True)


async def handle_delete_checkpoint_callback(bot, query):
    if query.from_user.id not in ADMINS:
        return await query.answer("Only admins can do this!", show_alert=True)
    
    chat_id = query.data.split('#')[1]
    try:
        chat_id = int(chat_id)
    except:
        pass
    
    delete_checkpoint(chat_id)
    await query.answer("Checkpoint deleted!")
    await query.message.edit("🗑️ Checkpoint deleted successfully.")
