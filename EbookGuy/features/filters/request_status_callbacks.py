import asyncio
import logging
from dataclasses import dataclass

from pyrogram.errors import RPCError, UserIsBlocked
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from Script import script
from info import ADMINS, CHNL_LNK, SUPPORT_CHAT_ID
from EbookGuy.shared.global_settings import get_global_settings


ACCESS_DENIED_MESSAGE = "You don't have sufficient rights to do this !"
logger = logging.getLogger(__name__)
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
    settings: dict[str, object]


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
_request_channel_urls = {}
_request_channel_lock = asyncio.Lock()
_notification_tasks = set()


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


async def _request_channel_link(client, channel_id):
    if not channel_id:
        return CHNL_LNK
    if channel_id in _request_channel_urls:
        return _request_channel_urls[channel_id]
    async with _request_channel_lock:
        if channel_id in _request_channel_urls:
            return _request_channel_urls[channel_id]
        try:
            link = await client.create_chat_invite_link(channel_id)
            channel_url = link.invite_link
        except RPCError:
            channel_url = CHNL_LNK
        _request_channel_urls[channel_id] = channel_url
    return channel_url


async def _notification_markup(client, query, channel_id):
    channel_url = await _request_channel_link(client, channel_id)
    return InlineKeyboardMarkup(
        [[
            InlineKeyboardButton("Join Channel", url=channel_url),
            InlineKeyboardButton("View Status", url=query.message.link),
        ]]
    )


async def _notify_requester(client, notification):
    settings = notification.settings
    selection = notification.selection
    text = selection.status.notification_template.format(
        notification.user.mention
    )
    reply_markup = await _notification_markup(
        client,
        notification.query,
        int(settings["request_channel_id"]),
    )
    try:
        await client.send_message(
            chat_id=int(selection.from_user),
            text=text,
            reply_markup=reply_markup,
        )
    except UserIsBlocked:
        if SUPPORT_CHAT_ID is None:
            logger.info("Requester blocked notification and no fallback chat exists")
            return
        await client.send_message(
            chat_id=int(SUPPORT_CHAT_ID),
            text=text + BLOCKED_USER_NOTE,
            reply_markup=reply_markup,
        )


def _status_options_markup(from_user):
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
    return InlineKeyboardMarkup(buttons)


async def _edit_status_options(query, from_user):
    try:
        await query.message.edit_text(
            f"<b>{query.message.text}</b>",
            reply_markup=_status_options_markup(from_user),
        )
    except RPCError:
        logger.exception("Failed to show request status options")


async def _apply_status_change(client, query, selection):
    try:
        await query.message.edit_text(
            f"<b><strike>{query.message.text}</strike></b>",
            reply_markup=_status_markup(selection),
        )
        settings = await get_global_settings()
        if not settings["request_notifications_enabled"]:
            return
        user = await client.get_users(selection.from_user)
        notification = RequestNotification(
            query=query,
            selection=selection,
            user=user,
            settings=settings,
        )
        await _notify_requester(client, notification)
    except (RPCError, TypeError, ValueError):
        logger.exception("Failed to apply request status change")


def _retain_task(coroutine):
    task = asyncio.create_task(coroutine)
    _notification_tasks.add(task)
    task.add_done_callback(_notification_tasks.discard)


async def _set_request_status(client, query, selection):
    await query.answer(selection.status.confirmation)
    _retain_task(
        _apply_status_change(client, query, selection)
    )


async def _show_requester_alert(client, query, selection):
    if int(query.from_user.id) != int(selection.from_user):
        await query.answer(ACCESS_DENIED_MESSAGE, show_alert=True)
        return
    await query.answer(
        f"Hey {query.from_user.first_name}, "
        f"{selection.status.requester_alert}",
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
            await query.answer("Here are the options !")
            _retain_task(_edit_status_options(query, from_user))
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
