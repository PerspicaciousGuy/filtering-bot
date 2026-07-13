import logging

from pyrogram.errors import MessageNotModified
from pyrogram.types import InlineKeyboardMarkup

from Script import script
from database.search_repository import SearchRequest, get_search_results
from EbookGuy.features.search.models import NextPageView, PageRequest
from EbookGuy.features.search.pagination import (
    PaginationState,
    build_file_buttons,
    build_pagination_row,
    get_page_size,
    normalize_offset,
)
from EbookGuy.features.search.state import FRESH
from EbookGuy.shared.global_settings import get_global_settings
from info import BUTTON_MODE
from utils import get_cap, temp


logger = logging.getLogger(__name__)


def _fresh_search(key):
    fresh_data = FRESH.get(key)
    if isinstance(fresh_data, dict):
        return fresh_data.get("query"), fresh_data.get("format_type")
    return fresh_data, None


async def _page_request(query):
    _, requester_id, key, raw_offset = query.data.split("_")
    if int(requester_id) not in (query.from_user.id, 0):
        await query.answer(
            script.ALRT_TXT.format(query.from_user.first_name),
            show_alert=True,
        )
        return None
    search, format_type = _fresh_search(key)
    if not search:
        await query.answer(
            script.OLD_ALRT_TXT.format(query.from_user.first_name),
            show_alert=True,
        )
        return None
    return PageRequest(
        requester_id=requester_id,
        key=key,
        offset=normalize_offset(raw_offset),
        search=search,
        format_type=format_type,
    )


async def _page_view(query, request):
    global_settings = await get_global_settings()
    if not global_settings["search_enabled"]:
        await query.answer("Search is temporarily disabled.", show_alert=True)
        return None
    page_size = get_page_size(global_settings)
    files, next_offset, total = await get_search_results(SearchRequest(
        request.search,
        max_results=page_size,
        offset=request.offset,
        format_type=request.format_type,
        result_limit=int(global_settings["max_search_results"]),
        use_caption_filter=bool(global_settings["use_caption_filter"]),
    ))
    if not files:
        return None
    temp.GETALL[request.key] = files
    temp.SHORT[query.from_user.id] = query.message.chat.id
    prefix = "filep" if global_settings["protect_content"] else "file"
    buttons = build_file_buttons(files, prefix) if BUTTON_MODE else []
    buttons.append(build_pagination_row(PaginationState(
        requester_id=request.requester_id,
        key=request.key,
        offset=request.offset,
        next_offset=normalize_offset(next_offset),
        total_results=total,
        page_size=page_size,
    )))
    return NextPageView(
        files,
        request.search,
        prefix,
        buttons,
        int(global_settings["search_result_expiry_seconds"]),
    )


async def _render_next_page(query, view):
    reply_markup = InlineKeyboardMarkup(view.buttons)
    try:
        if BUTTON_MODE:
            await query.edit_message_reply_markup(reply_markup=reply_markup)
        else:
            await query.message.edit_text(
                text=get_cap(
                    view.files,
                    view.search,
                    (view.prefix, view.expiry_seconds),
                ),
                reply_markup=reply_markup,
                disable_web_page_preview=True,
            )
    except MessageNotModified:
        logger.debug("Search results message is already current")


async def handle_next_page(bot, query):
    """Validate and render one search-results page callback."""
    request = await _page_request(query)
    if request is None:
        return
    view = await _page_view(query, request)
    if view is None:
        return
    await _render_next_page(query, view)
    await query.answer()
