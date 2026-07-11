import logging
from functools import partial

from pyrogram.errors import RPCError
from pymongo.errors import PyMongoError

from database.gfilters_mdb import find_gfilter, get_gfilters
from EbookGuy.features.filters.delivery import (
    FilterPayload,
    FilterWorkflow,
    delete_filter_message,
    find_matching_filter,
    is_setting_enabled,
    run_auto_search,
    send_filter_message,
)
from EbookGuy.features.filters.manual import manual_filters
from utils import get_settings

logger = logging.getLogger(__name__)
logger.setLevel(logging.ERROR)


async def global_filters(client, message, text=False):
    settings = await get_settings(message.chat.id)
    name = text or message.text
    reply_id = (
        message.reply_to_message.id
        if message.reply_to_message
        else message.id
    )
    stored_filter = await find_matching_filter(
        name,
        await get_gfilters("gfilters"),
        partial(find_gfilter, "gfilters"),
    )
    if stored_filter is None:
        return False

    try:
        payload = FilterPayload(
            reply_text=stored_filter.reply_text,
            buttons_data=stored_filter.buttons_data,
            file_id=stored_filter.file_id,
            reply_id=reply_id,
            protect_content=False,
        )
        sent_message, is_media = await send_filter_message(
            client,
            message,
            payload,
        )
        manual_result = await manual_filters(client, message)
        workflow = FilterWorkflow(client, message, sent_message, settings)
        if manual_result is False:
            workflow.settings = await get_settings(message.chat.id)
            if await is_setting_enabled(workflow, "auto_ffilter"):
                await run_auto_search(workflow)
                if "auto_ffilter" not in workflow.repaired_settings:
                    await delete_filter_message(workflow)
        elif is_media:
            await delete_filter_message(workflow)
    except (
        KeyError,
        PyMongoError,
        RPCError,
        SyntaxError,
        TypeError,
        ValueError,
    ):
        logger.exception("Failed to process global filter")
