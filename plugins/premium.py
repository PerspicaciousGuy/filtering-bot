import logging

from pyrogram import Client, filters
from pyrogram.types import PreCheckoutQuery

from info import ADMINS
from EbookGuy.features.premium.admin import (
    handle_add_premium_command,
    handle_premium_users_command,
    handle_remove_premium_command,
    handle_stars_balance_command,
    handle_stars_history_command,
)
from EbookGuy.features.premium.payments import (
    handle_buy_premium_callback,
    handle_confirm_premium_callback,
    handle_pre_checkout_handler,
    handle_successful_payment_handler,
)
from EbookGuy.features.premium.views import (
    handle_my_status_command,
    handle_premium_command,
    handle_show_premium_callback,
)

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

logger.info("Premium plugin initialized")


@Client.on_message(filters.command("plan") & filters.private, group=-1)
async def premium_command(client, message):
    await handle_premium_command(client, message)


@Client.on_message(filters.command("mystatus") & filters.private, group=-1)
async def my_status_command(client, message):
    await handle_my_status_command(client, message)


@Client.on_callback_query(filters.regex(r"^show_premium$"))
async def show_premium_callback(client, query):
    await handle_show_premium_callback(client, query)


@Client.on_callback_query(filters.regex(r"^buy_premium_(\d+)$"))
async def buy_premium_callback(client, query):
    await handle_buy_premium_callback(client, query)


@Client.on_callback_query(filters.regex(r"^confirm_premium_(\d+)$"))
async def confirm_premium_callback(client, query):
    await handle_confirm_premium_callback(client, query)


@Client.on_pre_checkout_query()
async def pre_checkout_handler(client, query: PreCheckoutQuery):
    await handle_pre_checkout_handler(client, query)


@Client.on_message(filters.successful_payment)
async def successful_payment_handler(client, message):
    await handle_successful_payment_handler(client, message)


@Client.on_message(filters.command("addpremium") & filters.user(ADMINS), group=-1)
async def add_premium_command(client, message):
    await handle_add_premium_command(client, message)


@Client.on_message(filters.command("removepremium") & filters.user(ADMINS), group=-1)
async def remove_premium_command(client, message):
    await handle_remove_premium_command(client, message)


@Client.on_message(filters.command("premiumusers") & filters.user(ADMINS), group=-1)
async def premium_users_command(client, message):
    await handle_premium_users_command(client, message)


@Client.on_message(filters.command("stars") & filters.user(ADMINS), group=-1)
async def stars_balance_command(client, message):
    await handle_stars_balance_command(client, message)


@Client.on_message(filters.command("starhistory") & filters.user(ADMINS), group=-1)
async def stars_history_command(client, message):
    await handle_stars_history_command(client, message)
