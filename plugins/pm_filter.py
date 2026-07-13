import logging
from pyrogram import Client, filters
from pyrogram.types import CallbackQuery

from plugins.pm_filter_callbacks import handle_callback
from plugins.pm_filter_search import (
    handle_format_selection,
    handle_next_page,
    handle_private_text,
    handle_switch_format,
)

logger = logging.getLogger(__name__)
logger.setLevel(logging.ERROR)


@Client.on_message(filters.private & filters.text & filters.incoming)
async def pm_text(bot, message):
    await handle_private_text(bot, message)


@Client.on_callback_query(filters.regex(r"^next"))
async def next_page(bot, query):
    await handle_next_page(bot, query)


@Client.on_callback_query(filters.regex(r"^format_select"))
async def format_selection(bot, query):
    await handle_format_selection(bot, query)


@Client.on_callback_query(filters.regex(r"^switch_format"))
async def switch_format(bot, query):
    await handle_switch_format(bot, query)


@Client.on_callback_query()
async def cb_handler(client: Client, query: CallbackQuery):
    await handle_callback(client, query)
