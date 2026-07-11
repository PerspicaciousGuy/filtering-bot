import asyncio
import logging
import datetime

from pyrogram.errors import RPCError

from Script import script
from database.users_chats_db import db
from info import FREE_DAILY_LIMIT, PREMIUM_DAILY_LIMIT, PREMIUM_DOWNLOAD_COOLDOWN


async def check_and_increment_download(user_id):
    """Check if user can download and increment count. Returns (can_download, is_premium, current_count, cooldown_remaining)"""
    is_premium, expiry = await db.get_premium_status(user_id)
    
    if is_premium:
        # Check premium rate limit (30 second cooldown)
        last_download = await db.get_user_last_download_time(user_id)
        if last_download:
            time_since_download = (datetime.datetime.now() - last_download).total_seconds()
            if time_since_download < PREMIUM_DOWNLOAD_COOLDOWN:
                remaining = PREMIUM_DOWNLOAD_COOLDOWN - int(time_since_download)
                return False, True, 0, remaining  # Still in cooldown
        
        # Check daily limit for premium
        current_downloads = await db.get_daily_downloads(user_id)
        if current_downloads >= PREMIUM_DAILY_LIMIT:
            return False, True, current_downloads, 0  # Daily limit reached
        
        # Allow download and update timestamp
        new_count = await db.increment_downloads(user_id)
        await db.set_user_last_download_time(user_id)
        return True, True, new_count, 0
    
    # Free user logic
    current_downloads = await db.get_daily_downloads(user_id)
    
    if current_downloads >= FREE_DAILY_LIMIT:
        return False, False, current_downloads, 0  # Daily limit reached
    
    # Increment and allow download
    new_count = await db.increment_downloads(user_id)
    return True, False, new_count, 0


async def send_auto_delete_message(client, user_id, filesarr):
    """Send auto-delete warning and delete files after 10 minutes"""
    k = await client.send_message(
        chat_id=user_id, 
        text=script.IMPORTANT_DELETE_MSG
    )
    await asyncio.sleep(600)
    for msg in filesarr:
        try:
            await msg.delete()
        except RPCError:
            logging.getLogger(__name__).debug("Auto-delete message was already unavailable", exc_info=True)
    await k.edit_text("<b>✅ Your message is successfully deleted</b>")
