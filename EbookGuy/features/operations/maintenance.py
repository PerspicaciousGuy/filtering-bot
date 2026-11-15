"""Maintenance-mode access checks for Telegram updates."""

from html import escape

from EbookGuy.shared.global_settings import get_global_settings
from EbookGuy.shared.permissions import is_bot_admin


async def get_maintenance_message(user) -> str | None:
    """Return the maintenance notice for a restricted user update."""
    if is_bot_admin(user):
        return None
    settings = await get_global_settings()
    if not settings["maintenance_mode"]:
        return None
    message = escape(str(settings["maintenance_message"]))
    return f"<b>Maintenance</b>\n\n{message}"


__all__ = ["get_maintenance_message"]
