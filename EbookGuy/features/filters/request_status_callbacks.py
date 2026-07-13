from dataclasses import dataclass

from pyrogram.errors import RPCError, UserIsBlocked
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from Script import script
from info import ADMINS, CHNL_LNK, REQST_CHANNEL, SUPPORT_CHAT_ID


ACCESS_DENIED_MESSAGE = "You don't have sufficient rights to do this !"
BLOCKED_USER_NOTE = (
    "\n\nNote: This message is sent to this group because you've blocked the bot. "
    "To send this message to your PM, Must unblock the bot."
)


@dataclass(frozen=True)
class RequestStatus:
    button_text: str
    alert_callback: str
    notification_template: str
    confirmation: str
    requester_alert: str
    includes_back_button: bool = False


@dataclass(frozen=True)
class StatusSelection:
    status: RequestStatus
    from_user: str


@dataclass(frozen=True)
class RequestNotification:
    query: object
    selection: StatusSelection
    user: object


REQUEST_STATUSES = {
    "unavailable": RequestStatus(
        button_text="\u26a0\ufe0f Unavailable \u26a0\ufe0f",
        alert_callback="unalert",
        notification_template=script.REQ_UNAVAILABLE,
        confirmation="Set to Unavailable !",
        requester_alert="Your Request is Unavailable !",
        includes_back_button=True,
    ),
    "uploaded": RequestStatus(
        button_text="\u2705 Uploaded \u2705",
        alert_callback="upalert",
        notification_template=script.REQ_UPLOADED,
        confirmation="Set to Uploaded !",
        requester_alert="Your Request is Uploaded !",
    ),
    "already_available": RequestStatus(
        button_text="\U0001f7e2 Already Available \U0001f7e2",
        alert_callback="alalert",
        notification_template=script.REQ_ALREADY_EXIST,
        confirmation="Set to Already Available !",
        requester_alert="Your Request is Already Available !",
    ),
    "processing": RequestStatus(
        button_text="\u23f3 Processing \u23f3",
        alert_callback="proalert",
        notification_template=script.REQ_PROCESSING,
        confirmation="Set to Processing !",
        requester_alert="Your Request is Processing !",
        includes_back_button=True,
    ),
}
ALERT_STATUSES = {
    status.alert_callback: status for status in REQUEST_STATUSES.values()
}


def _status_markup(selection):
    buttons = [
        InlineKeyboardButton(
            selection.status.button_text,
            callback_data=(
                f"{selection.status.alert_callback}#{selection.from_user}"
            ),
        )
    ]
    if selection.status.includes_back_button:
        buttons.append(
            InlineKeyboardButton(
                "\U0001f519 Back",
                callback_data=f"show_option#{selection.from_user}",
            )
        )
    return InlineKeyboardMarkup([buttons])


async def _notification_markup(client, query):
    try:
        link = await client.create_chat_invite_link(int(REQST_CHANNEL))
        channel_url = link.invite_link
    except RPCError:
        channel_url = CHNL_LNK
    return InlineKeyboardMarkup(
        [[
            InlineKeyboardButton("Join Channel", url=channel_url),
            InlineKeyboardButton("View Status", url=query.message.link),
        ]]
    )


async def _notify_requester(client, notification):
    selection = notification.selection
    text = selection.status.notification_template.format(
        notification.user.mention
    )
    reply_markup = await _notification_markup(client, notification.query)
    try:
        await client.send_message(
            chat_id=int(selection.from_user),
            text=text,
            reply_markup=reply_markup,
        )
    except UserIsBlocked:
        await client.send_message(
            chat_id=int(SUPPORT_CHAT_ID),
            text=text + BLOCKED_USER_NOTE,
            reply_markup=reply_markup,
        )


async def _show_status_options(query, from_user):
    buttons = [
        [
            InlineKeyboardButton(
                "Unavailable", callback_data=f"unavailable#{from_user}"
            ),
            InlineKeyboardButton(
                "Uploaded", callback_data=f"uploaded#{from_user}"
            ),
        ],
        [
            InlineKeyboardButton(
                "Already Available",
                callback_data=f"already_available#{from_user}",
            ),
            InlineKeyboardButton(
                "Processing", callback_data=f"processing#{from_user}"
            ),
        ],
    ]
    await query.message.edit_text(
        f"<b>{query.message.text}</b>",
        reply_markup=InlineKeyboardMarkup(buttons),
    )
    await query.answer("Here are the options !")


async def _set_request_status(client, query, selection):
    user = await client.get_users(selection.from_user)
    await query.message.edit_text(
        f"<b><strike>{query.message.text}</strike></b>",
        reply_markup=_status_markup(selection),
    )
    await query.answer(selection.status.confirmation)
    await _notify_requester(
        client,
        RequestNotification(query=query, selection=selection, user=user),
    )


async def _show_requester_alert(client, query, selection):
    if int(query.from_user.id) != int(selection.from_user):
        await query.answer(ACCESS_DENIED_MESSAGE, show_alert=True)
        return
    user = await client.get_users(selection.from_user)
    await query.answer(
        f"Hey {user.first_name}, {selection.status.requester_alert}",
        show_alert=True,
    )


async def maybe_handle_request_status_callback(client, query):
    action, separator, from_user = query.data.partition("#")
    if not separator:
        return False

    if action in REQUEST_STATUSES or action == "show_option":
        if query.from_user.id not in ADMINS:
            await query.answer(ACCESS_DENIED_MESSAGE, show_alert=True)
            return True
        if action == "show_option":
            await _show_status_options(query, from_user)
        else:
            await _set_request_status(
                client,
                query,
                StatusSelection(REQUEST_STATUSES[action], from_user),
            )
        return True

    status = ALERT_STATUSES.get(action)
    if status is None:
        return False
    await _show_requester_alert(
        client,
        query,
        StatusSelection(status, from_user),
    )
    return True
