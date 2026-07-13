import logging

from pyrogram import enums
from pyrogram.errors import RPCError

from database.connections_mdb import active_connection
from database.filters_mdb import del_all
from database.gfilters_mdb import del_allg
from info import ADMINS, MSG_ALRT


logger = logging.getLogger(__name__)
GROUP_TYPES = {enums.ChatType.GROUP, enums.ChatType.SUPERGROUP}


async def _delete_global_filters(query):
    await del_allg(query.message, "gfilters")
    await query.answer("Done !")


async def _cancel_global_filter_delete(query):
    await query.message.reply_to_message.delete()
    await query.message.delete()
    await query.answer("Process Cancelled !")


async def _resolve_group(client, query):
    chat_type = query.message.chat.type
    if chat_type in GROUP_TYPES:
        return query.message.chat.id, query.message.chat.title
    if chat_type != enums.ChatType.PRIVATE:
        await query.answer(MSG_ALRT)
        return None

    group_id = await active_connection(str(query.from_user.id))
    if group_id is None:
        await query.message.edit_text(
            "I'm not connected to any groups!\n"
            "Check /connections or connect to any groups"
        )
        await query.answer(MSG_ALRT)
        return None
    try:
        chat = await client.get_chat(group_id)
    except RPCError:
        await query.message.edit_text(
            "Make sure I'm present in your group!!"
        )
        await query.answer(MSG_ALRT)
        return None
    return group_id, chat.title


async def _can_manage_filters(client, query, group_id):
    member = await client.get_chat_member(
        group_id,
        query.from_user.id,
    )
    user_id = query.from_user.id
    is_admin = user_id in ADMINS or str(user_id) in ADMINS
    return member.status == enums.ChatMemberStatus.OWNER or is_admin


async def _confirm_filter_delete(client, query):
    group = await _resolve_group(client, query)
    if group is None:
        return
    group_id, title = group
    if await _can_manage_filters(client, query, group_id):
        await del_all(query.message, group_id, title)
        return
    await query.answer(
        "You need to be Group Owner or an Auth User to do that!",
        show_alert=True,
    )


async def _cancel_filter_delete(client, query):
    chat_type = query.message.chat.type
    if chat_type == enums.ChatType.PRIVATE:
        await query.message.reply_to_message.delete()
        await query.message.delete()
        return
    if chat_type not in GROUP_TYPES:
        return

    group_id = query.message.chat.id
    if not await _can_manage_filters(client, query, group_id):
        await query.answer("That's not for you!!", show_alert=True)
        return
    await query.message.delete()
    try:
        await query.message.reply_to_message.delete()
    except RPCError:
        logger.debug(
            "Replied filter message was already unavailable",
            exc_info=True,
        )


async def maybe_handle_filter_management_callback(client, query):
    handlers = {
        "gfiltersdeleteallconfirm": _delete_global_filters,
        "gfiltersdeleteallcancel": _cancel_global_filter_delete,
        "delallconfirm": _confirm_filter_delete,
        "delallcancel": _cancel_filter_delete,
    }
    handler = handlers.get(query.data)
    if handler is None:
        return False
    if query.data.startswith("gfilters"):
        await handler(query)
    else:
        await handler(client, query)
    return True
