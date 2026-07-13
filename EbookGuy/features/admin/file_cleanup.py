import logging

from pyrogram.errors import RPCError
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from pymongo.errors import PyMongoError

from database.ia_filterdb import (
    col,
    delete_file_record,
    sec_col,
    unpack_new_file_id,
)
from info import ADMINS
from utils import get_size


logger = logging.getLogger(__name__)
DATABASE_ERRORS = (KeyError, PyMongoError, RPCError, TypeError, ValueError)


def _message_media(message):
    for file_type in ("document", "video", "audio"):
        media = getattr(message, file_type, None)
        if media is not None:
            return media
    return None


def _deletion_reply(file_name, file_size, deleted_count):
    details = (
        f"\n\n\U0001f4c1 <code>{file_name}</code>"
        f"\n\U0001f4be Size: {file_size}"
    )
    if deleted_count == 1:
        return "\u2705 <b>File Deleted Successfully!</b>" + details
    if deleted_count > 1:
        return (
            f"\u2705 <b>{deleted_count} Files Deleted!</b>"
            + details
            + "\n\n<i>\u2139\ufe0f Multiple duplicates were removed</i>"
        )
    return (
        "\u274c <b>File Not Found in Database</b>"
        + details
        + "\n\n<i>This file may have already been deleted or was never indexed.</i>"
    )


async def handle_delete_media(bot, message):
    """Delete database records matching media sent to a delete channel."""
    try:
        media = _message_media(message)
        if media is None:
            return
        file_name = getattr(media, "file_name", "Unknown")
        total_deleted = await delete_file_record(
            unpack_new_file_id(media.file_id),
            media.file_name,
            media.file_size,
        )
        reply = _deletion_reply(
            file_name,
            get_size(media.file_size),
            total_deleted,
        )
        await message.reply_text(reply)
        logger.info("Deleted %s file record(s): %s", total_deleted, file_name)
    except DATABASE_ERRORS:
        logger.exception("File deletion handler failed")


def _duplicate_pipeline(include_report_sort=False):
    pipeline = [
        {"$group": {
            "_id": {"file_name": "$file_name", "file_size": "$file_size"},
            "count": {"$sum": 1},
            "ids": {"$push": "$_id"},
        }},
        {"$match": {"count": {"$gt": 1}}},
    ]
    if include_report_sort:
        pipeline.extend([
            {"$sort": {"count": -1}},
            {"$limit": 20},
        ])
    return pipeline


def _duplicate_report(duplicates, secondary_duplicates):
    groups = len(duplicates) + len(secondary_duplicates)
    wasted = sum(
        item["count"] - 1
        for item in duplicates + secondary_duplicates
    )
    text = (
        "\U0001f4ca <b>Duplicate Files Report</b>\n\n"
        f"\U0001f522 Total duplicate groups: <b>{groups}</b>\n"
        f"\U0001f5d1\ufe0f Redundant copies: <b>{wasted}</b>\n\n"
        "<b>Top Duplicates:</b>\n\n"
    )
    for index, duplicate in enumerate(duplicates[:10], 1):
        name = duplicate["_id"]["file_name"]
        display_name = name[:40] + "..." if len(name) > 40 else name
        size_value = duplicate["_id"]["file_size"]
        size = get_size(size_value) if size_value else "Unknown"
        text += (
            f"{index}. <code>{display_name}</code>\n"
            f"   \U0001f4cb {duplicate['count']} copies | \U0001f4be {size}\n\n"
        )
    return text


async def handle_find_duplicates(bot, message):
    status = await message.reply_text(
        "\U0001f50d <b>Scanning for duplicates...</b>\n\n"
        "<i>This may take a while depending on database size.</i>"
    )
    try:
        pipeline = _duplicate_pipeline(include_report_sort=True)
        duplicates = await col.aggregate(pipeline).to_list(length=None)
        secondary = await sec_col.aggregate(pipeline).to_list(length=None)
        if not duplicates and not secondary:
            await status.edit_text(
                "\u2705 <b>No duplicates found!</b>\n\n"
                "<i>Your database is clean.</i>"
            )
            return
        markup = InlineKeyboardMarkup([[
            InlineKeyboardButton(
                "\U0001f5d1\ufe0f Clean All Duplicates",
                callback_data="clean_duplicates",
            )
        ]])
        await status.edit_text(
            _duplicate_report(duplicates, secondary),
            reply_markup=markup,
        )
    except DATABASE_ERRORS:
        logger.exception("Failed to find duplicate files")
        await status.edit_text(
            "<b>Error scanning duplicates.</b> Please try again later."
        )


async def _remove_duplicates(collection):
    duplicates = await collection.aggregate(
        _duplicate_pipeline()
    ).to_list(length=None)
    removed = 0
    for duplicate in duplicates:
        redundant_ids = duplicate["ids"][1:]
        if redundant_ids:
            result = await collection.delete_many({
                "_id": {"$in": redundant_ids}
            })
            removed += result.deleted_count
    return removed


async def handle_clean_duplicates(bot, query):
    if query.from_user.id not in ADMINS:
        await query.answer(
            "\u26a0\ufe0f Only admins can do this!",
            show_alert=True,
        )
        return
    await query.answer("\U0001f9f9 Cleaning duplicates...")
    await query.message.edit_text(
        "\U0001f9f9 <b>Cleaning duplicates...</b>\n\n<i>Please wait...</i>"
    )
    try:
        total_removed = await _remove_duplicates(col)
        total_removed += await _remove_duplicates(sec_col)
        await query.message.edit_text(
            "\u2705 <b>Cleanup Complete!</b>\n\n"
            f"\U0001f5d1\ufe0f Removed: <b>{total_removed}</b> duplicate files\n\n"
            "<i>Your database is now optimized.</i>"
        )
        logger.info("Cleaned %s duplicate files", total_removed)
    except DATABASE_ERRORS:
        logger.exception("Failed to clean duplicate files")
        await query.message.edit_text(
            "<b>Error cleaning duplicates.</b> Please try again later."
        )
