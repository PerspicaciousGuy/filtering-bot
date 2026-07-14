"""Maintenance-mode access checks for Telegram updates."""

from html import escape

from info import ADMINS
from EbookGuy.shared.global_settings import get_global_settings


def _is_admin(user) -> bool:
    identifiers = {str(admin).lower() for admin in ADMINS}
    user_id = str(getattr(user, "id", ""))
    username = str(getattr(user, "username", "")).lower()
    return user_id in identifiers or username in identifiers


async def get_maintenance_message(user) -> str | None:
    """Return the maintenance notice for a restricted user update."""
    if _is_admin(user):
        return None
    settings = await get_global_settings()
    if not settings["maintenance_mode"]:
        return None
    message = escape(str(settings["maintenance_message"]))
    return f"<b>Maintenance</b>\n\n{message}"


__all__ = ["get_maintenance_message"]
