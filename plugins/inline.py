from pyrogram import Client

from EbookGuy.features.search.inline_queries import handle_inline_query


@Client.on_inline_query()
async def answer(bot, query):
    await handle_inline_query(bot, query)
