"""Bot administrator checks shared by Telegram handlers."""

from info import ADMINS


def is_bot_admin(user) -> bool:
    """Return whether a Telegram user matches an ADMINS ID or username."""
    identifiers = {str(admin).lower() for admin in ADMINS}
    user_id = str(getattr(user, "id", ""))
    username = str(getattr(user, "username", "")).lower()
    return user_id in identifiers or username in identifiers
