from urllib.parse import quote_plus

from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from Script import script
from EbookGuy.features.search.expiry import SearchExpiry, schedule_search_expiry
from EbookGuy.features.search.pagination import (
    PaginationState,
    build_file_buttons,
    build_pagination_row,
    get_page_size,
    normalize_offset,
)
from EbookGuy.features.search.state import FRESH, PENDING_SEARCH
from info import BUTTON_MODE
from utils import get_cap, temp


def _store_pending_search(request, key):
    message = request.message
    PENDING_SEARCH[key] = {
        "query": request.name,
        "chat_id": message.chat.id,
        "user_id": message.from_user.id if message.from_user else 0,
        "message_id": message.id,
    }


def _alternate_format_button(request, key):
    alternate = "audiobook" if request.format_type == "ebook" else "ebook"
    label = (
        "\U0001f3a7 Try Audiobook Instead"
        if alternate == "audiobook"
        else "\U0001f4d6 Try Ebook Instead"
    )
    return InlineKeyboardButton(
        label,
        callback_data=f"switch_format#{alternate}#{key}",
    )


def _no_results_markup(request, key, settings):
    buttons = []
    if settings["search_suggestions_enabled"]:
        buttons.append([InlineKeyboardButton(
            "\U0001f50d Check Spelling on Google",
            url=f"https://www.google.com/search?q={quote_plus(request.name)}+book",
        )])
    if request.format_type not in {"ebook", "audiobook"}:
        return InlineKeyboardMarkup(buttons) if buttons else None
    _store_pending_search(request, key)
    buttons.insert(0, [_alternate_format_button(request, key)])
    buttons.append([InlineKeyboardButton(
        "\U0001f4da Search All Formats",
        callback_data=f"switch_format#all#{key}",
    )])
    return InlineKeyboardMarkup(buttons)


async def show_no_results(request, settings):
    key = f"{request.message.chat.id}-{request.message.id}"
    format_labels = {
        "ebook": " (\U0001f4d6 Ebooks)",
        "audiobook": " (\U0001f3a7 Audiobooks)",
    }
    result_message = await request.reply_message.edit_text(
        text=(
            f"<b>\u274c No results found for:</b> <i>{request.name}</i>"
            f"{format_labels.get(request.format_type, '')}\n\n"
            + script.NO_RESULTS_MSG.format(request.name, request.name, request.name)
        ),
        reply_markup=_no_results_markup(request, key, settings),
        disable_web_page_preview=True,
    )
    schedule_search_expiry(SearchExpiry(
        key=key,
        delay_seconds=int(settings["search_result_expiry_seconds"]),
        messages=(request.message, result_message),
    ))


async def _initial_buttons(request, outcome, key):
    message = request.message
    requester_id = message.from_user.id if message.from_user else 0
    prefix = "filep" if outcome.settings["protect_content"] else "file"
    buttons = build_file_buttons(outcome.files, prefix) if BUTTON_MODE else []
    buttons.append(build_pagination_row(PaginationState(
        requester_id=str(requester_id),
        key=key,
        offset=0,
        next_offset=normalize_offset(outcome.next_offset),
        total_results=outcome.total_results,
        page_size=get_page_size(outcome.settings),
    ), is_initial=True))
    return buttons, prefix, requester_id


def _result_caption(outcome, prefix):
    expiry_seconds = int(outcome.settings["search_result_expiry_seconds"])
    if not BUTTON_MODE:
        return get_cap(
            outcome.files,
            outcome.search,
            (prefix, expiry_seconds),
        )
    return (
        f"<b>The Result for => {outcome.search}\n\n"
        f"\u26a0\ufe0f After {expiry_seconds} seconds this message will be "
        "Automatically Deleted \U0001f5d1\ufe0f\n\n</b>"
    )


async def show_search_results(request, outcome):
    message = request.message
    key = f"{message.chat.id}-{message.id}"
    FRESH[key] = {"query": outcome.search, "format_type": request.format_type}
    temp.GETALL[key] = outcome.files
    buttons, prefix, requester_id = await _initial_buttons(request, outcome, key)
    temp.SHORT[requester_id] = message.chat.id
    result_message = await request.reply_message.edit_text(
        text=_result_caption(outcome, prefix),
        reply_markup=InlineKeyboardMarkup(buttons),
        disable_web_page_preview=True,
    )
    schedule_search_expiry(SearchExpiry(
        key=key,
        delay_seconds=int(outcome.settings["search_result_expiry_seconds"]),
        messages=(message, result_message),
    ))
