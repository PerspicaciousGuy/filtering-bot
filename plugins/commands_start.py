import asyncio
import random

from Script import script
from pyrogram import enums
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from database.ia_filterdb import get_file_details
from database.users_chats_db import db
from info import *
from plugins.commands_download_limits import (
    check_and_increment_download,
    send_auto_delete_message,
)
from utils import get_size, is_subscribed, temp


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
