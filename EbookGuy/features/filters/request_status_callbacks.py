"""Administrator and requester callbacks for book-request statuses."""

import asyncio
from dataclasses import dataclass
from datetime import datetime, timezone
from html import escape
import logging

from pyrogram.errors import RPCError
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from pymongo.errors import PyMongoError

from database.users_chats_db import db
from database.request_records_db import RequestStatusUpdate
from EbookGuy.features.requests.notifications import (
    ALERT_ACTIONS,
    REQUEST_STATUSES,
    STATUS_ACTIONS,
    RequestNotification,
    RequestStatusDefinition,
    notify_requester,
)
from EbookGuy.shared.analytics import track_event
from EbookGuy.shared.global_settings import get_global_settings
from info import ADMINS


ACCESS_DENIED_MESSAGE = "Only bot administrators can change request status."
logger = logging.getLogger(__name__)
_notification_tasks: set[asyncio.Task] = set()


@dataclass(frozen=True)
class StatusChange:
    """Context required to apply one request status transition."""

    query: object
    status: RequestStatusDefinition
    token: str


def _is_bot_admin(user) -> bool:
    identifiers = {str(admin).lower() for admin in ADMINS}
    user_id = str(getattr(user, "id", ""))
    username = str(getattr(user, "username", "")).lower()
    return user_id in identifiers or username in identifiers


def _parse_request_token(token: str) -> tuple[str | None, int]:
    request_id, separator, user_id = token.partition(":")
    if not separator:
        return None, int(request_id)
    if len(request_id) != 24:
        raise ValueError("Invalid request identifier")
    return request_id, int(user_id)


def _status_options_markup(token: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    "Unavailable",
                    callback_data=f"unavailable#{token}",
                ),
                InlineKeyboardButton(
                    "Uploaded",
                    callback_data=f"uploaded#{token}",
                ),
            ],
            [
                InlineKeyboardButton(
                    "Already Available",
                    callback_data=f"already_available#{token}",
                ),
                InlineKeyboardButton(
                    "Processing",
                    callback_data=f"processing#{token}",
                ),
            ],
        ]
    )


def _request_message_text(message) -> str:
    text = message.text or ""
    status_marker = "\n\nStatus:"
    if status_marker in text:
        return text.rsplit(status_marker, 1)[0]
    return text


def _status_markup(
    status: RequestStatusDefinition,
    token: str,
) -> InlineKeyboardMarkup:
    _, user_id = _parse_request_token(token)
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    status.button_text,
                    callback_data=f"rq_alert_{status.key}#{user_id}",
                )
            ],
            [
                InlineKeyboardButton(
                    "Change Status",
                    callback_data=f"show_option#{token}",
                )
            ],
        ]
    )


async def _show_status_options(query, token: str) -> None:
    await query.message.edit_text(
        f"<b>{escape(_request_message_text(query.message))}</b>",
        reply_markup=_status_options_markup(token),
    )


async def _apply_status_change(
    client,
    change: StatusChange,
) -> None:
    try:
        request_id, user_id = _parse_request_token(change.token)
        await change.query.message.edit_text(
            f"{escape(_request_message_text(change.query.message))}\n\n"
            f"<b>Status: {change.status.button_text}</b>",
            reply_markup=_status_markup(change.status, change.token),
        )
        changed_at = datetime.now(timezone.utc).replace(tzinfo=None)
        if request_id:
            await db.update_request_status(
                RequestStatusUpdate(
                    request_id=request_id,
                    status=change.status.key,
                    admin_id=change.query.from_user.id,
                    changed_at=changed_at,
                )
            )
        track_event(
            f"request.{change.status.key}",
            user_id,
            request_id=request_id or "legacy",
            admin_id=int(change.query.from_user.id),
        )
        settings = await get_global_settings()
        if settings["request_notifications_enabled"]:
            await notify_requester(RequestNotification(
                client=client,
                query=change.query,
                status=change.status,
                request_id=request_id,
                user_id=user_id,
                settings=settings,
            ))
    except (PyMongoError, RPCError, TypeError, ValueError):
        logger.exception("Failed to apply request status change")


def _retain_task(coroutine) -> None:
    task = asyncio.create_task(coroutine)
    _notification_tasks.add(task)
    task.add_done_callback(_notification_tasks.discard)


async def _show_requester_alert(query, status, user_id: str) -> None:
    if int(query.from_user.id) != int(user_id):
        await query.answer("This request does not belong to you.", show_alert=True)
        return
    await query.answer(status.requester_alert, show_alert=True)


async def maybe_handle_request_status_callback(client, query) -> bool:
    """Handle canonical and legacy request-status callback payloads."""
    action, separator, token = query.data.partition("#")
    if not separator:
        return False

    if action in {"show_option", "request_options"}:
        if not _is_bot_admin(query.from_user):
            await query.answer(ACCESS_DENIED_MESSAGE, show_alert=True)
            return True
        try:
            _parse_request_token(token)
        except ValueError:
            await query.answer("Invalid request.", show_alert=True)
            return True
        await query.answer("Choose the new request status")
        _retain_task(_show_status_options(query, token))
        return True

    status = STATUS_ACTIONS.get(action)
    if status is not None:
        if not _is_bot_admin(query.from_user):
            await query.answer(ACCESS_DENIED_MESSAGE, show_alert=True)
            return True
        try:
            _parse_request_token(token)
        except ValueError:
            await query.answer("Invalid request.", show_alert=True)
            return True
        await query.answer(status.confirmation)
        _retain_task(
            _apply_status_change(
                client,
                StatusChange(query=query, status=status, token=token),
            )
        )
        return True

    alert_status = ALERT_ACTIONS.get(action)
    if alert_status is None:
        return False
    await _show_requester_alert(query, alert_status, token)
    return True


__all__ = ["maybe_handle_request_status_callback"]
