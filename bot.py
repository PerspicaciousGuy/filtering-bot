import asyncio
import logging
import logging.config
from dataclasses import dataclass
from datetime import datetime

import pytz
from aiohttp import web
from pymongo.errors import PyMongoError
from pyrogram import idle
from pyrogram.errors import RPCError

from database.ia_filterdb import col, sec_col
from database.users_chats_db import db
from EbookGuy.bot import EbookGuyBot, multi_clients, work_loads
from EbookGuy.bot.clients import initialize_clients
from EbookGuy.features.premium.expiry_notifications import (
    run_premium_expiry_notifier,
)
from EbookGuy.shared.configured_channels import configured_channels
from EbookGuy.shared.global_settings import get_global_settings
from EbookGuy.util.keepalive import ping_server
from info import ON_HEROKU, PORT
from Script import script
from utils import temp

logging.config.fileConfig("logging.conf")
logging.getLogger().setLevel(logging.INFO)
logging.getLogger("pyrogram").setLevel(logging.ERROR)
logging.getLogger("cinemagoer").setLevel(logging.ERROR)
logger = logging.getLogger(__name__)


@dataclass
class ServiceState:
    is_ready: bool = False


service_state = ServiceState()


async def _health_handler(request):
    return web.json_response({"status": "ok"})


async def _readiness_handler(request):
    status = 200 if service_state.is_ready else 503
    state = "ready" if service_state.is_ready else "starting"
    return web.json_response({"status": state}, status=status)


async def web_server():
    app = web.Application()
    app.router.add_get("/", _health_handler)
    app.router.add_get("/health", _health_handler)
    app.router.add_get("/ready", _readiness_handler)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", PORT)
    await site.start()
    logger.info("Web server started on port %s", PORT)
    return runner


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
    current_time = datetime.now(timezone)
    restart_text = script.RESTART_TXT.format(
        current_time.date(),
        current_time.strftime("%H:%M:%S %p"),
    )
    settings = await get_global_settings()
    log_channel_id = int(settings["log_channel_id"])
    if log_channel_id:
        await _notify_restart(log_channel_id, restart_text)

    notified_channels = {log_channel_id}
    for channel_id in configured_channels(settings, "file_channel_ids"):
        if channel_id in notified_channels:
            continue
        notified_channels.add(channel_id)
        message = await _notify_restart(channel_id, "**Bot Restarted**")
        if message:
            try:
                await message.delete()
            except RPCError:
                logger.exception(
                    "Failed to remove restart notification from %s",
                    channel_id,
                )


async def _cancel_background_tasks(tasks):
    for task in tasks:
        task.cancel()
    if tasks:
        await asyncio.gather(*tasks, return_exceptions=True)


async def _stop_clients():
    clients = list(dict.fromkeys([*multi_clients.values(), EbookGuyBot]))
    for client in reversed(clients):
        if not getattr(client, "is_connected", False):
            continue
        try:
            await client.stop()
        except RPCError:
            logger.exception("Failed to stop Telegram client cleanly")
    multi_clients.clear()
    work_loads.clear()


async def start():
    logger.info("Initializing bot")
    runner = None
    background_tasks = []
    try:
        await EbookGuyBot.start()
        await initialize_clients()
        runner = await web_server()
        await _initialize_bot_state()
        background_tasks.extend([
            asyncio.create_task(
                _refresh_library_count(),
                name="library-count-refresh",
            ),
            asyncio.create_task(
                run_premium_expiry_notifier(EbookGuyBot),
                name="premium-expiry-notifier",
            ),
        ])
        if ON_HEROKU:
            background_tasks.append(
                asyncio.create_task(ping_server(), name="keepalive")
            )
        service_state.is_ready = True
        logger.info(script.LOGO)
        await _send_restart_notifications()
        await idle()
    finally:
        service_state.is_ready = False
        await _cancel_background_tasks(background_tasks)
        if runner is not None:
            await runner.cleanup()
        await _stop_clients()


if __name__ == "__main__":
    try:
        asyncio.run(start())
    except KeyboardInterrupt:
        logger.info("Service stopped")
