import math
from dataclasses import dataclass

from pyrogram.types import InlineKeyboardButton

from info import MAX_B_TN
from utils import get_size, save_group_settings


@dataclass(frozen=True)
class PaginationState:
    requester_id: str
    key: str
    offset: int
    next_offset: int
    total_results: int
    page_size: int


def normalize_offset(value):
    try:
        return int(value)
    except (TypeError, ValueError):
        return 0


def build_file_buttons(files, prefix):
    return [
        [
            InlineKeyboardButton(
                text=(
                    f"[{get_size(file['file_size'])}] "
                    + " ".join(
                        part
                        for part in file["file_name"].split()
                        if not part.startswith("[")
                        and not part.startswith("@")
                        and not part.startswith("www.")
                    )
                ),
                callback_data=f"{prefix}#{file['file_id']}",
            )
        ]
        for file in files
    ]


async def get_page_size(settings, chat_id):
    try:
        uses_default_size = settings["max_btn"]
    except KeyError:
        await save_group_settings(chat_id, "max_btn", True)
        uses_default_size = True
    return 10 if uses_default_size else int(MAX_B_TN)


def build_pagination_row(state, is_initial=False):
    total_pages = math.ceil(state.total_results / state.page_size)
    next_callback = (
        f"next_{state.requester_id}_{state.key}_{state.next_offset}"
    )
    if is_initial:
        if state.next_offset == 0:
            return [
                InlineKeyboardButton(
                    "No More Pages Available",
                    callback_data="pages",
                )
            ]
        return [
            InlineKeyboardButton("Page", callback_data="pages"),
            InlineKeyboardButton(f"1/{total_pages}", callback_data="pages"),
            InlineKeyboardButton(
                "Next \u27aa",
                callback_data=next_callback,
            ),
        ]

    previous_offset = None
    if state.offset > 0:
        previous_offset = max(0, state.offset - state.page_size)
    page_number = math.ceil(state.offset / state.page_size) + 1
    page_button = InlineKeyboardButton(
        f"{page_number} / {total_pages}",
        callback_data="pages",
    )
    back_button = InlineKeyboardButton(
        "\u232b Back",
        callback_data=(
            f"next_{state.requester_id}_{state.key}_{previous_offset}"
        ),
    )
    if state.next_offset == 0:
        return [back_button, page_button]
    next_button = InlineKeyboardButton(
        "Next \u27aa",
        callback_data=next_callback,
    )
    if previous_offset is None:
        return [
            InlineKeyboardButton("Page", callback_data="pages"),
            page_button,
            next_button,
        ]
    return [back_button, page_button, next_button]
