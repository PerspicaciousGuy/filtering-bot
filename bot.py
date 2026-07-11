import glob, logging, logging.config, asyncio
from aiohttp import web
import pytz

# Get logging configurations
logging.config.fileConfig('logging.conf')
logging.getLogger().setLevel(logging.INFO)
logging.getLogger("pyrogram").setLevel(logging.ERROR)
logging.getLogger("cinemagoer").setLevel(logging.ERROR)

from pyrogram import idle
from pyrogram.errors import RPCError
from pymongo.errors import PyMongoError
from database.users_chats_db import db
from info import *
from utils import temp
from Script import script 
from datetime import date, datetime 


from EbookGuy.bot import EbookGuyBot
from EbookGuy.util.keepalive import ping_server
from EbookGuy.bot.clients import initialize_clients
from database.ia_filterdb import col, sec_col

ppath = "plugins/*.py"
files = glob.glob(ppath)
EbookGuyBot.start()
loop = asyncio.get_event_loop()

async def web_server():
    async def handle(request):
        return web.Response(text="Hello world")

    app = web.Application()
    app.router.add_get('/', handle)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', PORT)
    await site.start()
    logging.info(f"Web server started on port {PORT}")

async def start():
    print('\n')
    print('Initalizing Your Bot')
    await initialize_clients()
    
    if ON_HEROKU:
        asyncio.create_task(ping_server())
    
    # Start web server
    await web_server()
    
    b_users, b_chats = await db.get_banned()
    temp.BANNED_USERS = b_users
    temp.BANNED_CHATS = b_chats
    me = await EbookGuyBot.get_me()
    temp.BOT = EbookGuyBot
    temp.ME = me.id
    temp.U_NAME = me.username
    temp.B_NAME = me.first_name

    # Cache library count and refresh hourly
    async def refresh_lib_count():
        while True:
            try:
                total = col.count_documents({}) + sec_col.count_documents({})
                temp.LIB_COUNT = f"{total // 1000}K" if total >= 1000 else str(total)
            except PyMongoError:
                logging.exception("Failed to refresh cached library count")
            await asyncio.sleep(3600)
    asyncio.create_task(refresh_lib_count())

    logging.info(script.LOGO)
    tz = pytz.timezone('Asia/Kolkata')
    today = date.today()
    now = datetime.now(tz)
    time = now.strftime("%H:%M:%S %p")
    try:
        await EbookGuyBot.send_message(chat_id=LOG_CHANNEL, text=script.RESTART_TXT.format(today, time))
    except RPCError:
        logging.exception("Failed to send restart notification to log channel")
    for ch in CHANNELS:
        try:
            k = await EbookGuyBot.send_message(chat_id=ch, text="**Bot Restarted**")
            await k.delete()
        except RPCError:
            logging.exception("Failed to send restart notification to file channel %s", ch)
    try:
        k = await EbookGuyBot.send_message(chat_id=AUTH_CHANNEL, text="**Bot Restarted**")
        await k.delete()
    except RPCError:
        logging.exception("Failed to send restart notification to force-subscribe channel")
    await idle()


if __name__ == '__main__':
    try:
        loop.run_until_complete(start())
    except KeyboardInterrupt:
        logging.info('Service Stopped Bye 👋')

