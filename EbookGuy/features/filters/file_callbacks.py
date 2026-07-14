import asyncio
import logging

from pyrogram.errors import PeerIdInvalid, RPCError, UserIsBlocked
from pymongo.errors import PyMongoError

from database.ia_filterdb import (
    delete_file_by_id,
    get_bad_files,
    get_file_details,
)
from utils import (
    get_settings,
    is_subscribed,
    pub_is_subscribed,
    temp,
)


logger = logging.getLogger(__name__)
logger.setLevel(logging.ERROR)
lock = asyncio.Lock()

CALLBACK_ERRORS = (
    AttributeError,
    KeyError,
    PyMongoError,
    RPCError,
    TypeError,
    ValueError,
)


def _file_start_url(prefix, file_id):
    return f"https://telegram.me/{temp.U_NAME}?start={prefix}_{file_id}"


async def _handle_file_link(query):
    prefix, file_id = query.data.split("#")
    file = await get_file_details(file_id)
    if not file:
        await query.answer("No such file exist.")
        return

    clicked_user_id = query.from_user.id
    try:
        requesting_user_id = query.message.reply_to_message.from_user.id
    except CALLBACK_ERRORS:
        requesting_user_id = clicked_user_id

    try:
        if clicked_user_id == requesting_user_id:
            await query.answer(url=_file_start_url(prefix, file_id))
        else:
            await query.answer(
                f"Hey {query.from_user.first_name}, This Is Not Your Movie "
                "Request. Request Your's !",
                show_alert=True,
            )
    except UserIsBlocked:
        await query.answer("Unblock the bot mahn !", show_alert=True)
    except (PeerIdInvalid, *CALLBACK_ERRORS):
        await query.answer(url=_file_start_url(prefix, file_id))


async def _handle_sendfiles(query):
    _, key = query.data.split("#")
    settings = await get_settings(query.message.chat.id)
    prefix = "allfilesp" if settings["file_secure"] else "allfiles"
    url = _file_start_url(prefix, key)
    try:
        await query.answer(url=url)
    except UserIsBlocked:
        await query.answer("Unblock the bot mahn !", show_alert=True)
    except PeerIdInvalid:
        await query.answer(url=url)
    except CALLBACK_ERRORS:
        logger.exception("Failed to answer sendfiles callback")
        await query.answer(url=url)


async def _handle_unmute(client, query):
    _, user_id = query.data.split("#")
    settings = await get_settings(int(query.message.chat.id))
    if int(user_id) == 0:
        await query.answer("You are anonymous admin !", show_alert=True)
        return

    try:
        button = await pub_is_subscribed(client, query, settings["fsub"])
        if button:
            await query.answer(
                "Kindly Join Given Channel Then Click On Unmute Button",
                show_alert=True,
            )
            return
        await client.unban_chat_member(
            query.message.chat.id,
            query.from_user.id,
        )
        await query.answer("Unmuted Successfully !", show_alert=True)
        try:
            await query.message.delete()
        except CALLBACK_ERRORS:
            return
    except CALLBACK_ERRORS:
        await query.answer("Not For Your My Dear", show_alert=True)


async def _handle_delete_link(query):
    _, file_id = query.data.split("#")
    if not await get_file_details(file_id):
        await query.answer("No such file exist.")
        return
    await query.answer(url=_file_start_url("file", file_id))


async def _handle_check_subscription(client, query):
    if not await is_subscribed(client, query):
        await query.answer(
            "Join our Back-up channel mahn! \U0001f612",
            show_alert=True,
        )
        return
    _, prefix, file_id = query.data.split("#")
    await query.answer(url=_file_start_url(prefix, file_id))


async def _handle_delete_pages(query):
    _, keyword = query.data.split("#")
    files, _ = await get_bad_files(keyword)
    await query.message.edit_text(
        "<b>File deletion process will start in 5 seconds !</b>"
    )
    await asyncio.sleep(5)
    deleted = 0
    async with lock:
        try:
            for file in files:
                deleted_count = await delete_file_by_id(file["file_id"])
                if deleted_count:
                    logger.info(
                        "Deleted %s for query %s",
                        file["file_name"],
                        keyword,
                    )
                deleted += deleted_count
                if deleted and deleted % 50 == 0:
                    await query.message.edit_text(
                        "<b>Process started for deleting files from DB. "
                        f"Successfully deleted {deleted} files from DB for "
                        f"your query {keyword} !\n\nPlease wait...</b>"
                    )
        except CALLBACK_ERRORS:
            logger.exception("Failed while deleting files from database")
            await query.message.edit_text(
                "Error deleting files. Please try again later."
            )
            return
    await query.message.edit_text(
        "<b>Process Completed for file deletion !\n\n"
        f"Successfully deleted {deleted} files from database for your query "
        f"{keyword}.</b>"
    )


async def maybe_handle_file_callback(client, query):
    action = query.data.partition("#")[0]
    if action.startswith("file"):
        await _handle_file_link(query)
    elif action == "sendfiles":
        await _handle_sendfiles(query)
    elif action == "unmuteme":
        await _handle_unmute(client, query)
    elif action == "del":
        await _handle_delete_link(query)
    elif action == "checksub":
        await _handle_check_subscription(client, query)
    elif action == "pages":
        if "#" in query.data:
            await _handle_delete_pages(query)
        else:
            await query.answer()
    else:
        return False
    return True
