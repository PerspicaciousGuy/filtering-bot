from pyrogram import Client, filters

from info import ADMINS
from EbookGuy.features.indexing.admin import (
    handle_delete_checkpoint_callback,
    handle_resume_callback,
    handle_resume_indexing,
    handle_set_skip_number,
)
from EbookGuy.features.indexing.moderation import handle_index_files
from EbookGuy.features.indexing.requests import handle_send_for_index


@Client.on_callback_query(filters.regex(r'^index'))
async def index_files(bot, query):
    await handle_index_files(bot, query)


@Client.on_message(filters.private & filters.command('index'))
async def send_for_index(bot, message):
    await handle_send_for_index(bot, message)


@Client.on_message(filters.command('setskip') & filters.user(ADMINS))
async def set_skip_number(bot, message):
    await handle_set_skip_number(bot, message)


@Client.on_message(filters.command('resume') & filters.user(ADMINS))
async def resume_indexing(bot, message):
    await handle_resume_indexing(bot, message)


@Client.on_callback_query(filters.regex(r'^resume_idx#'))
async def resume_callback(bot, query):
    await handle_resume_callback(bot, query)


@Client.on_callback_query(filters.regex(r'^delete_cp#'))
async def delete_checkpoint_callback(bot, query):
    await handle_delete_checkpoint_callback(bot, query)


#EbookGuy
