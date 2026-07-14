from pyrogram import Client, filters

from EbookGuy.features.admin.file_cleanup import (
    handle_clean_duplicates,
    handle_delete_media,
    handle_find_duplicates,
)
from info import ADMINS
from EbookGuy.shared.callback_metrics import measure_callback
from EbookGuy.shared.configured_channels import configured_channel_filter


media_filter = filters.document | filters.video | filters.audio


@Client.on_message(media_filter & configured_channel_filter("delete_channel_ids"))
async def deletemultiplemedia(bot, message):
    await handle_delete_media(bot, message)


@Client.on_message(filters.command("duplicates") & filters.user(ADMINS))
async def find_duplicates(bot, message):
    await handle_find_duplicates(bot, message)


@Client.on_callback_query(filters.regex(r"^clean_duplicates"))
@measure_callback("clean_duplicates")
async def clean_duplicates(bot, query):
    await handle_clean_duplicates(bot, query)
