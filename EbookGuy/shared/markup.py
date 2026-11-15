"""Reusable Telegram inline keyboard builders."""

from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup


def single_button_markup(label: str, callback_data: str) -> InlineKeyboardMarkup:
    """Build an inline keyboard holding one callback button."""
    return InlineKeyboardMarkup([[
        InlineKeyboardButton(label, callback_data=callback_data)
    ]])
