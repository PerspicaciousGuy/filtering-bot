import asyncio
import logging
import logging.config
from datetime import date, datetime

import pytz
from aiohttp import web
from pyrogram import idle
from pyrogram.errors import RPCError
from pymongo.errors import PyMongoError

from Script import script
from database.ia_filterdb import col, sec_col
from database.users_chats_db import db
from EbookGuy.bot import EbookGuyBot
from EbookGuy.bot.clients import initialize_clients
from EbookGuy.util.keepalive import ping_server
from info import (
    AUTH_CHANNEL,
    CHANNELS,
    LOG_CHANNEL,
    ON_HEROKU,
    PORT,
)
from utils import temp


logging.config.fileConfig("logging.conf")
logging.getLogger().setLevel(logging.INFO)
logging.getLogger("pyrogram").setLevel(logging.ERROR)
logging.getLogger("cinemagoer").setLevel(logging.ERROR)
logger = logging.getLogger(__name__)

EbookGuyBot.start()
loop = asyncio.get_event_loop()


async def web_server():
    async def handle(request):
        return web.Response(text="Hello world")

    app = web.Application()
    app.router.add_get("/", handle)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", PORT)
    await site.start()
    logger.info("Web server started on port %s", PORT)


async def _initialize_bot_state():
    banned_users, banned_chats = await db.get_banned()
    temp.BANNED_USERS = banned_users
    temp.BANNED_CHATS = banned_chats
    identity = await EbookGuyBot.get_me()
    temp.BOT = EbookGuyBot
    temp.ME = identity.id
    temp.U_NAME = identity.username
    temp.B_NAME = identity.first_name


async def _refresh_library_count():
    while True:
        try:
            total = (
                await col.count_documents({})
                + await sec_col.count_documents({})
            )
            temp.LIB_COUNT = (
                f"{total // 1000}K" if total >= 1000 else str(total)
            )
        except PyMongoError:
            logger.exception("Failed to refresh cached library count")
        await asyncio.sleep(3600)


async def _notify_restart(chat_id, text):
    try:
        message = await EbookGuyBot.send_message(
            chat_id=chat_id,
            text=text,
        )
        return message
    except RPCError:
        logger.exception(
            "Failed to send restart notification to %s",
            chat_id,
        )
        return None


async def _send_restart_notifications():
    timezone = pytz.timezone("Asia/Kolkata")
    restart_text = script.RESTART_TXT.format(
        date.today(),
        datetime.now(timezone).strftime("%H:%M:%S %p"),
    )
    await _notify_restart(LOG_CHANNEL, restart_text)

    for channel_id in CHANNELS:
        message = await _notify_restart(
            channel_id,
            "**Bot Restarted**",
        )
        if message:
            await message.delete()

    if AUTH_CHANNEL:
        message = await _notify_restart(
            AUTH_CHANNEL,
            "**Bot Restarted**",
        )
        if message:
            await message.delete()


async def start():
    logger.info("Initializing bot")
    await initialize_clients()
    if ON_HEROKU:
        asyncio.create_task(ping_server())
    await web_server()
    await _initialize_bot_state()
    asyncio.create_task(_refresh_library_count())
    logger.info(script.LOGO)
    await _send_restart_notifications()
    await idle()


if __name__ == "__main__":
    try:
        loop.run_until_complete(start())
    except KeyboardInterrupt:
        logger.info("Service stopped")
