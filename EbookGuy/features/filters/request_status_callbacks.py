from pyrogram.errors import UserIsBlocked
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from Script import script
from info import ADMINS, CHNL_LNK, REQST_CHANNEL, SUPPORT_CHAT_ID


async def maybe_handle_request_status_callback(client, query):
    if query.data.startswith("show_option"):
        ident, from_user = query.data.split("#")
        btn = [[
                InlineKeyboardButton("Unavailable", callback_data=f"unavailable#{from_user}"),
                InlineKeyboardButton("Uploaded", callback_data=f"uploaded#{from_user}")
             ],[
                InlineKeyboardButton("Already Available", callback_data=f"already_available#{from_user}"),
                InlineKeyboardButton("Processing", callback_data=f"processing#{from_user}")
              ]]
        btn2 = [[
                 InlineKeyboardButton("View Status", url=f"{query.message.link}")
               ]]
        if query.from_user.id in ADMINS:
            user = await client.get_users(from_user)
            reply_markup = InlineKeyboardMarkup(btn)
            content = query.message.text
            await query.message.edit_text(f"<b>{content}</b>", reply_markup=reply_markup)
            await query.answer("Here are the options !")
        else:
            await query.answer("You don't have sufficient rights to do this !", show_alert=True)
        
    elif query.data.startswith("unavailable"):
        ident, from_user = query.data.split("#")
        btn = [[
                InlineKeyboardButton("⚠️ Unavailable ⚠️", callback_data=f"unalert#{from_user}"),
                InlineKeyboardButton("🔙 Back", callback_data=f"show_option#{from_user}")
              ]]
        try:
            link = await client.create_chat_invite_link(int(REQST_CHANNEL))
            url = link.invite_link
        except Exception:
            url = CHNL_LNK
        btn2 = [[
                 InlineKeyboardButton('Join Channel', url=url),
                 InlineKeyboardButton("View Status", url=f"{query.message.link}")
               ]]
        if query.from_user.id in ADMINS:
            user = await client.get_users(from_user)
            reply_markup = InlineKeyboardMarkup(btn)
            content = query.message.text
            await query.message.edit_text(f"<b><strike>{content}</strike></b>", reply_markup=reply_markup)
            await query.answer("Set to Unavailable !")
            try:
                await client.send_message(chat_id=int(from_user), text=script.REQ_UNAVAILABLE.format(user.mention), reply_markup=InlineKeyboardMarkup(btn2))
            except UserIsBlocked:
                await client.send_message(chat_id=int(SUPPORT_CHAT_ID), text=script.REQ_UNAVAILABLE.format(user.mention) + "\n\nNote: This message is sent to this group because you've blocked the bot. To send this message to your PM, Must unblock the bot.", reply_markup=InlineKeyboardMarkup(btn2))
        else:
            await query.answer("You don't have sufficient rights to do this !", show_alert=True)

    elif query.data.startswith("uploaded"):
        ident, from_user = query.data.split("#")
        btn = [[
                InlineKeyboardButton("✅ Uploaded ✅", callback_data=f"upalert#{from_user}")
              ]]
        try:
            link = await client.create_chat_invite_link(int(REQST_CHANNEL))
            url = link.invite_link
        except Exception:
            url = CHNL_LNK
        btn2 = [[
                 InlineKeyboardButton('Join Channel', url=url),
                 InlineKeyboardButton("View Status", url=f"{query.message.link}")
               ]]
        if query.from_user.id in ADMINS:
            user = await client.get_users(from_user)
            reply_markup = InlineKeyboardMarkup(btn)
            content = query.message.text
            await query.message.edit_text(f"<b><strike>{content}</strike></b>", reply_markup=reply_markup)
            await query.answer("Set to Uploaded !")
            try:
                await client.send_message(chat_id=int(from_user), text=script.REQ_UPLOADED.format(user.mention), reply_markup=InlineKeyboardMarkup(btn2))
            except UserIsBlocked:
                await client.send_message(chat_id=int(SUPPORT_CHAT_ID), text=script.REQ_UPLOADED.format(user.mention) + "\n\nNote: This message is sent to this group because you've blocked the bot. To send this message to your PM, Must unblock the bot.", reply_markup=InlineKeyboardMarkup(btn2))
        else:
            await query.answer("You don't have sufficient rights to do this !", show_alert=True)

    elif query.data.startswith("already_available"):
        ident, from_user = query.data.split("#")
        btn = [[
            InlineKeyboardButton("🟢 Already Available 🟢", callback_data=f"alalert#{from_user}")
        ]]
        try:
            link = await client.create_chat_invite_link(int(REQST_CHANNEL))
            url = link.invite_link
        except Exception:
            url = CHNL_LNK
        btn2 = [[
            InlineKeyboardButton('Join Channel', url=url),
            InlineKeyboardButton("View Status", url=f"{query.message.link}")
        ]]
        if query.from_user.id in ADMINS:
            user = await client.get_users(from_user)
            reply_markup = InlineKeyboardMarkup(btn)
            content = query.message.text
            await query.message.edit_text(f"<b><strike>{content}</strike></b>", reply_markup=reply_markup)
            await query.answer("Set to Already Available !")
            try:
                await client.send_message(chat_id=int(from_user), text=script.REQ_ALREADY_EXIST.format(user.mention), reply_markup=InlineKeyboardMarkup(btn2))
            except UserIsBlocked:
                await client.send_message(chat_id=int(SUPPORT_CHAT_ID), text=script.REQ_ALREADY_EXIST.format(user.mention) + "\n\nNote: This message is sent to this group because you've blocked the bot. To send this message to your PM, Must unblock the bot.", reply_markup=InlineKeyboardMarkup(btn2))
        else:
            await query.answer("You don't have sufficient rights to do this !", show_alert=True)

    elif query.data.startswith("alalert"):
        ident, from_user = query.data.split("#")
        if int(query.from_user.id) == int(from_user):
            user = await client.get_users(from_user)
            await query.answer(f"Hey {user.first_name}, Your Request is Already Available !", show_alert=True)
        else:
            await query.answer("You don't have sufficient rights to do this !", show_alert=True)

    elif query.data.startswith("upalert"):
        ident, from_user = query.data.split("#")
        if int(query.from_user.id) == int(from_user):
            user = await client.get_users(from_user)
            await query.answer(f"Hey {user.first_name}, Your Request is Uploaded !", show_alert=True)
        else:
            await query.answer("You don't have sufficient rights to do this !", show_alert=True)
        
    elif query.data.startswith("unalert"):
        ident, from_user = query.data.split("#")
        if int(query.from_user.id) == int(from_user):
            user = await client.get_users(from_user)
            await query.answer(f"Hey {user.first_name}, Your Request is Unavailable !", show_alert=True)
        else:
            await query.answer("You don't have sufficient rights to do this !", show_alert=True)

    elif query.data.startswith("processing"):
        ident, from_user = query.data.split("#")
        btn = [[
                InlineKeyboardButton("⏳ Processing ⏳", callback_data=f"proalert#{from_user}"),
                InlineKeyboardButton("🔙 Back", callback_data=f"show_option#{from_user}")
              ]]
        try:
            link = await client.create_chat_invite_link(int(REQST_CHANNEL))
            url = link.invite_link
        except Exception:
            url = CHNL_LNK
        btn2 = [[
                 InlineKeyboardButton('Join Channel', url=url),
                 InlineKeyboardButton("View Status", url=f"{query.message.link}")
               ]]
        if query.from_user.id in ADMINS:
            user = await client.get_users(from_user)
            reply_markup = InlineKeyboardMarkup(btn)
            content = query.message.text
            await query.message.edit_text(f"<b><strike>{content}</strike></b>", reply_markup=reply_markup)
            await query.answer("Set to Processing !")
            try:
                await client.send_message(chat_id=int(from_user), text=script.REQ_PROCESSING.format(user.mention), reply_markup=InlineKeyboardMarkup(btn2))
            except UserIsBlocked:
                await client.send_message(chat_id=int(SUPPORT_CHAT_ID), text=script.REQ_PROCESSING.format(user.mention) + "\n\nNote: This message is sent to this group because you've blocked the bot. To send this message to your PM, Must unblock the bot.", reply_markup=InlineKeyboardMarkup(btn2))
        else:
            await query.answer("You don't have sufficient rights to do this !", show_alert=True)

    elif query.data.startswith("proalert"):
        ident, from_user = query.data.split("#")
        if int(query.from_user.id) == int(from_user):
            user = await client.get_users(from_user)
            await query.answer(f"Hey {user.first_name}, Your Request is Processing !", show_alert=True)
        else:
            await query.answer("You don't have sufficient rights to do this !", show_alert=True)
    else:
        return False
    return True
