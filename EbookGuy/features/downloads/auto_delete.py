"""Background cleanup for delivered Telegram files."""

import asyncio
import logging
from typing import Awaitable, Callable

from pyrogram.errors import RPCError


logger = logging.getLogger(__name__)
_AUTO_DELETE_TASKS = set()


def auto_delete_notice(delay_seconds):
    """Build a delivery warning for the configured deletion delay."""
    if delay_seconds % 60 == 0:
        duration = f"{delay_seconds // 60} minute(s)"
    else:
        duration = f"{delay_seconds} second(s)"
    return (
        "<b>Important:</b> This file will be deleted in "
        f"<b>{duration}</b>. Save it before then."
    )


async def _delete_delivered_messages(messages, settings):
    await asyncio.sleep(int(settings["auto_delete_delay_seconds"]))
    for message in messages:
        try:
            await message.delete()
        except RPCError:
            logging.getLogger(__name__).debug(
                "Auto-delete message was already unavailable",
                exc_info=True,
            )


def schedule_delivered_messages_deletion(
    messages,
    settings,
    after_delete: Callable[[], Awaitable[None]] | None = None,
):
    """Schedule delivery cleanup without holding the active handler open."""
    if not settings["auto_delete_enabled"]:
        return False

    async def run_cleanup():
        await _delete_delivered_messages(messages, settings)
        if after_delete is not None:
            try:
                await after_delete()
            except RPCError:
                logger.debug(
                    "Auto-delete follow-up message was unavailable",
                    exc_info=True,
                )

    task = asyncio.create_task(run_cleanup())
    _AUTO_DELETE_TASKS.add(task)
    task.add_done_callback(_finish_auto_delete_task)
    return True


def _finish_auto_delete_task(task):
    _AUTO_DELETE_TASKS.discard(task)
    if task.cancelled():
        return
    error = task.exception()
    if error is not None:
        logger.error(
            "Auto-delete task failed",
            exc_info=(type(error), error, error.__traceback__),
        )


async def cancel_auto_delete_tasks():
    """Cancel pending delivery cleanup tasks during application shutdown."""
    tasks = tuple(_AUTO_DELETE_TASKS)
    for task in tasks:
        task.cancel()
    if tasks:
        await asyncio.gather(*tasks, return_exceptions=True)


async def send_auto_delete_message(client, user_id, messages):
    """Warn about and schedule the configured delivery cleanup policy."""
    from EbookGuy.shared.global_settings import get_global_settings

    settings = await get_global_settings()
    if not settings["auto_delete_enabled"]:
        return
    warning_message = await client.send_message(
        chat_id=user_id,
        text=auto_delete_notice(
            int(settings["auto_delete_delay_seconds"])
        ),
    )

    async def confirm_deletion():
        await warning_message.edit_text(
            "<b>\u2705 Your message is successfully deleted</b>"
        )

    schedule_delivered_messages_deletion(
        messages,
        settings,
        after_delete=confirm_deletion,
    )
