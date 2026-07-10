from pyrogram import Client
from pyrogram.types import CallbackQuery

from EbookGuy.features.filters.alert_callbacks import maybe_handle_alert_callback
from EbookGuy.features.filters.connection_callbacks import maybe_handle_connection_callback
from EbookGuy.features.filters.file_callbacks import maybe_handle_file_callback
from EbookGuy.features.filters.management_callbacks import (
    maybe_handle_filter_management_callback,
)
from EbookGuy.features.filters.premium_callbacks import maybe_handle_premium_callback
from EbookGuy.features.filters.request_status_callbacks import (
    maybe_handle_request_status_callback,
)


async def handle_callback(client: Client, query: CallbackQuery):
    if query.data == "close_data":
        await query.message.delete()
        return

    if await maybe_handle_premium_callback(client, query):
        return
    if await maybe_handle_filter_management_callback(client, query):
        return
    if await maybe_handle_connection_callback(client, query):
        return
    if await maybe_handle_alert_callback(client, query):
        return
    if await maybe_handle_file_callback(client, query):
        return
    if await maybe_handle_request_status_callback(client, query):
        return
