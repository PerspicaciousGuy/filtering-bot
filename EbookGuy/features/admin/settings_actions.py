"""Confirmed administrator actions exposed from the settings dashboard."""

from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from database.users_chats_db import db
from EbookGuy.shared.global_settings import record_admin_action


CALLBACK_PREFIX = "global_settings"


async def show_download_reset_confirmation(query) -> None:
    """Show the impact and confirmation controls for a daily-counter reset."""
    affected_users = await db.count_users_with_daily_downloads()
    text = (
        "<b>Reset Today's Download Limits?</b>\n\n"
        f"This will reset the counters of <b>{affected_users}</b> user(s). "
        "Premium status, cooldown settings, and analytics will not be changed."
    )
    markup = InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    "Confirm Reset",
                    callback_data=f"{CALLBACK_PREFIX}:confirm:reset_downloads",
                )
            ],
            [
                InlineKeyboardButton(
                    "Back",
                    callback_data=f"{CALLBACK_PREFIX}:category:usage",
                )
            ],
        ]
    )
    await query.answer()
    await query.message.edit_text(text, reply_markup=markup)


async def reset_download_limits(query) -> None:
    """Reset every current daily download counter after confirmation."""
    affected_users = await db.reset_all_daily_downloads()
    await record_admin_action(
        "daily_download_limits_reset",
        query.from_user.id,
        {"affected_users": affected_users},
    )
    markup = InlineKeyboardMarkup(
        [[
            InlineKeyboardButton(
                "Back to Usage Limits",
                callback_data=f"{CALLBACK_PREFIX}:category:usage",
            )
        ]]
    )
    await query.answer("Download limits reset")
    await query.message.edit_text(
        "<b>Download Limits Reset</b>\n\n"
        f"Reset today's counters for <b>{affected_users}</b> user(s).",
        reply_markup=markup,
    )


__all__ = ["reset_download_limits", "show_download_reset_confirmation"]
