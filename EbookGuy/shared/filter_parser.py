import ast
import re

from pyrogram.types import InlineKeyboardButton


BTN_URL_REGEX = re.compile(
    r"(\[([^\[]+?)\]\((buttonurl|buttonalert):"
    r"(?:/{0,2})(.+?)(:same)?\))"
)


def parse_stored_buttons(buttons):
    """Parse stored inline keyboard button data without executing code."""
    return ast.literal_eval(buttons)


def _is_escaped(text, match_start):
    escape_count = 0
    index = match_start - 1
    while index > 0 and text[index] == "\\":
        escape_count += 1
        index -= 1
    return escape_count % 2 != 0, index


def _append_button(buttons, button, same_row):
    if same_row and buttons:
        buttons[-1].append(button)
    else:
        buttons.append([button])


def _parse_filter_buttons(text, keyword, alert_prefix):
    if "buttonalert" in text:
        text = text.replace("\n", "\\n").replace("\t", "\\t")

    buttons = []
    alerts = []
    note_parts = []
    previous_end = 0
    alert_index = 0
    for match in BTN_URL_REGEX.finditer(text):
        is_escaped, escape_start = _is_escaped(
            text,
            match.start(1),
        )
        if is_escaped:
            note_parts.append(text[previous_end:escape_start])
            previous_end = match.start(1) - 1
            continue

        note_parts.append(text[previous_end:match.start(1)])
        previous_end = match.end(1)
        same_row = bool(match.group(5))
        if match.group(3) == "buttonalert":
            button = InlineKeyboardButton(
                text=match.group(2),
                callback_data=(
                    f"{alert_prefix}:{alert_index}:{keyword}"
                ),
            )
            alert_index += 1
            alerts.append(match.group(4))
        else:
            button = InlineKeyboardButton(
                text=match.group(2),
                url=match.group(4).replace(" ", ""),
            )
        _append_button(buttons, button, same_row)

    note_parts.append(text[previous_end:])
    return "".join(note_parts), buttons, alerts


def gfilterparser(text, keyword):
    return _parse_filter_buttons(
        text,
        keyword,
        "gfilteralert",
    )


def parser(text, keyword):
    return _parse_filter_buttons(
        text,
        keyword,
        "alertmessage",
    )
