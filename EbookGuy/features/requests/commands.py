import logging

from pyrogram.errors import RPCError
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from info import ADMINS, CHNL_LNK, REQST_CHANNEL


logger = logging.getLogger(__name__)

MINIMUM_REQUEST_LENGTH = 3
REQUEST_MARKERS = ("#request", "/request", "#Request", "/Request")
EMPTY_REQUEST_MESSAGE = (
    "<b>You must type about your request [Minimum 3 Characters]. "
    "Requests can't be empty.</b>"
)
FORWARD_ERROR_MESSAGE = (
    "Something went wrong while sending your request. Please try again later."
)


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
    if includes_reporter_id:
        reporter = f"{message.from_user.mention} ({message.from_user.id})"
    else:
        reporter = message.from_user.first_name
    return (
        f"<b>Reporter :</b> <code>{reporter}</code>\n\n"
        f"<b>Message :</b> <code>{content}</code>"
    )


async def _forward_request(bot, message, content):
    reporter_id = str(message.from_user.id)
    reply_markup = _moderation_markup(reporter_id)
    if REQST_CHANNEL is not None:
        return await bot.send_message(
            chat_id=REQST_CHANNEL,
            text=_request_text(message, content, False),
            reply_markup=reply_markup,
        )

    reported_post = None
    for admin_id in ADMINS:
        reported_post = await bot.send_message(
            chat_id=admin_id,
            text=_request_text(message, content, True),
            reply_markup=reply_markup,
        )
    return reported_post


async def _request_confirmation_markup(bot, reported_post):
    try:
        invite = await bot.create_chat_invite_link(int(REQST_CHANNEL))
        channel_url = invite.invite_link
    except RPCError:
        channel_url = CHNL_LNK
    return InlineKeyboardMarkup(
        [[
            InlineKeyboardButton("Join Channel", url=channel_url),
            InlineKeyboardButton("View Request", url=reported_post.link),
        ]]
    )


async def _confirm_request(bot, message, reported_post):
    if REQST_CHANNEL is None:
        await message.reply_text("<b>Your request has been sent to Admins!</b>")
        return

    reply_markup = await _request_confirmation_markup(bot, reported_post)
    await message.reply_text(
        "<b>Your request has been added! Please wait for some time.\n\n"
        "Join Channel First & View Request</b>",
        reply_markup=reply_markup,
    )


async def handle_requests(bot, message):
    """Validate, forward, and confirm a user book request."""
    content = _extract_request_content(message)
    if len(content) < MINIMUM_REQUEST_LENGTH:
        await message.reply_text(EMPTY_REQUEST_MESSAGE)
        return

    try:
        reported_post = await _forward_request(bot, message, content)
    except RPCError:
        logger.exception("Failed to forward request")
        await message.reply_text(FORWARD_ERROR_MESSAGE)
        return

    if reported_post is None:
        logger.error("Request could not be forwarded because no destination is configured")
        await message.reply_text(FORWARD_ERROR_MESSAGE)
        return

    try:
        await _confirm_request(bot, message, reported_post)
    except RPCError:
        logger.exception("Failed to send request confirmation")
        await message.reply_text(
            "Your request was sent, but I could not send the confirmation message."
        )
