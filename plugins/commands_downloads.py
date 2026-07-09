import asyncio, datetime, random

from Script import script
from pyrogram import enums
from pyrogram.types import *
from database.ia_filterdb import get_file_details
from database.users_chats_db import db
from info import *
from utils import get_size, is_subscribed, temp

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
        except Exception:
            pass
    await k.edit_text("<b>✅ Your message is successfully deleted</b>")

def get_start_buttons():
    """Generate start buttons from centralized config"""
    buttons = []
    for btn in START_BUTTONS:
        buttons.append([InlineKeyboardButton(btn["label"], url=btn["url"])])
    return buttons

async def handle_start(client, message):
    if not await db.is_user_exist(message.from_user.id):
        await db.add_user(message.from_user.id, message.from_user.first_name)
        await client.send_message(LOG_CHANNEL, script.LOG_TEXT_P.format(message.from_user.id, message.from_user.mention))
    if len(message.command) != 2:
        reply_markup = InlineKeyboardMarkup(get_start_buttons())
        await message.reply_photo(
            photo=random.choice(PICS),
            caption=script.START_TXT.format(message.from_user.mention, temp.LIB_COUNT),
            reply_markup=reply_markup,
            parse_mode=enums.ParseMode.HTML
        )
        return
    
    if AUTH_CHANNEL and not await is_subscribed(client, message):
        try:
            if REQUEST_TO_JOIN_MODE == True:
                invite_link = await client.create_chat_invite_link(chat_id=(int(AUTH_CHANNEL)), creates_join_request=True)
            else:
                invite_link = await client.create_chat_invite_link(int(AUTH_CHANNEL))
        except Exception as e:
            await message.reply_text(script.FORCE_SUB_ADMIN_ERROR)
            return
        try:
            btn = [[InlineKeyboardButton(script.BACKUP_CHANNEL_BTN, url=invite_link.invite_link)]]
            if message.command[1] != "subscribe":
                if REQUEST_TO_JOIN_MODE == True:
                    if TRY_AGAIN_BTN == True:
                        try:
                            kk, file_id = message.command[1].split("_", 1)
                            btn.append([InlineKeyboardButton(script.TRY_AGAIN_BTN, callback_data=f"checksub#{kk}#{file_id}")])
                        except (IndexError, ValueError):
                            btn.append([InlineKeyboardButton(script.TRY_AGAIN_BTN, url=f"https://t.me/{temp.U_NAME}?start={message.command[1]}")])
                else:
                    try:
                        kk, file_id = message.command[1].split("_", 1)
                        btn.append([InlineKeyboardButton(script.TRY_AGAIN_BTN, callback_data=f"checksub#{kk}#{file_id}")])
                    except (IndexError, ValueError):
                        btn.append([InlineKeyboardButton(script.TRY_AGAIN_BTN, url=f"https://t.me/{temp.U_NAME}?start={message.command[1]}")])
            if REQUEST_TO_JOIN_MODE == True:
                if TRY_AGAIN_BTN == True:
                    text = script.BACKUP_CHANNEL_NOT_JOINED
                else:
                    await db.set_msg_command(message.from_user.id, com=message.command[1])
                    text = script.BACKUP_CHANNEL_NOT_JOINED_2
            else:
                text = script.BACKUP_CHANNEL_NOT_JOINED
            await client.send_message(
                chat_id=message.from_user.id,
                text=text,
                reply_markup=InlineKeyboardMarkup(btn),
                parse_mode=enums.ParseMode.MARKDOWN
            )
            return
        except Exception as e:
            return await message.reply_text(script.FORCE_SUB_ERROR)
            
    if len(message.command) == 2 and message.command[1] in ["subscribe", "error", "okay", "help"]:
        reply_markup = InlineKeyboardMarkup(get_start_buttons())      
        await message.reply_photo(
            photo=random.choice(PICS),
            caption=script.START_TXT.format(message.from_user.mention, temp.LIB_COUNT),
            reply_markup=reply_markup,
            parse_mode=enums.ParseMode.HTML
        )
        return
    data = message.command[1]
 
    try:
        pre, file_id = data.split('_', 1)
    except:
        file_id = data
        pre = ""
    
    if data.startswith("all"):
        files = temp.GETALL.get(file_id)
        if not files:
            return await message.reply(script.NO_FILE_EXIST)
        
        # Check download limit
        can_download, is_premium, count, cooldown = await check_and_increment_download(message.from_user.id)
        if not can_download:
            btn = [[InlineKeyboardButton("⭐ Upgrade to Premium", callback_data="show_premium")]]
            if is_premium and cooldown > 0:
                await message.reply_text(f"⏱️ <b>Rate Limited</b>\n\nPlease wait <b>{cooldown} seconds</b> before your next download.\n\n<i>Premium users can download 20 books/day with 30 second gaps.</i>")
            elif is_premium:
                await message.reply_text(f"📚 <b>Daily Limit Reached</b>\n\nYou have reached your premium limit of {PREMIUM_DAILY_LIMIT} downloads today.\n\nLimit resets at midnight.")
            else:
                await message.reply_text(
                    text=f"📚 <b>Daily Limit Reached</b>\n\nFree users can download <b>1 book per day</b>.\n\nUpgrade to premium for <b>20 downloads/day</b>!",
                    reply_markup=InlineKeyboardMarkup(btn)
                )
            return
        
        filesarr = []
        for file in files:
            file_id = file["file_id"]
            files1 = await get_file_details(file_id)
            title = files1["file_name"]
            size=get_size(files1["file_size"])
            f_caption=files1["caption"]
            if CUSTOM_FILE_CAPTION:
                try:
                    f_caption=CUSTOM_FILE_CAPTION.format(file_name= '' if title is None else title, file_size='' if size is None else size, file_caption='' if f_caption is None else f_caption)
                except Exception:
                    f_caption=f_caption
            if f_caption is None:
                f_caption = f"{' '.join(filter(lambda x: not x.startswith('[') and not x.startswith('@'), files1['file_name'].split()))}"
            reply_markup = None
            msg = await client.send_cached_media(
                chat_id=message.from_user.id,
                file_id=file_id,
                protect_content=True if pre == 'allfilesp' else False,
                reply_markup=reply_markup
            )
            filesarr.append(msg)
        
        # Show download count
        if is_premium:
            await message.reply_text(script.DOWNLOAD_COUNT_PREMIUM)
        else:
            await message.reply_text(script.DOWNLOAD_COUNT.format(count, FREE_DAILY_LIMIT))
        
        await send_auto_delete_message(client, message.from_user.id, filesarr)
        return    
        
    elif pre in ["file", "filep"]:
        # Main file handler
        user = message.from_user.id
        files_ = await get_file_details(file_id)           
        if not files_:
            pre, file_id = ((base64.urlsafe_b64decode(data + "=" * (-len(data) % 4))).decode("ascii")).split("_", 1)
            try:
                # Check download limit
                can_download, is_premium, count, cooldown = await check_and_increment_download(message.from_user.id)
                if not can_download:
                    btn = [[InlineKeyboardButton("⭐ Upgrade to Premium", callback_data="show_premium")]]
                    if is_premium and cooldown > 0:
                        await message.reply_text(f"⏱️ <b>Rate Limited</b>\n\nPlease wait <b>{cooldown} seconds</b> before your next download.")
                    elif is_premium:
                        await message.reply_text(f"📊 <b>Daily Limit Reached</b>\n\nYou have reached your premium limit of {PREMIUM_DAILY_LIMIT} downloads today.")
                    else:
                        await message.reply_text(
                            text=f"📊 <b>Daily Limit Reached</b>\n\nFree users can download <b>1 book per day</b>.\n\nUpgrade to premium for <b>20 downloads/day</b>!",
                            reply_markup=InlineKeyboardMarkup(btn)
                        )
                    return
                
                reply_markup = None
                msg = await client.send_cached_media(
                    chat_id=message.from_user.id,
                    file_id=file_id,
                    protect_content=True if pre == 'filep' else False,
                    reply_markup=reply_markup
                )
                filetype = msg.media
                file = getattr(msg, filetype.value)
                title = file.file_name
                size=get_size(file.file_size)
                f_caption = f"<code>{title}</code>"
                if CUSTOM_FILE_CAPTION:
                    try:
                        f_caption=CUSTOM_FILE_CAPTION.format(file_name= '' if title is None else title, file_size='' if size is None else size, file_caption='')
                    except Exception:
                        pass
                await msg.edit_caption(caption=f_caption)
                
                # Show download count
                if is_premium:
                    count_msg = await msg.reply(script.DOWNLOAD_COUNT_PREMIUM + "\n\n" + script.IMPORTANT_DELETE_MSG)
                else:
                    count_msg = await msg.reply(script.DOWNLOAD_COUNT.format(count, FREE_DAILY_LIMIT) + "\n\n" + script.IMPORTANT_DELETE_MSG)
                
                btn = [[InlineKeyboardButton(script.GET_FILE_AGAIN, callback_data=f'del#{file_id}')]]
                await asyncio.sleep(600)
                await msg.delete()
                await count_msg.edit_text(script.FILE_DELETED_BTN, reply_markup=InlineKeyboardMarkup(btn))
                return
            except Exception:
                pass
            return await message.reply(script.NO_FILE_EXIST)
        files = files_
        title = files["file_name"]
        size = get_size(files["file_size"])
        clean_title = ' '.join(filter(lambda x: not x.startswith('[') and not x.startswith('@'), title.split()))

        # Detect format from stored file name (dots replaced with spaces by clean_file_name)
        CONVERTIBLE = ['epub', 'pdf', 'mobi', 'azw', 'azw3']
        detected_ext = next((w for w in reversed(title.lower().split()) if w in CONVERTIBLE), None)

        btn = [[InlineKeyboardButton("📥 Download", callback_data=f"download_book#{pre}#{file_id}")]]
        if detected_ext:
            btn.append([InlineKeyboardButton("🔄 Convert Format", callback_data=f"convert_menu#{pre}#{file_id}")])

        await message.reply_text(
            text=f"<b>📖 {clean_title}</b>\n<b>📦 Size:</b> {size}",
            reply_markup=InlineKeyboardMarkup(btn)
        )
        return   

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
