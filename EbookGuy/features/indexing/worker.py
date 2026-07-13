import asyncio
import logging
import time

from pyrogram import enums
from pyrogram.errors import FloodWait, MessageNotModified, RPCError
from pymongo.errors import PyMongoError

from database.ia_filterdb import (
    is_allowed_file,
    save_file,
)
from database.indexing_checkpoints import (
    delete_checkpoint,
    get_checkpoint,
    save_checkpoint,
)
from EbookGuy.bot import MessageRange
from EbookGuy.features.indexing.models import IndexState
from EbookGuy.features.indexing.progress import (
    completion_text,
    failure_text,
    format_progress,
    pause_markup,
    paused_text,
    rate_limit_text,
)
from info import FILTER_BY_EXTENSION
from utils import temp


logger = logging.getLogger(__name__)
lock = asyncio.Lock()
CHECKPOINT_INTERVAL = 100
PROGRESS_UPDATE_INTERVAL = 3
INDEXING_ERRORS = (
    KeyError,
    OSError,
    PyMongoError,
    RPCError,
    TypeError,
    ValueError,
)
DEFAULT_STATS = {
    "total": 0,
    "duplicate": 0,
    "errors": 0,
    "deleted": 0,
    "no_media": 0,
    "unsupported": 0,
    "filtered": 0,
}


async def _load_state(request):
    checkpoint = (
        await get_checkpoint(request.chat_id)
        if request.should_resume
        else None
    )
    stats = dict(checkpoint.get("stats", DEFAULT_STATS)) if checkpoint else dict(DEFAULT_STATS)
    start_from = checkpoint["current_msg"] if checkpoint else temp.CURRENT
    return IndexState(start_from, start_from, stats, time.time())


async def _update_progress(request, state):
    if time.time() - state.last_update <= PROGRESS_UPDATE_INTERVAL:
        return
    try:
        await request.status_message.edit_text(
            format_progress(state.current_message, state.stats),
            reply_markup=pause_markup(),
        )
    except MessageNotModified:
        logger.debug("Indexing progress message is already current")
    state.last_update = time.time()


async def _pause_if_requested(request, state):
    if not temp.CANCEL:
        return False
    await save_checkpoint(request.chat_id, state.current_message, state.stats)
    await request.status_message.edit(
        paused_text(state.current_message, state.stats)
    )
    return True


def _get_supported_media(message, stats):
    if message.empty:
        stats["deleted"] += 1
        return None
    if not message.media:
        stats["no_media"] += 1
        return None
    supported = {
        enums.MessageMediaType.VIDEO,
        enums.MessageMediaType.AUDIO,
        enums.MessageMediaType.DOCUMENT,
    }
    if message.media not in supported:
        stats["unsupported"] += 1
        return None
    media = getattr(message, message.media.value, None)
    if media is None:
        stats["unsupported"] += 1
    return media


async def _save_media(message, state):
    media = _get_supported_media(message, state.stats)
    if media is None:
        return
    if FILTER_BY_EXTENSION and not is_allowed_file(getattr(media, "file_name", "")):
        state.stats["filtered"] += 1
        return
    media.caption = message.caption
    try:
        success, code = await save_file(media)
        if success:
            state.stats["total"] += 1
        elif code == 0:
            state.stats["duplicate"] += 1
        elif code == 2:
            state.stats["errors"] += 1
    except INDEXING_ERRORS:
        state.stats["errors"] += 1
        logger.exception("Failed to save indexed file")


async def _index_messages(request, state):
    messages = request.bot.iter_messages(MessageRange(
        chat_id=request.chat_id,
        limit=request.last_message_id,
        offset=state.start_from,
    ))
    async for message in messages:
        if await _pause_if_requested(request, state):
            return False
        state.current_message += 1
        await _update_progress(request, state)
        if state.current_message % CHECKPOINT_INTERVAL == 0:
            await save_checkpoint(
                request.chat_id,
                state.current_message,
                state.stats,
            )
        await _save_media(message, state)
    return True


async def _handle_flood_wait(request, state, error):
    await save_checkpoint(request.chat_id, state.current_message, state.stats)
    wait_time = error.value + 5
    await request.status_message.edit(
        rate_limit_text(state.current_message, state.stats, wait_time)
    )
    await asyncio.sleep(wait_time)
    await request.status_message.edit("\u25b6\ufe0f Resuming indexing...")
    state.start_from = state.current_message


async def _handle_failure(request, state):
    await save_checkpoint(request.chat_id, state.current_message, state.stats)
    logger.exception("Indexing failed unexpectedly")
    await request.status_message.edit(
        failure_text(state.current_message, state.stats)
    )


async def index_files_to_db(request):
    """Index channel media while preserving resumable checkpoint state."""
    state = await _load_state(request)
    async with lock:
        temp.CANCEL = False
        while True:
            try:
                if not await _index_messages(request, state):
                    return
                break
            except FloodWait as error:
                await _handle_flood_wait(request, state, error)
            except INDEXING_ERRORS:
                await _handle_failure(request, state)
                return
        await delete_checkpoint(request.chat_id)
        await request.status_message.edit(
            completion_text(state.current_message, state.stats)
        )
