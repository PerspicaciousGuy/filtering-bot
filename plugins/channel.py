

from pyrogram import Client, filters

from database.ia_filterdb import save_file
from EbookGuy.shared.configured_channels import configured_channel_filter

media_filter = filters.document | filters.video | filters.audio

@Client.on_message(media_filter & configured_channel_filter("file_channel_ids"))
async def media(bot, message):
    media = getattr(message, message.media.value, None)
    media.caption = message.caption
    await save_file(media)
