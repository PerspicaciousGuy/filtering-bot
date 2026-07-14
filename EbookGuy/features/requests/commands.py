import asyncio
import datetime
import logging
from dataclasses import dataclass
from html import escape

from pyrogram.errors import RPCError
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from database.users_chats_db import db
from EbookGuy.shared.global_settings import get_global_settings
from info import ADMINS, CHNL_LNK


logger = logging.getLogger(__name__)

MINIMUM_REQUEST_LENGTH = 3
MAXIMUM_REQUEST_LENGTH = 3500
REQUEST_MARKERS = ("#request", "/request", "#Request", "/Request")
EMPTY_REQUEST_MESSAGE = (
    "<b>You must type about your request [Minimum 3 Characters]. "
    "Requests can't be empty.</b>"
)
FORWARD_ERROR_MESSAGE = (
    "Something went wrong while sending your request. Please try again later."
)
_request_lock = asyncio.Lock()


def _utc_now():
    return datetime.datetime.now(datetime.timezone.utc).replace(tzinfo=None)


@dataclass(frozen=True)
class RequestSubmission:
    """Validated request data and its effective global settings."""

    bot: object
    message: object
    content: str
    normalized_content: str
    settings: dict[str, object]


def _extract_request_content(message):
    if message.reply_to_message:
        replied_message = message.reply_to_message
        return (replied_message.text or replied_message.caption or "").strip()

    content = message.text or ""
    for marker in REQUEST_MARKERS:
        content = content.replace(marker, "")
    return content.strip()


def _moderation_markup(reporter_id):
    return InlineKeyboardMarkup(
        [[
            InlineKeyboardButton(
                "Show Options",
                callback_data=f"show_option#{reporter_id}",
            )
        ]]
    )


def _request_text(message, content, includes_reporter_id):
    reporter_name = escape(message.from_user.first_name or "Unknown")
    if includes_reporter_id:
        reporter = f"{reporter_name} ({message.from_user.id})"
    else:
        reporter = reporter_name
    return (
        f"<b>Reporter :</b> <code>{reporter}</code>\n\n"
        f"<b>Message :</b> <code>{escape(content)}</code>"
    )


async def _forward_request(submission):
    message = submission.message
    reporter_id = str(message.from_user.id)
    reply_markup = _moderation_markup(reporter_id)
    channel_id = int(submission.settings["request_channel_id"])
    if channel_id:
        return await submission.bot.send_message(
            chat_id=channel_id,
            text=_request_text(message, submission.content, False),
            reply_markup=reply_markup,
        )

    reported_post = None
    for admin_id in ADMINS:
        reported_post = await submission.bot.send_message(
            chat_id=admin_id,
            text=_request_text(message, submission.content, True),
            reply_markup=reply_markup,
        )
    return reported_post


async def _request_confirmation_markup(submission, reported_post):
    channel_id = int(submission.settings["request_channel_id"])
    try:
        invite = await submission.bot.create_chat_invite_link(channel_id)
        channel_url = invite.invite_link
    except RPCError:
        channel_url = CHNL_LNK
    return InlineKeyboardMarkup(
        [[
            InlineKeyboardButton("Join Channel", url=channel_url),
            InlineKeyboardButton("View Request", url=reported_post.link),
        ]]
    )


async def _confirm_request(submission, reported_post):
    message = submission.message
    channel_id = int(submission.settings["request_channel_id"])
    if not submission.settings["request_notifications_enabled"]:
        await message.reply_text("<b>Your request has been submitted.</b>")
        return
    if not channel_id:
        await message.reply_text("<b>Your request has been sent to Admins!</b>")
        return

    reply_markup = await _request_confirmation_markup(submission, reported_post)
    await message.reply_text(
        "<b>Your request has been added! Please wait for some time.\n\n"
        "Join Channel First & View Request</b>",
        reply_markup=reply_markup,
    )


def _normalize_request(content):
    return " ".join(content.casefold().split())


async def _request_denial(submission):
    settings = submission.settings
    if not settings["requests_enabled"]:
        return "Book requests are temporarily disabled."
    request_date = _utc_now().date().isoformat()
    count = await db.get_daily_request_count(
        submission.message.from_user.id,
        request_date,
    )
    daily_limit = int(settings["request_daily_limit"])
    if daily_limit and count >= daily_limit:
        return f"You have reached today's limit of {daily_limit} request(s)."
    last_request = await db.get_last_request(submission.message.from_user.id)
    cooldown = int(settings["request_cooldown_seconds"])
    if last_request and cooldown:
        elapsed = _utc_now() - last_request["submitted_at"]
        remaining = cooldown - int(elapsed.total_seconds())
        if remaining > 0:
            return f"Please wait {remaining} second(s) before requesting again."
    if not settings["allow_duplicate_requests"]:
        if await db.request_exists(submission.normalized_content):
            return "That book has already been requested."
    return None


def _request_record(submission):
    submitted_at = _utc_now()
    return {
        "user_id": int(submission.message.from_user.id),
        "content": submission.content,
        "normalized_content": submission.normalized_content,
        "request_date": submitted_at.date().isoformat(),
        "submitted_at": submitted_at,
    }


async def _submit_request(submission):
    async with _request_lock:
        denial = await _request_denial(submission)
        if denial:
            await submission.message.reply_text(denial)
            return
        try:
            reported_post = await _forward_request(submission)
        except RPCError:
            logger.exception("Failed to forward request")
            await submission.message.reply_text(FORWARD_ERROR_MESSAGE)
            return
        if reported_post is None:
            logger.error("No request destination is configured")
            await submission.message.reply_text(FORWARD_ERROR_MESSAGE)
            return
        await db.record_request(_request_record(submission))
    try:
        await _confirm_request(submission, reported_post)
    except RPCError:
        logger.exception("Failed to send request confirmation")
        await submission.message.reply_text(
            "Your request was sent, but confirmation could not be displayed."
        )


async def handle_requests(bot, message):
    """Validate, limit, forward, and confirm a user book request."""
    settings = await get_global_settings()
    if not settings["requests_enabled"]:
        await message.reply_text("Book requests are temporarily disabled.")
        return
    content = _extract_request_content(message)
    if len(content) < MINIMUM_REQUEST_LENGTH:
        await message.reply_text(EMPTY_REQUEST_MESSAGE)
        return
    if len(content) > MAXIMUM_REQUEST_LENGTH:
        await message.reply_text(
            f"Keep the request under {MAXIMUM_REQUEST_LENGTH} characters."
        )
        return
    await db.ensure_request_indexes()
    submission = RequestSubmission(
        bot=bot,
        message=message,
        content=content,
        normalized_content=_normalize_request(content),
        settings=settings,
    )
    await _submit_request(submission)
