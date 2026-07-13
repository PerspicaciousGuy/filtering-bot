"""Lifecycle management for private search messages and state."""

import asyncio
import logging
from dataclasses import dataclass

from pyrogram.errors import RPCError

from EbookGuy.features.search.state import FRESH, PENDING_SEARCH
from utils import temp


logger = logging.getLogger(__name__)
_expiry_tasks: dict[str, asyncio.Task] = {}


@dataclass(frozen=True)
class SearchExpiry:
    """Search state and messages that expire together."""

    key: str
    delay_seconds: int
    messages: tuple[object, ...]


async def _delete_messages(messages: tuple[object, ...]) -> None:
    for message in messages:
        try:
            await message.delete()
        except RPCError:
            logger.debug("Search message was already unavailable")


async def _expire_search(expiry: SearchExpiry) -> None:
    await asyncio.sleep(expiry.delay_seconds)
    FRESH.pop(expiry.key, None)
    PENDING_SEARCH.pop(expiry.key, None)
    temp.GETALL.pop(expiry.key, None)
    await _delete_messages(expiry.messages)


def _discard_task(key: str, task: asyncio.Task) -> None:
    if _expiry_tasks.get(key) is task:
        _expiry_tasks.pop(key, None)


def schedule_search_expiry(expiry: SearchExpiry) -> None:
    """Replace any existing expiry task for the same search."""
    previous = _expiry_tasks.get(expiry.key)
    if previous is not None:
        previous.cancel()
    task = asyncio.create_task(_expire_search(expiry))
    _expiry_tasks[expiry.key] = task
    task.add_done_callback(
        lambda completed: _discard_task(expiry.key, completed)
    )


__all__ = ["SearchExpiry", "schedule_search_expiry"]
