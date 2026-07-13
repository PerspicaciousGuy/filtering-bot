import logging
from dataclasses import dataclass

from pyrogram import emoji
from pyrogram.errors import RPCError
from pyrogram.errors.exceptions.bad_request_400 import QueryIdInvalid
from pyrogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    InlineQuery,
    InlineQueryResultCachedDocument,
)

from database.search_repository import SearchRequest, get_search_results
from EbookGuy.shared.formatting import format_file_caption
from EbookGuy.shared.global_settings import get_global_settings
from info import AUTH_CHANNEL, AUTH_USERS
from utils import get_size, is_subscribed, temp


logger = logging.getLogger(__name__)
@dataclass(frozen=True)
class InlineResultPage:
    results: list
    next_offset: int | str
    total_results: int
    query_text: str


def inline_users(query: InlineQuery):
    if AUTH_USERS:
        return bool(
            query.from_user
            and query.from_user.id in AUTH_USERS
        )
    return bool(
        query.from_user
        and query.from_user.id not in temp.BANNED_USERS
    )


def _parse_offset(value):
    try:
        return int(value or 0)
    except (TypeError, ValueError):
        return 0


def get_reply_markup(query):
    return InlineKeyboardMarkup([[
        InlineKeyboardButton(
            "Search again",
            switch_inline_query_current_chat=query,
        )
    ]])


def _build_inline_results(files, reply_markup):
    results = []
    for file in files:
        title = file["file_name"]
        size = get_size(file["file_size"])
        caption = format_file_caption(title, size, file["caption"])
        results.append(InlineQueryResultCachedDocument(
            title=title,
            document_file_id=file["file_id"],
            caption=caption or title,
            description=f"Size: {size}",
            reply_markup=reply_markup,
        ))
    return results


async def _answer_found(query, page, cache_duration):
    switch_text = f"{emoji.FILE_FOLDER} Results - {page.total_results}"
    if page.query_text:
        switch_text += f" for {page.query_text}"
    try:
        await query.answer(
            results=page.results,
            is_personal=True,
            cache_time=cache_duration,
            switch_pm_text=switch_text,
            switch_pm_parameter="start",
            next_offset=str(page.next_offset),
        )
    except QueryIdInvalid:
        logger.debug("Inline query expired before it could be answered")
    except (KeyError, RPCError, TypeError, ValueError):
        logger.exception("Failed to answer inline query")


async def _answer_empty(query, query_text, cache_duration):
    switch_text = f"{emoji.CROSS_MARK} No results"
    if query_text:
        switch_text += f' for "{query_text}"'
    await query.answer(
        results=[],
        is_personal=True,
        cache_time=cache_duration,
        switch_pm_text=switch_text,
        switch_pm_parameter="okay",
    )


def _inline_cache_duration(settings):
    if AUTH_USERS or AUTH_CHANNEL:
        return 0
    return int(settings["search_result_expiry_seconds"])


async def _load_inline_page(query, settings):
    query_text = query.query.split("|", maxsplit=1)[0].strip()
    files, next_offset, total = await get_search_results(SearchRequest(
        query_text,
        max_results=int(settings["results_per_page"]),
        offset=_parse_offset(query.offset),
        result_limit=int(settings["max_search_results"]),
        use_caption_filter=bool(settings["use_caption_filter"]),
    ))
    return InlineResultPage(
        results=_build_inline_results(files, get_reply_markup(query_text)),
        next_offset=next_offset,
        total_results=total,
        query_text=query_text,
    )


async def handle_inline_query(bot, query):
    """Show search results for an authorized inline query."""
    if not inline_users(query):
        await query.answer(
            results=[],
            cache_time=0,
            switch_pm_text="okDa",
            switch_pm_parameter="hehe",
        )
        return
    if AUTH_CHANNEL and not await is_subscribed(bot, query):
        await query.answer(
            results=[],
            cache_time=0,
            switch_pm_text="You have to subscribe my channel to use the bot",
            switch_pm_parameter="subscribe",
        )
        return
    settings = await get_global_settings()
    cache_duration = _inline_cache_duration(settings)
    if not settings["search_enabled"]:
        await query.answer(
            results=[],
            cache_time=0,
            switch_pm_text="Search is temporarily disabled",
            switch_pm_parameter="start",
        )
        return
    page = await _load_inline_page(query, settings)
    if not page.results:
        await _answer_empty(query, page.query_text, cache_duration)
        return
    await _answer_found(query, page, cache_duration)
