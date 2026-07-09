import asyncio, ast, logging

from pyrogram import Client, enums
from pyrogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from pyrogram.errors import UserIsBlocked, PeerIdInvalid
from info import *
from Script import script
from utils import get_size, is_subscribed, pub_is_subscribed, temp, get_settings
from database.ia_filterdb import col, sec_col, get_file_details, get_bad_files
from database.filters_mdb import del_all, find_filter
from database.connections_mdb import active_connection, all_connections, delete_connection, if_active, make_active, make_inactive
from database.gfilters_mdb import find_gfilter, del_allg
from plugins.pm_filter_premium_callbacks import maybe_handle_premium_callback

logger = logging.getLogger(__name__)
logger.setLevel(logging.ERROR)
lock = asyncio.Lock()

async def handle_callback(client: Client, query: CallbackQuery):
    if query.data == "close_data":
        await query.message.delete()
    elif await maybe_handle_premium_callback(client, query):
        return
    elif query.data == "gfiltersdeleteallconfirm":
        await del_allg(query.message, 'gfilters')
        await query.answer("Done !")
        return
    elif query.data == "gfiltersdeleteallcancel": 
        await query.message.reply_to_message.delete()
        await query.message.delete()
        await query.answer("Process Cancelled !")
        return
    elif query.data == "delallconfirm":
        userid = query.from_user.id
        chat_type = query.message.chat.type

        if chat_type == enums.ChatType.PRIVATE:
            grpid = await active_connection(str(userid))
            if grpid is not None:
                grp_id = grpid
                try:
                    chat = await client.get_chat(grpid)
                    title = chat.title
                except:
                    await query.message.edit_text("Make sure I'm present in your group!!", quote=True)
                    return await query.answer(MSG_ALRT)
            else:
                await query.message.edit_text(
                    "I'm not connected to any groups!\nCheck /connections or connect to any groups",
                    quote=True
                )
                return await query.answer(MSG_ALRT)

        elif chat_type in [enums.ChatType.GROUP, enums.ChatType.SUPERGROUP]:
            grp_id = query.message.chat.id
            title = query.message.chat.title

        else:
            return await query.answer(MSG_ALRT)

        st = await client.get_chat_member(grp_id, userid)
        if (st.status == enums.ChatMemberStatus.OWNER) or (str(userid) in ADMINS):
            await del_all(query.message, grp_id, title)
        else:
            await query.answer("You need to be Group Owner or an Auth User to do that!", show_alert=True)
    elif query.data == "delallcancel":
        userid = query.from_user.id
        chat_type = query.message.chat.type

        if chat_type == enums.ChatType.PRIVATE:
            await query.message.reply_to_message.delete()
            await query.message.delete()

        elif chat_type in [enums.ChatType.GROUP, enums.ChatType.SUPERGROUP]:
            grp_id = query.message.chat.id
            st = await client.get_chat_member(grp_id, userid)
            if (st.status == enums.ChatMemberStatus.OWNER) or (str(userid) in ADMINS):
                await query.message.delete()
                try:
                    await query.message.reply_to_message.delete()
                except:
                    pass
            else:
                await query.answer("That's not for you!!", show_alert=True)
    elif "groupcb" in query.data:
        await query.answer()

        group_id = query.data.split(":")[1]

        act = query.data.split(":")[2]
        hr = await client.get_chat(int(group_id))
        title = hr.title
        user_id = query.from_user.id

        if act == "":
            stat = "CONNECT"
            cb = "connectcb"
        else:
            stat = "DISCONNECT"
            cb = "disconnect"

        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton(f"{stat}", callback_data=f"{cb}:{group_id}"),
             InlineKeyboardButton("DELETE", callback_data=f"deletecb:{group_id}")],
            [InlineKeyboardButton("BACK", callback_data="backcb")]
        ])

        await query.message.edit_text(
            f"Group Name : **{title}**\nGroup ID : `{group_id}`",
            reply_markup=keyboard,
            parse_mode=enums.ParseMode.MARKDOWN
        )
        return await query.answer(MSG_ALRT)
    elif "connectcb" in query.data:
        await query.answer()

        group_id = query.data.split(":")[1]

        hr = await client.get_chat(int(group_id))

        title = hr.title

        user_id = query.from_user.id

        mkact = await make_active(str(user_id), str(group_id))

        if mkact:
            await query.message.edit_text(
                f"Connected to **{title}**",
                parse_mode=enums.ParseMode.MARKDOWN
            )
        else:
            await query.message.edit_text('Some error occurred!!', parse_mode=enums.ParseMode.MARKDOWN)
        return await query.answer(MSG_ALRT)
    elif "disconnect" in query.data:
        await query.answer()

        group_id = query.data.split(":")[1]

        hr = await client.get_chat(int(group_id))

        title = hr.title
        user_id = query.from_user.id

        mkinact = await make_inactive(str(user_id))

        if mkinact:
            await query.message.edit_text(
                f"Disconnected from **{title}**",
                parse_mode=enums.ParseMode.MARKDOWN
            )
        else:
            await query.message.edit_text(
                f"Some error occurred!!",
                parse_mode=enums.ParseMode.MARKDOWN
            )
        return await query.answer(MSG_ALRT)
    elif "deletecb" in query.data:
        await query.answer()

        user_id = query.from_user.id
        group_id = query.data.split(":")[1]

        delcon = await delete_connection(str(user_id), str(group_id))

        if delcon:
            await query.message.edit_text(
                "Successfully deleted connection !"
            )
        else:
            await query.message.edit_text(
                f"Some error occurred!!",
                parse_mode=enums.ParseMode.MARKDOWN
            )
        return await query.answer(MSG_ALRT)
    elif query.data == "backcb":
        await query.answer()

        userid = query.from_user.id

        groupids = await all_connections(str(userid))
        if groupids is None:
            await query.message.edit_text(
                "There are no active connections!! Connect to some groups first.",
            )
            return await query.answer(MSG_ALRT)
        buttons = []
        for groupid in groupids:
            try:
                ttl = await client.get_chat(int(groupid))
                title = ttl.title
                active = await if_active(str(userid), str(groupid))
                act = " - ACTIVE" if active else ""
                buttons.append(
                    [
                        InlineKeyboardButton(
                            text=f"{title}{act}", callback_data=f"groupcb:{groupid}:{act}"
                        )
                    ]
                )
            except:
                pass
        if buttons:
            await query.message.edit_text(
                "Your connected group details ;\n\n",
                reply_markup=InlineKeyboardMarkup(buttons)
            )
    elif "gfilteralert" in query.data:
        grp_id = query.message.chat.id
        i = query.data.split(":")[1]
        keyword = query.data.split(":")[2]
        reply_text, btn, alerts, fileid = await find_gfilter('gfilters', keyword)
        if alerts is not None:
            alerts = ast.literal_eval(alerts)
            alert = alerts[int(i)]
            alert = alert.replace("\\n", "\n").replace("\\t", "\t")
            await query.answer(alert, show_alert=True)
    
    elif "alertmessage" in query.data:
        grp_id = query.message.chat.id
        i = query.data.split(":")[1]
        keyword = query.data.split(":")[2]
        reply_text, btn, alerts, fileid = await find_filter(grp_id, keyword)
        if alerts is not None:
            alerts = ast.literal_eval(alerts)
            alert = alerts[int(i)]
            alert = alert.replace("\\n", "\n").replace("\\t", "\t")
            await query.answer(alert, show_alert=True)
        
    if query.data.startswith("file"):
        clicked = query.from_user.id
        try:
            typed = query.message.reply_to_message.from_user.id
        except:
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
            except Exception as e:
                logger.exception(e)
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
        except Exception as e:
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
        except Exception as e:
            logger.exception(e)
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
                except:
                    return
        except:
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
            except Exception as e:
                logger.exception(e)
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
            except Exception as e:
                logger.exception(e)
                await query.message.edit_text(f'Error: {e}')
            else:
                await query.message.edit_text(f"<b>Process Completed for file deletion !\n\nSuccessfully deleted {str(deleted)} files from database for your query {keyword}.</b>")
    
    elif query.data.startswith("show_option"):
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
        except:
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
        except:
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
        except:
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
        except:
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
