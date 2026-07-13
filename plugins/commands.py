from pyrogram import Client, filters

from info import ADMINS
from EbookGuy.shared.callback_metrics import measure_callback, measure_command
from EbookGuy.features.admin.commands import (
    handle_channel_info,
    handle_delete,
    handle_delete_all_index,
    handle_delete_all_index_confirm,
    handle_deletemultiplefiles,
    handle_log_file,
    handle_send_msg,
    handle_stats,
    handle_stop_button,
)
from EbookGuy.features.admin.settings_callbacks import handle_settings_callback
from EbookGuy.features.admin.settings_commands import handle_settings_command
from EbookGuy.features.downloads.conversion import (
    handle_convert_back_callback,
    handle_convert_menu_callback,
    handle_do_convert_callback,
)
from plugins.commands_downloads import (
    handle_download_book_callback,
    handle_start,
)
from EbookGuy.features.requests.commands import handle_requests


@Client.on_message(filters.command("start") & filters.incoming & filters.private)
async def start(client, message):
    await handle_start(client, message)


@Client.on_callback_query(filters.regex(r"^download_book#"))
@measure_callback("download_book")
async def download_book_callback(client, query):
    await handle_download_book_callback(client, query)


@Client.on_callback_query(filters.regex(r"^convert_menu#"))
@measure_callback("convert_menu")
async def convert_menu_callback(client, query):
    await handle_convert_menu_callback(client, query)


@Client.on_callback_query(filters.regex(r"^do_convert#"))
@measure_callback("do_convert")
async def do_convert_callback(client, query):
    await handle_do_convert_callback(client, query)


@Client.on_callback_query(filters.regex(r"^convert_back#"))
@measure_callback("convert_back")
async def convert_back_callback(client, query):
    await handle_convert_back_callback(client, query)


@Client.on_message(filters.command('channel') & filters.user(ADMINS))
async def channel_info(bot, message):
    await handle_channel_info(bot, message)


@Client.on_message(
    filters.command("settings") & filters.user(ADMINS) & filters.private
)
@measure_command("settings")
async def settings_command(client, message):
    await handle_settings_command(client, message)


@Client.on_callback_query(filters.regex(r"^global_settings:"))
@measure_callback("global_settings")
async def settings_callback(client, query):
    await handle_settings_callback(client, query)


@Client.on_message(filters.command('logs') & filters.user(ADMINS))
async def log_file(bot, message):
    await handle_log_file(bot, message)


@Client.on_message(filters.command('delete') & filters.user(ADMINS))
async def delete(bot, message):
    await handle_delete(bot, message)


@Client.on_message(filters.command('deleteall') & filters.user(ADMINS))
async def delete_all_index(bot, message):
    await handle_delete_all_index(bot, message)


@Client.on_callback_query(filters.regex(r'^autofilter_delete'))
@measure_callback("delete_all_index")
async def delete_all_index_confirm(bot, query):
    await handle_delete_all_index_confirm(bot, query)


@Client.on_message((filters.command(["request", "Request"]) | filters.regex("#request") | filters.regex("#Request")) & filters.private)
@measure_command("request_book")
async def requests(bot, message):
    await handle_requests(bot, message)


@Client.on_message(filters.command("send") & filters.user(ADMINS))
async def send_msg(bot, message):
    await handle_send_msg(bot, message)


@Client.on_message(filters.command("deletefiles") & filters.user(ADMINS) & filters.private)
async def deletemultiplefiles(bot, message):
    await handle_deletemultiplefiles(bot, message)


@Client.on_message(filters.command("stats") & filters.user(ADMINS))
async def stats(client, message):
    await handle_stats(client, message)


@Client.on_message(filters.command("restart") & filters.user(ADMINS))
async def stop_button(bot, message):
    await handle_stop_button(bot, message)
