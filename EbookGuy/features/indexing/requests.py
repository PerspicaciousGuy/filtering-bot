import logging
import re
from dataclasses import dataclass

from pyrogram import enums
from pyrogram.errors import RPCError
from pyrogram.errors.exceptions.bad_request_400 import (
    ChannelInvalid,
    ChatAdminRequired,
    UsernameInvalid,
    UsernameNotModified,
)
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from database.indexing_checkpoints import get_checkpoint
from EbookGuy.shared.global_settings import get_global_settings
from info import ADMINS, FILTER_BY_EXTENSION


logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
INDEX_LINK_PATTERN = re.compile(
    r"(https://)?(t\.me/|telegram\.me/|telegram\.dog/)"
    r"(c/)?(\d+|[a-zA-Z_0-9]+)/(\d+)$"
)


@dataclass(frozen=True)
class IndexTarget:
    chat_id: int | str
    last_message_id: int


async def _parse_index_target(response):
    forwarded_chat = response.forward_from_chat
    if (
        forwarded_chat
        and forwarded_chat.type == enums.ChatType.CHANNEL
    ):
        return IndexTarget(
            chat_id=forwarded_chat.username or forwarded_chat.id,
            last_message_id=response.forward_from_message_id,
        )
    if not response.text:
        return None

    match = INDEX_LINK_PATTERN.match(response.text)
    if not match:
        await response.reply("Invalid link\n\nTry again by /index")
        return None
    chat_id = match.group(4)
    if chat_id.isnumeric():
        chat_id = int("-100" + chat_id)
    return IndexTarget(
        chat_id=chat_id,
        last_message_id=int(match.group(5)),
    )


async def _validate_index_target(bot, response, target):
    try:
        await bot.get_chat(target.chat_id)
    except ChannelInvalid:
        await response.reply(
            "This may be a private channel / group. Make me an admin "
            "over there to index the files."
        )
        return False
    except (UsernameInvalid, UsernameNotModified):
        await response.reply("Invalid Link specified.")
        return False
    except RPCError:
        logger.exception("Failed to validate indexing target chat")
        await response.reply(
            "Unable to verify this chat right now. "
            "Please try again later."
        )
        return False

    try:
        last_message = await bot.get_messages(
            target.chat_id,
            target.last_message_id,
        )
    except RPCError:
        logger.exception("Failed to fetch indexing target message")
        await response.reply(
            "Make sure I am an admin in the channel, "
            "if the channel is private."
        )
        return False
    if last_message.empty:
        await response.reply(
            "This may be group and I am not an admin of the group."
        )
        return False
    return True


async def _show_admin_index_prompt(message, target):
    checkpoint = await get_checkpoint(target.chat_id)
    resume_text = ""
    if checkpoint:
        resume_text = (
            "\n\n\u26a0\ufe0f **Found saved progress at message "
            f"{checkpoint['current_msg']}**\n"
            "Use /resume to continue or start fresh."
        )
    buttons = [
        [
            InlineKeyboardButton(
                "\u2705 Yes, Start Indexing",
                callback_data=(
                    f"index#accept#{target.chat_id}#"
                    f"{target.last_message_id}#{message.from_user.id}"
                ),
            )
        ],
        [
            InlineKeyboardButton(
                "\u274c Close",
                callback_data="close_data",
            )
        ],
    ]
    filter_status = (
        "\u2705 Enabled (ebooks/audiobooks only)"
        if FILTER_BY_EXTENSION
        else "\u274c Disabled (all files)"
    )
    await message.reply(
        "\U0001f4e5 **Index This Channel/Group?**\n\n"
        f"\U0001f4cb Chat ID: \x60{target.chat_id}\x60\n"
        f"\U0001f4e8 Last Message: \x60{target.last_message_id}\x60\n"
        f"\U0001f50d Extension Filter: {filter_status}"
        f"{resume_text}",
        reply_markup=InlineKeyboardMarkup(buttons),
    )


def _index_request_markup(target, message):
    buttons = [
        [
            InlineKeyboardButton(
                "Accept Index",
                callback_data=(
                    f"index#accept#{target.chat_id}#"
                    f"{target.last_message_id}#{message.from_user.id}"
                ),
            )
        ],
        [
            InlineKeyboardButton(
                "Reject Index",
                callback_data=(
                    f"index#reject#{target.chat_id}#"
                    f"{message.id}#{message.from_user.id}"
                ),
            )
        ],
    ]
    return InlineKeyboardMarkup(buttons)


async def _submit_index_request(bot, message, target):
    settings = await get_global_settings()
    channel_id = int(settings["index_request_channel_id"])
    channel_id = channel_id or int(settings["log_channel_id"])
    if not channel_id:
        await message.reply("Index requests are temporarily unavailable.")
        return
    if isinstance(target.chat_id, int):
        try:
            invite = await bot.create_chat_invite_link(target.chat_id)
        except ChatAdminRequired:
            await message.reply(
                "Make sure I am an admin in the chat and have "
                "permission to invite users."
            )
            return
        invite_link = invite.invite_link
    else:
        invite_link = f"@{target.chat_id}"

    await bot.send_message(
        channel_id,
        "#IndexRequest\n\n"
        f"By : {message.from_user.mention} "
        f"(\x60{message.from_user.id}\x60)\n"
        f"Chat ID/Username: \x60{target.chat_id}\x60\n"
        f"Last Message ID: \x60{target.last_message_id}\x60\n"
        f"InviteLink: {invite_link}",
        reply_markup=_index_request_markup(target, message),
    )
    await message.reply(
        "Thank you for the contribution! Wait for our moderators "
        "to verify the files."
    )


async def handle_send_for_index(bot, message):
    settings = await get_global_settings()
    if not settings["indexing_enabled"]:
        await message.reply("Indexing is temporarily disabled.")
        return
    response = await bot.ask(
        message.chat.id,
        "**\U0001f4e5 Send me your channel's last post link or "
        "forward the last message from your index channel.**\n\n"
        "\U0001f4a1 Tips:\n"
        "\u2022 Use /setskip <number> to skip messages\n"
        "\u2022 Use /resume to continue paused indexing\n"
        "\u2022 Indexing auto-saves progress every 100 messages",
    )
    target = await _parse_index_target(response)
    if target is None:
        return
    if not await _validate_index_target(bot, response, target):
        return
    if message.from_user.id in ADMINS:
        await _show_admin_index_prompt(message, target)
        return
    await _submit_index_request(bot, message, target)
