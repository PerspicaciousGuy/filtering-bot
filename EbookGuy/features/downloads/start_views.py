import random
from html import escape

from pyrogram import enums
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from Script import script
from info import PICS, START_BUTTONS
from EbookGuy.shared.global_settings import get_global_settings
from utils import temp


def get_start_buttons(settings=None):
    """Build the configured welcome-screen buttons."""
    buttons = [
        [InlineKeyboardButton(button["label"], url=button["url"])]
        for button in START_BUTTONS
    ]
    if settings is not None:
        support_url = str(settings["support_url"])
        if not any(button["url"] == support_url for button in START_BUTTONS):
            buttons.append([InlineKeyboardButton("Support", url=support_url)])
    return buttons


def _welcome_caption(message, settings):
    if not settings["welcome_message_enabled"]:
        free_limit = settings["free_daily_limit"] or "unlimited"
        return script.START_TXT.format(
            message.from_user.mention,
            temp.LIB_COUNT,
            free_limit,
        )
    user = message.from_user
    first_name = escape(user.first_name or "Reader")
    username = escape(f"@{user.username}" if user.username else "Not set")
    mention = f'<a href="tg://user?id={user.id}">{first_name}</a>'
    values = {
        "first_name": first_name,
        "username": username,
        "mention": mention,
        "bot_name": escape(str(temp.U_NAME)),
        "library_count": escape(str(temp.LIB_COUNT)),
        "free_limit": escape(str(settings["free_daily_limit"] or "unlimited")),
        "support_url": escape(str(settings["support_url"]), quote=True),
    }
    return str(settings["welcome_message_template"]).format(**values)


async def show_start_message(message):
    """Render the standard bot welcome message."""
    settings = await get_global_settings()
    await message.reply_photo(
        photo=random.choice(PICS),
        caption=_welcome_caption(message, settings),
        reply_markup=InlineKeyboardMarkup(get_start_buttons(settings)),
        parse_mode=enums.ParseMode.HTML,
    )
