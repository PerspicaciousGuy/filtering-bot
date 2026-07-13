import random

from pyrogram import enums
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from Script import script
from info import PICS, START_BUTTONS
from utils import temp


def get_start_buttons():
    """Build the configured welcome-screen buttons."""
    return [
        [InlineKeyboardButton(button["label"], url=button["url"])]
        for button in START_BUTTONS
    ]


async def show_start_message(message):
    """Render the standard bot welcome message."""
    await message.reply_photo(
        photo=random.choice(PICS),
        caption=script.START_TXT.format(
            message.from_user.mention,
            temp.LIB_COUNT,
        ),
        reply_markup=InlineKeyboardMarkup(get_start_buttons()),
        parse_mode=enums.ParseMode.HTML,
    )
