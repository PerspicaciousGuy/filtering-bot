from pyrogram import Client
from pyrogram.types import CallbackQuery

from plugins.pm_filter_alert_callbacks import maybe_handle_alert_callback
from plugins.pm_filter_connection_callbacks import maybe_handle_connection_callback
from plugins.pm_filter_file_callbacks import maybe_handle_file_callback
from plugins.pm_filter_filter_management_callbacks import (
    maybe_handle_filter_management_callback,
)
from plugins.pm_filter_premium_callbacks import maybe_handle_premium_callback
from plugins.pm_filter_request_status_callbacks import (
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
