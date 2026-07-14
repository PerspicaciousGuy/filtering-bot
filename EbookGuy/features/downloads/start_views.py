import random

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


async def show_start_message(message):
    """Render the standard bot welcome message."""
    settings = await get_global_settings()
    free_limit = settings["free_daily_limit"] or "unlimited"
    await message.reply_photo(
        photo=random.choice(PICS),
        caption=script.START_TXT.format(
            message.from_user.mention,
            temp.LIB_COUNT,
            free_limit,
        ),
        reply_markup=InlineKeyboardMarkup(get_start_buttons(settings)),
        parse_mode=enums.ParseMode.HTML,
    )
