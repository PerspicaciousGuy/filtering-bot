import logging
from urllib.parse import quote_plus

from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from Script import script
from EbookGuy.features.search.expiry import SearchExpiry, schedule_search_expiry
from EbookGuy.features.search.pagination import (
    NO_MORE_PAGES_TEXT,
    PaginationState,
    build_file_buttons,
    build_pagination_row,
    get_page_size,
    normalize_offset,
)
from EbookGuy.features.search.state import FRESH, PENDING_SEARCH
from EbookGuy.shared.bot_api import (
    BotApiError,
    call_bot_api,
    disabled_button_payload,
    inline_button_payload,
)
from info import BUTTON_MODE
from utils import get_cap, temp

logger = logging.getLogger(__name__)


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


def _disabled_last_page_keyboard(buttons):
    """Return Bot API rows with a disabled "No More Pages" button, or None."""
    last_row = buttons[-1] if buttons else []
    if len(last_row) != 1 or last_row[0].text != NO_MORE_PAGES_TEXT:
        return None
    rows = []
    for row in buttons[:-1]:
        payload_row = [inline_button_payload(button) for button in row]
        if None in payload_row:
            return None
        rows.append(payload_row)
    rows.append([disabled_button_payload(NO_MORE_PAGES_TEXT)])
    return rows


async def _edit_with_disabled_last_page(result_message, text, buttons):
    """Show single-page results with a disabled button via the Bot API.

    Pyrofork cannot send disabled buttons (Bot API 10.3), so this one edit
    goes through the Bot API. Returns False when the caller should fall back
    to the normal Pyrogram edit.
    """
    keyboard = _disabled_last_page_keyboard(buttons)
    if keyboard is None:
        return False
    try:
        await call_bot_api("editMessageText", {
            "chat_id": result_message.chat.id,
            "message_id": result_message.id,
            "text": text,
            "parse_mode": "HTML",
            "link_preview_options": {"is_disabled": True},
            "reply_markup": {"inline_keyboard": keyboard},
        })
    except BotApiError as error:
        logger.info("Falling back to a normal results edit: %s", error)
        return False
    return True


async def show_search_results(request, outcome):
    message = request.message
    key = f"{message.chat.id}-{message.id}"
    FRESH[key] = {"query": outcome.search, "format_type": request.format_type}
    temp.GETALL[key] = outcome.files
    buttons, prefix, requester_id = await _initial_buttons(request, outcome, key)
    temp.SHORT[requester_id] = message.chat.id
    text = _result_caption(outcome, prefix)
    result_message = request.reply_message
    if not await _edit_with_disabled_last_page(result_message, text, buttons):
        result_message = await result_message.edit_text(
            text=text,
            reply_markup=InlineKeyboardMarkup(buttons),
            disable_web_page_preview=True,
        )
    schedule_search_expiry(SearchExpiry(
        key=key,
        delay_seconds=int(outcome.settings["search_result_expiry_seconds"]),
        messages=(message, result_message),
    ))
