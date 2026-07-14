"""Admin command and views for global bot settings."""

import logging
from html import escape

from pyrogram.errors import RPCError
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from pymongo.errors import PyMongoError

from EbookGuy.shared.global_settings import get_global_settings
from EbookGuy.shared.settings_catalog import (
    CATEGORY_LABELS,
    CATEGORY_SETTINGS,
    SETTING_DESCRIPTIONS,
    SETTING_LABELS,
    get_setting_category,
)
from EbookGuy.shared.settings_schema import (
    DEFAULT_GLOBAL_SETTINGS,
    is_boolean_setting,
    is_editable_setting,
)


CALLBACK_PREFIX = "global_settings"
MAX_DISPLAY_LENGTH = 70
logger = logging.getLogger(__name__)


def _display_value(value: object) -> str:
    if isinstance(value, bool):
        return "Enabled" if value else "Disabled"
    if value == 0:
        return "Unlimited / not set"
    if isinstance(value, (list, tuple)):
        text = ", ".join(str(item) for item in value) or "None"
    else:
        text = str(value).replace("\n", " ")
    if len(text) > MAX_DISPLAY_LENGTH:
        text = f"{text[:MAX_DISPLAY_LENGTH]}..."
    return escape(text)


def build_settings_dashboard() -> tuple[str, InlineKeyboardMarkup]:
    """Build the global settings category dashboard."""
    buttons = [
        [
            InlineKeyboardButton(
                label,
                callback_data=f"{CALLBACK_PREFIX}:category:{key}",
            )
        ]
        for key, label in CATEGORY_LABELS.items()
    ]
    buttons.append(
        [
            InlineKeyboardButton(
                "Analytics",
                callback_data="global_settings:analytics:overview:7d",
            )
        ]
    )
    buttons.append(
        [InlineKeyboardButton("Close", callback_data=f"{CALLBACK_PREFIX}:close")]
    )
    text = (
        "<b>Global Bot Settings</b>\n\n"
        "Select a category to view its current values."
    )
    return text, InlineKeyboardMarkup(buttons)


def build_category_view(category: str) -> tuple[str, InlineKeyboardMarkup]:
    """Build a compact list of settings in one category."""
    label = CATEGORY_LABELS[category]
    rows = [
        [
            InlineKeyboardButton(
                SETTING_LABELS[key],
                callback_data=f"{CALLBACK_PREFIX}:setting:{key}",
            )
        ]
        for key in CATEGORY_SETTINGS[category]
    ]
    if category == "usage":
        rows.append(
            [
                InlineKeyboardButton(
                    "Reset Today's Download Limits",
                    callback_data=f"{CALLBACK_PREFIX}:action:reset_downloads",
                )
            ]
        )
    rows.append(
        [
            InlineKeyboardButton(
                "Back",
                callback_data=f"{CALLBACK_PREFIX}:home",
            ),
            InlineKeyboardButton(
                "Close",
                callback_data=f"{CALLBACK_PREFIX}:close",
            ),
        ]
    )
    return f"<b>{escape(label)}</b>", InlineKeyboardMarkup(rows)


def _setting_action_rows(
    key: str,
    category: str,
) -> list[list[InlineKeyboardButton]]:
    rows = []
    if is_editable_setting(key) and is_boolean_setting(key):
        rows.append(
            [
                InlineKeyboardButton(
                    "Enable",
                    callback_data=f"{CALLBACK_PREFIX}:value:{key}:1",
                ),
                InlineKeyboardButton(
                    "Disable",
                    callback_data=f"{CALLBACK_PREFIX}:value:{key}:0",
                ),
            ]
        )
    elif is_editable_setting(key):
        rows.append(
            [
                InlineKeyboardButton(
                    "Edit Value",
                    callback_data=f"{CALLBACK_PREFIX}:edit:{key}",
                ),
                InlineKeyboardButton(
                    "Reset Default",
                    callback_data=f"{CALLBACK_PREFIX}:reset:{key}",
                ),
            ]
        )
    rows.append(
        [
            InlineKeyboardButton(
                "Back",
                callback_data=f"{CALLBACK_PREFIX}:category:{category}",
            )
        ]
    )
    return rows


def build_setting_detail(
    key: str,
    settings: dict[str, object],
) -> tuple[str, InlineKeyboardMarkup]:
    """Build the description and controls for one global setting."""
    category = get_setting_category(key)
    current_value = _display_value(settings[key])
    default_value = _display_value(DEFAULT_GLOBAL_SETTINGS[key])
    lines = [
        f"<b>{escape(SETTING_LABELS[key])}</b>",
        "",
        escape(SETTING_DESCRIPTIONS[key]),
        "",
        f"<b>Current:</b> <code>{current_value}</code>",
        f"<b>Default:</b> <code>{default_value}</code>",
    ]
    markup = InlineKeyboardMarkup(_setting_action_rows(key, category))
    return "\n".join(lines), markup


async def handle_settings_command(client, message) -> None:
    """Show the global settings dashboard to a bot administrator."""
    try:
        await get_global_settings()
        text, markup = build_settings_dashboard()
        await message.reply_text(text, reply_markup=markup)
    except PyMongoError:
        logger.exception("Failed to load global settings")
        try:
            await message.reply_text("Settings are temporarily unavailable.")
        except RPCError:
            logger.exception("Failed to send the settings error message")
    except RPCError:
        logger.exception("Failed to send the global settings dashboard")


__all__ = [
    "CALLBACK_PREFIX",
    "build_category_view",
    "build_setting_detail",
    "build_settings_dashboard",
    "handle_settings_command",
]
