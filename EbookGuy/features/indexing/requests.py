import logging
import re

from pyrogram import enums
from pyrogram.errors.exceptions.bad_request_400 import (
    ChannelInvalid,
    ChatAdminRequired,
    UsernameInvalid,
    UsernameNotModified,
)
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from database.ia_filterdb import get_checkpoint
from info import ADMINS, FILTER_BY_EXTENSION
from info import INDEX_REQ_CHANNEL as LOG_CHANNEL

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

async def handle_send_for_index(bot, message):
    msg = await bot.ask(message.chat.id, "**📥 Send me your channel's last post link or forward the last message from your index channel.**\n\n💡 Tips:\n• Use /setskip <number> to skip messages\n• Use /resume to continue paused indexing\n• Indexing auto-saves progress every 100 messages")
    if msg.forward_from_chat and msg.forward_from_chat.type == enums.ChatType.CHANNEL:
        last_msg_id = msg.forward_from_message_id
        chat_id = msg.forward_from_chat.username or msg.forward_from_chat.id
    elif msg.text:
        regex = re.compile("(https://)?(t\.me/|telegram\.me/|telegram\.dog/)(c/)?(\d+|[a-zA-Z_0-9]+)/(\d+)$")
        match = regex.match(msg.text)
        if not match:
            return await msg.reply('Invalid link\n\nTry again by /index')
        chat_id = match.group(4)
        last_msg_id = int(match.group(5))
        if chat_id.isnumeric():
            chat_id  = int(("-100" + chat_id))
    else:
        return
    try:
        await bot.get_chat(chat_id)
    except ChannelInvalid:
        return await msg.reply('This may be a private channel / group. Make me an admin over there to index the files.')
    except (UsernameInvalid, UsernameNotModified):
        return await msg.reply('Invalid Link specified.')
    except Exception:
        logger.exception("Failed to validate indexing target chat")
        return await msg.reply('Unable to verify this chat right now. Please try again later.')
    try:
        k = await bot.get_messages(chat_id, last_msg_id)
    except Exception:
        logger.exception("Failed to fetch indexing target message")
        return await message.reply('Make sure I am an admin in the channel, if the channel is private.')
    if k.empty:
        return await message.reply('This may be group and I am not an admin of the group.')

    if message.from_user.id in ADMINS:
        # Check for existing checkpoint
        existing = get_checkpoint(chat_id if isinstance(chat_id, int) else chat_id)
        resume_text = ""
        if existing:
            resume_text = f"\n\n⚠️ **Found saved progress at message {existing['current_msg']}**\nUse /resume to continue or start fresh."
        
        buttons = [[
            InlineKeyboardButton('✅ Yes, Start Indexing', callback_data=f'index#accept#{chat_id}#{last_msg_id}#{message.from_user.id}')
        ],[
            InlineKeyboardButton('❌ Close', callback_data='close_data')
        ]]
        reply_markup = InlineKeyboardMarkup(buttons)
        filter_status = "✅ Enabled (ebooks/audiobooks only)" if FILTER_BY_EXTENSION else "❌ Disabled (all files)"
        return await message.reply(
            f'📥 **Index This Channel/Group?**\n\n'
            f'📋 Chat ID: `{chat_id}`\n'
            f'📨 Last Message: `{last_msg_id}`\n'
            f'🔍 Extension Filter: {filter_status}'
            f'{resume_text}',
            reply_markup=reply_markup
        )

    if type(chat_id) is int:
        try:
            link = (await bot.create_chat_invite_link(chat_id)).invite_link
        except ChatAdminRequired:
            return await message.reply('Make sure I am an admin in the chat and have permission to invite users.')
    else:
        link = f"@{chat_id}"
    buttons = [[
        InlineKeyboardButton('Accept Index', callback_data=f'index#accept#{chat_id}#{last_msg_id}#{message.from_user.id}')
    ],[
        InlineKeyboardButton('Reject Index', callback_data=f'index#reject#{chat_id}#{message.id}#{message.from_user.id}'),
    ]]
    reply_markup = InlineKeyboardMarkup(buttons)
    await bot.send_message(
        LOG_CHANNEL,
        f'#IndexRequest\n\nBy : {message.from_user.mention} (`{message.from_user.id}`)\nChat ID/Username: `{chat_id}`\nLast Message ID: `{last_msg_id}`\nInviteLink: {link}',
        reply_markup=reply_markup
    )
    await message.reply('Thank you for the contribution! Wait for our moderators to verify the files.')
