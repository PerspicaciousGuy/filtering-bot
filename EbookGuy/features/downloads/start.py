from Script import script
from database.users_chats_db import db
from EbookGuy.features.downloads.force_subscription import enforce_subscription
from EbookGuy.features.downloads.start_delivery import handle_start_payload
from EbookGuy.features.downloads.start_views import (
    get_start_buttons,
    show_start_message,
)
from info import LOG_CHANNEL


WELCOME_PAYLOADS = {"subscribe", "error", "okay", "help"}


async def _register_user(client, message):
    user = message.from_user
    if await db.is_user_exist(user.id):
        return
    await db.add_user(user.id, user.first_name)
    await client.send_message(
        LOG_CHANNEL,
        script.LOG_TEXT_P.format(user.id, user.mention),
    )


async def handle_start(client, message):
    """Register the user and route the start command payload."""
    await _register_user(client, message)
    if len(message.command) != 2:
        await show_start_message(message)
        return
    if await enforce_subscription(client, message):
        return

    payload = message.command[1]
    if payload in WELCOME_PAYLOADS:
        await show_start_message(message)
        return
    await handle_start_payload(client, message, payload)


__all__ = ["get_start_buttons", "handle_start"]
