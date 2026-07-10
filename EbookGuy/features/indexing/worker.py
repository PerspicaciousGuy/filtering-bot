import asyncio
import logging
import time

from pyrogram import enums
from pyrogram.errors import FloodWait, MessageNotModified
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from database.ia_filterdb import (
    delete_checkpoint,
    get_checkpoint,
    is_allowed_file,
    save_checkpoint,
    save_file,
)
from info import FILTER_BY_EXTENSION
from utils import temp

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
lock = asyncio.Lock()

CHECKPOINT_INTERVAL = 100      # Save checkpoint every N messages
PROGRESS_UPDATE_INTERVAL = 3   # Update progress every N seconds

def format_progress(current, stats, paused=False):
    """Format progress message for indexing."""
    status = "⏸️ **Paused**" if paused else "📥 **Indexing...**"
    filtered_text = f"\n🚫 Filtered: `{stats.get('filtered', 0)}`" if FILTER_BY_EXTENSION else ""
    return (
        f"{status}\n\n"
        f"📊 Messages processed: `{current}`\n"
        f"✅ Saved: `{stats['total']}`\n"
        f"🔄 Duplicates: `{stats['duplicate']}`\n"
        f"🗑️ Deleted: `{stats['deleted']}`\n"
        f"📄 No media: `{stats['no_media']}`\n"
        f"⚠️ Unsupported: `{stats['unsupported']}`"
        f"{filtered_text}\n"
        f"❌ Errors: `{stats['errors']}`"
    )


async def index_files_to_db(lst_msg_id, chat, msg, bot, resume=False):
    """
    Index files from a channel to database.
    
    Features:
    - Resume from checkpoint
    - Extension filtering (ebooks/audiobooks)
    - FloodWait handling with auto-retry
    - Progress saving every 100 messages
    - Time-based progress updates
    """
    
    # Initialize or restore stats
    if resume:
        cp = get_checkpoint(chat)
        if cp:
            stats = cp.get('stats', {
                'total': 0, 'duplicate': 0, 'errors': 0,
                'deleted': 0, 'no_media': 0, 'unsupported': 0, 'filtered': 0
            })
            start_from = cp['current_msg']
        else:
            stats = {'total': 0, 'duplicate': 0, 'errors': 0, 'deleted': 0, 'no_media': 0, 'unsupported': 0, 'filtered': 0}
            start_from = temp.CURRENT
    else:
        stats = {'total': 0, 'duplicate': 0, 'errors': 0, 'deleted': 0, 'no_media': 0, 'unsupported': 0, 'filtered': 0}
        start_from = temp.CURRENT
    
    current = start_from
    last_update = time.time()
    
    async with lock:
        temp.CANCEL = False
        try:
            async for message in bot.iter_messages(chat, lst_msg_id, start_from):
                # Check for cancel/pause
                if temp.CANCEL:
                    save_checkpoint(chat, current, stats)
                    await msg.edit(
                        f"⏸️ **Indexing Paused!**\n\n"
                        f"Progress saved at message #{current}\n"
                        f"Use /resume to continue.\n\n"
                        + format_progress(current, stats, paused=True)
                    )
                    return
                
                current += 1
                
                # Time-based progress update (every 3 seconds)
                if time.time() - last_update > PROGRESS_UPDATE_INTERVAL:
                    try:
                        await msg.edit_text(
                            format_progress(current, stats),
                            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton('⏸️ Pause', callback_data='index_cancel')]])
                        )
                    except MessageNotModified:
                        pass
                    last_update = time.time()
                
                # Save checkpoint periodically
                if current % CHECKPOINT_INTERVAL == 0:
                    save_checkpoint(chat, current, stats)
                
                # Handle deleted/empty messages
                if message.empty:
                    stats['deleted'] += 1
                    continue
                
                # Handle non-media messages
                if not message.media:
                    stats['no_media'] += 1
                    continue
                
                # Handle unsupported media types
                if message.media not in [enums.MessageMediaType.VIDEO, enums.MessageMediaType.AUDIO, enums.MessageMediaType.DOCUMENT]:
                    stats['unsupported'] += 1
                    continue
                
                media = getattr(message, message.media.value, None)
                if not media:
                    stats['unsupported'] += 1
                    continue
                
                # Filter by extension (ebooks/audiobooks only)
                if FILTER_BY_EXTENSION and not is_allowed_file(getattr(media, 'file_name', '')):
                    stats['filtered'] += 1
                    continue
                
                # Save the file
                media.caption = message.caption
                try:
                    success, code = await save_file(media)
                    if success:
                        stats['total'] += 1
                    elif code == 0:
                        stats['duplicate'] += 1
                    elif code == 2:
                        stats['errors'] += 1
                except Exception as e:
                    stats['errors'] += 1
                    logger.error(f"Error saving file: {e}")
                    
        except FloodWait as e:
            # Save progress before waiting
            save_checkpoint(chat, current, stats)
            wait_time = e.value + 5
            await msg.edit(
                f"⏳ **Rate Limited!**\n\n"
                f"Waiting {wait_time} seconds...\n"
                f"Progress saved at message #{current}\n\n"
                + format_progress(current, stats)
            )
            await asyncio.sleep(wait_time)
            # Resume after wait
            await msg.edit("▶️ Resuming indexing...")
            return await index_files_to_db(lst_msg_id, chat, msg, bot, resume=True)
            
        except Exception as e:
            save_checkpoint(chat, current, stats)
            logger.exception(e)
            await msg.edit(
                f"❌ **Error:** `{e}`\n\n"
                f"Progress saved at message #{current}\n"
                f"Use /resume to continue.\n\n"
                + format_progress(current, stats)
            )
            return
        
        # Successful completion
        delete_checkpoint(chat)
        filtered_text = f"\n🚫 Filtered out: `{stats['filtered']}`" if FILTER_BY_EXTENSION else ""
        await msg.edit(
            f"✅ **Indexing Complete!**\n\n"
            f"📊 Total messages: `{current}`\n"
            f"✅ Files saved: `{stats['total']}`\n"
            f"🔄 Duplicates skipped: `{stats['duplicate']}`\n"
            f"🗑️ Deleted messages: `{stats['deleted']}`\n"
            f"📄 Non-media: `{stats['no_media']}`\n"
            f"⚠️ Unsupported: `{stats['unsupported']}`"
            f"{filtered_text}\n"
            f"❌ Errors: `{stats['errors']}`"
        )
