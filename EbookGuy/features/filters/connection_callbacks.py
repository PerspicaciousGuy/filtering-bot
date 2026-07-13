import logging

from pyrogram import enums
from pyrogram.errors import RPCError
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from database.connections_mdb import (
    all_connections,
    delete_connection,
    if_active,
    make_active,
    make_inactive,
)
from info import MSG_ALRT


logger = logging.getLogger(__name__)
MARKDOWN = enums.ParseMode.MARKDOWN


async def _show_group(client, query):
    _, group_id, active_marker = query.data.split(":", 2)
    chat = await client.get_chat(int(group_id))
    is_active = bool(active_marker)
    action_text = "DISCONNECT" if is_active else "CONNECT"
    action_callback = "disconnect" if is_active else "connectcb"
    keyboard = InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    action_text,
                    callback_data=f"{action_callback}:{group_id}",
                ),
                InlineKeyboardButton(
                    "DELETE",
                    callback_data=f"deletecb:{group_id}",
                ),
            ],
            [InlineKeyboardButton("BACK", callback_data="backcb")],
        ]
    )
    await query.message.edit_text(
        f"Group Name : **{chat.title}**\nGroup ID : \x60{group_id}\x60",
        reply_markup=keyboard,
        parse_mode=MARKDOWN,
    )


async def _connect_group(client, query):
    _, group_id = query.data.split(":", 1)
    chat = await client.get_chat(int(group_id))
    is_active = await make_active(str(query.from_user.id), str(group_id))
    text = f"Connected to **{chat.title}**" if is_active else "Some error occurred!!"
    await query.message.edit_text(text, parse_mode=MARKDOWN)


async def _disconnect_group(client, query):
    _, group_id = query.data.split(":", 1)
    chat = await client.get_chat(int(group_id))
    is_inactive = await make_inactive(str(query.from_user.id))
    if is_inactive:
        text = f"Disconnected from **{chat.title}**"
    else:
        text = "Some error occurred!!"
    await query.message.edit_text(text, parse_mode=MARKDOWN)


async def _delete_group_connection(query):
    _, group_id = query.data.split(":", 1)
    was_deleted = await delete_connection(
        str(query.from_user.id),
        str(group_id),
    )
    if was_deleted:
        await query.message.edit_text("Successfully deleted connection !")
    else:
        await query.message.edit_text(
            "Some error occurred!!",
            parse_mode=MARKDOWN,
        )


async def _connection_buttons(client, user_id, group_ids):
    buttons = []
    for group_id in group_ids:
        try:
            chat = await client.get_chat(int(group_id))
            is_active = await if_active(str(user_id), str(group_id))
        except (RPCError, TypeError, ValueError):
            logger.debug(
                "Skipping unavailable saved connection",
                exc_info=True,
            )
            continue
        active_marker = " - ACTIVE" if is_active else ""
        buttons.append(
            [
                InlineKeyboardButton(
                    text=f"{chat.title}{active_marker}",
                    callback_data=f"groupcb:{group_id}:{active_marker}",
                )
            ]
        )
    return buttons


async def _show_connections(client, query):
    user_id = query.from_user.id
    group_ids = await all_connections(str(user_id))
    if group_ids is None:
        await query.message.edit_text(
            "There are no active connections!! Connect to some groups first."
        )
        return

    buttons = await _connection_buttons(client, user_id, group_ids)
    if buttons:
        await query.message.edit_text(
            "Your connected group details ;\n\n",
            reply_markup=InlineKeyboardMarkup(buttons),
        )


async def maybe_handle_connection_callback(client, query):
    action = query.data.partition(":")[0]
    handlers = {
        "groupcb": _show_group,
        "connectcb": _connect_group,
        "disconnect": _disconnect_group,
        "backcb": _show_connections,
    }
    if action == "deletecb":
        await _delete_group_connection(query)
    elif action in handlers:
        await handlers[action](client, query)
    else:
        return False
    await query.answer(MSG_ALRT)
    return True
