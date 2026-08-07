"""Telegram administration menu and download flow for settings backups."""

from datetime import datetime, timezone
from io import BytesIO

from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from EbookGuy.shared.global_settings import get_global_settings
from EbookGuy.shared.settings_backup import (
    BACKUP_VERSION,
    create_settings_backup,
)


CALLBACK_PREFIX = "global_settings:backup"


def build_backup_view() -> tuple[str, InlineKeyboardMarkup]:
    """Build the settings backup and restore menu."""
    markup = InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    "Download Settings",
                    callback_data=f"{CALLBACK_PREFIX}:download",
                )
            ],
            [
                InlineKeyboardButton(
                    "Restore Settings",
                    callback_data=f"{CALLBACK_PREFIX}:restore",
                )
            ],
            [
                InlineKeyboardButton(
                    "Back",
                    callback_data="global_settings:home",
                )
            ],
        ]
    )
    text = (
        "<b>Backup & Restore</b>\n\n"
        "Download all global runtime settings as JSON, or upload a previous "
        "backup and preview its changes before restoring."
    )
    return text, markup


async def show_settings_backup(query) -> None:
    """Show the backup and restore menu."""
    text, markup = build_backup_view()
    await query.answer()
    await query.message.edit_text(text, reply_markup=markup)


async def download_settings_backup(query) -> None:
    """Send the current effective settings as a versioned JSON document."""
    await query.answer("Preparing settings backup...")
    settings = await get_global_settings()
    document = BytesIO(create_settings_backup(settings))
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    document.name = f"filtering-bot-settings-{timestamp}.json"
    await query.message.reply_document(
        document=document,
        caption=(
            f"<b>Global Settings Backup</b>\n"
            f"Format version: <code>{BACKUP_VERSION}</code>\n\n"
            "Keep this file private. It can be restored from /settings."
        ),
    )


__all__ = [
    "build_backup_view",
    "download_settings_backup",
    "show_settings_backup",
]
