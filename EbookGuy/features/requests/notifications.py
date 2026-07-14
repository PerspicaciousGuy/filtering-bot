"""Request status definitions and configurable user notifications."""

from dataclasses import dataclass
from html import escape
import logging

from pyrogram.errors import RPCError, UserIsBlocked
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from database.users_chats_db import db
from info import CHNL_LNK


logger = logging.getLogger(__name__)
BLOCKED_USER_NOTE = (
    "\n\nThe requester blocked the bot, so this notification was sent here."
)


@dataclass(frozen=True)
class RequestStatusDefinition:
    """Display and template metadata for one canonical request status."""

    key: str
    button_text: str
    template_setting: str
    confirmation: str
    requester_alert: str


@dataclass(frozen=True)
class RequestNotification:
    """Context required to render and send a request status notification."""

    client: object
    query: object
    status: RequestStatusDefinition
    request_id: str | None
    user_id: int
    settings: dict[str, object]


REQUEST_STATUSES = {
    "unavailable": RequestStatusDefinition(
        key="unavailable",
        button_text="Unavailable",
        template_setting="request_unavailable_message",
        confirmation="Set to Unavailable",
        requester_alert="Your request is unavailable.",
    ),
    "uploaded": RequestStatusDefinition(
        key="uploaded",
        button_text="Uploaded",
        template_setting="request_uploaded_message",
        confirmation="Set to Uploaded",
        requester_alert="Your request has been uploaded.",
    ),
    "already_available": RequestStatusDefinition(
        key="already_available",
        button_text="Already Available",
        template_setting="request_already_available_message",
        confirmation="Set to Already Available",
        requester_alert="Your request is already available.",
    ),
    "processing": RequestStatusDefinition(
        key="processing",
        button_text="Processing",
        template_setting="request_processing_message",
        confirmation="Set to Processing",
        requester_alert="Your request is processing.",
    ),
}

STATUS_ACTIONS = {
    "unavailable": REQUEST_STATUSES["unavailable"],
    "uploaded": REQUEST_STATUSES["uploaded"],
    "already_available": REQUEST_STATUSES["already_available"],
    "processing": REQUEST_STATUSES["processing"],
    "rq_accept": REQUEST_STATUSES["processing"],
    "rq_reject": REQUEST_STATUSES["unavailable"],
    "rq_complete": REQUEST_STATUSES["uploaded"],
}

ALERT_ACTIONS = {
    "rq_alert_unavailable": REQUEST_STATUSES["unavailable"],
    "rq_alert_uploaded": REQUEST_STATUSES["uploaded"],
    "rq_alert_already_available": REQUEST_STATUSES["already_available"],
    "rq_alert_processing": REQUEST_STATUSES["processing"],
    "rq_alert_accepted": REQUEST_STATUSES["processing"],
    "rq_alert_rejected": REQUEST_STATUSES["unavailable"],
    "rq_alert_completed": REQUEST_STATUSES["uploaded"],
    "unalert": REQUEST_STATUSES["unavailable"],
    "upalert": REQUEST_STATUSES["uploaded"],
    "alalert": REQUEST_STATUSES["already_available"],
    "proalert": REQUEST_STATUSES["processing"],
}

AVAILABLE_STATUS_KEYS = {"uploaded", "already_available"}


async def _request_channel_link(client, channel_id: int) -> str:
    if not channel_id:
        return CHNL_LNK
    try:
        chat = await client.get_chat(channel_id)
        if chat.username:
            return f"https://t.me/{chat.username}"
        if chat.invite_link:
            return chat.invite_link
        invite = await client.create_chat_invite_link(channel_id)
    except RPCError:
        logger.exception("Failed to build the request channel link")
        return CHNL_LNK
    return invite.invite_link


async def _notification_markup(notification: RequestNotification):
    rows = []
    if notification.status.key in AVAILABLE_STATUS_KEYS:
        try:
            bot = await notification.client.get_me()
        except RPCError:
            logger.exception("Failed to build the request search link")
        else:
            if bot.username:
                rows.append([
                    InlineKeyboardButton(
                        "Open Bot & Search",
                        url=f"https://t.me/{bot.username}",
                    )
                ])
    buttons = []
    channel_url = await _request_channel_link(
        notification.client,
        int(notification.settings["request_channel_id"]),
    )
    if channel_url:
        buttons.append(InlineKeyboardButton("Request Channel", url=channel_url))
    message_link = getattr(notification.query.message, "link", None)
    if message_link:
        buttons.append(InlineKeyboardButton("View Status", url=message_link))
    if buttons:
        rows.append(buttons)
    return InlineKeyboardMarkup(rows) if rows else None


def _template_values(user, record, request_id: str | None) -> dict[str, str]:
    return {
        "user_name": escape(user.first_name or "Reader"),
        "book_title": escape(str((record or {}).get("title", "your book"))),
        "author_name": escape(str((record or {}).get("author", "Not provided"))),
        "request_id": escape(request_id or "legacy"),
        "reason": "Not provided",
        "download_link": "Open the bot and search for the book now.",
    }


async def notify_requester(notification: RequestNotification) -> None:
    """Render the configured status template and notify its requester."""
    record = None
    if notification.request_id:
        record = await db.get_request_record(notification.request_id)
    user = await notification.client.get_users(notification.user_id)
    template = str(notification.settings[notification.status.template_setting])
    text = template.format(
        **_template_values(user, record, notification.request_id)
    )
    reply_markup = await _notification_markup(notification)
    try:
        await notification.client.send_message(
            chat_id=notification.user_id,
            text=text,
            reply_markup=reply_markup,
        )
    except UserIsBlocked:
        support_chat_id = int(notification.settings["support_chat_id"])
        if not support_chat_id:
            logger.info("Requester blocked the bot and no fallback chat exists")
            return
        await notification.client.send_message(
            chat_id=support_chat_id,
            text=text + BLOCKED_USER_NOTE,
            reply_markup=reply_markup,
        )


__all__ = [
    "ALERT_ACTIONS",
    "REQUEST_STATUSES",
    "STATUS_ACTIONS",
    "RequestNotification",
    "RequestStatusDefinition",
    "notify_requester",
]
