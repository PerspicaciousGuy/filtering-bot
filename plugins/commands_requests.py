from Script import script
from pyrogram.types import *
from pyrogram.errors import UserIsBlocked
from info import *

async def handle_requests(bot, message):
    if message.reply_to_message:
        reporter = str(message.from_user.id)
        mention = message.from_user.mention
        success = True
        reported_post = None
        content = message.reply_to_message.text
        try:
            btn = [[
                InlineKeyboardButton('Show Options', callback_data=f'show_option#{reporter}')
            ]]
            if REQST_CHANNEL is not None:
                reported_post = await bot.send_message(chat_id=REQST_CHANNEL, text=f"<b>Reporter :</b> <code>{message.from_user.first_name}</code>\n\n<b>Message :</b> <code>{content}</code>", reply_markup=InlineKeyboardMarkup(btn))
                success = True
            elif len(content) >= 3:
                for admin in ADMINS:
                    reported_post = await bot.send_message(chat_id=admin, text=f"<b>𝖱𝖾𝗉𝗈𝗋𝗍𝖾𝗿 : {mention} ({reporter})\n\n𝖬𝖾𝗌𝗌𝖺𝗀𝖾 : {content}</b>", reply_markup=InlineKeyboardMarkup(btn))
                    success = True
            else:
                if len(content) < 3:
                    await message.reply_text("<b>You must type about your request [Minimum 3 Characters]. Requests can't be empty.</b>")
            if len(content) < 3:
                success = False
        except Exception as e:
            await message.reply_text(f"Error: {e}")
        
    elif message.text:
        reporter = str(message.from_user.id)
        mention = message.from_user.mention
        success = True
        reported_post = None
        content = message.text
        keywords = ["#request", "/request", "#Request", "/Request"]
        for keyword in keywords:
            if keyword in content:
                content = content.replace(keyword, "")
        try:
            btn = [[
                InlineKeyboardButton('Show Options', callback_data=f'show_option#{reporter}')
            ]]
            if REQST_CHANNEL is not None and len(content) >= 3:
                reported_post = await bot.send_message(chat_id=REQST_CHANNEL, text=f"<b>Reporter :</b> <code>{message.from_user.first_name}</code>\n\n<b>Message :</b> <code>{content}</code>", reply_markup=InlineKeyboardMarkup(btn))
                success = True
            elif len(content) >= 3:
                for admin in ADMINS:
                    reported_post = await bot.send_message(chat_id=admin, text=f"<b>Reporter :</b> <code>{mention} ({reporter})</code>\n\n<b>Message :</b> <code>{content}</code>", reply_markup=InlineKeyboardMarkup(btn))
                    success = True
            else:
                if len(content) < 3:
                    await message.reply_text("<b>You must type about your request [Minimum 3 Characters]. Requests can't be empty.</b>")
            if len(content) < 3:
                success = False
        except Exception as e:
            await message.reply_text(f"Error: {e}")

    else:
        success = False
    
    if success:
        if reported_post:
            try:
                if REQST_CHANNEL:
                    try:
                        link = await bot.create_chat_invite_link(int(REQST_CHANNEL))
                        url = link.invite_link
                    except:
                        url = CHNL_LNK
                    
                    btn = [[
                        InlineKeyboardButton('Join Channel', url=url),
                        InlineKeyboardButton('View Request', url=f"{reported_post.link}")
                    ]]
                    await message.reply_text("<b>Your request has been added! Please wait for some time.\n\nJoin Channel First & View Request</b>", reply_markup=InlineKeyboardMarkup(btn))
                else:
                    await message.reply_text("<b>Your request has been sent to Admins!</b>")
            except Exception as e:
                await message.reply_text(f"Request sent, but failed to reply to you: {e}")
        elif REQST_CHANNEL is None:
             await message.reply_text("<b>Your request has been sent to Admins!</b>")
