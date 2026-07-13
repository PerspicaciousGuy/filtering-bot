import logging

from pyrogram import Client, filters

from EbookGuy.features.admin.file_cleanup import (
    handle_clean_duplicates,
    handle_delete_media,
    handle_find_duplicates,
)
from info import ADMINS, DELETE_CHANNELS


logger = logging.getLogger(__name__)
media_filter = filters.document | filters.video | filters.audio

if not DELETE_CHANNELS or DELETE_CHANNELS == [""]:
    logger.warning("Delete channels are empty; file deletion is disabled")
else:
    logger.info(
        "File deletion handler enabled for %s channel(s)",
        len(DELETE_CHANNELS),
    )


@Client.on_message(filters.chat(DELETE_CHANNELS) & media_filter)
async def deletemultiplemedia(bot, message):
    await handle_delete_media(bot, message)


@Client.on_message(filters.command("duplicates") & filters.user(ADMINS))
async def find_duplicates(bot, message):
    await handle_find_duplicates(bot, message)


@Client.on_callback_query(filters.regex(r"^clean_duplicates"))
async def clean_duplicates(bot, query):
    await handle_clean_duplicates(bot, query)
