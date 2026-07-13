from pyrogram import Client, filters

from EbookGuy.features.admin.user_info import (
    handle_show_id,
    handle_user_info,
)


@Client.on_message(filters.command("id") & filters.private)
async def showid(client, message):
    await handle_show_id(client, message)


@Client.on_message(filters.command(["info"]) & filters.private)
async def who_is(client, message):
    await handle_user_info(client, message)
