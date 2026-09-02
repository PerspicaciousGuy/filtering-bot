"""Inline format selection for user book requests."""

from dataclasses import dataclass

from bson import ObjectId
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup


REQUEST_FORMAT_CALLBACK = "request_format"
REQUEST_FORMAT_LABELS = {
    "ebook": "\U0001f4d6 Ebook",
    "audiobook": "\U0001f3a7 Audiobook",
}


@dataclass(frozen=True)
class RequestFormatSelection:
    """A validated format-selection callback payload."""

    request_id: ObjectId
    request_format: str
    user_id: int


def request_format_markup(request_id, user_id):
    """Build the one-time Ebook, Audiobook, and Cancel selection keyboard."""
    def format_button(request_format):
        return InlineKeyboardButton(
            REQUEST_FORMAT_LABELS[request_format],
            callback_data=(
                f"{REQUEST_FORMAT_CALLBACK}#{request_id}#"
                f"{request_format}#{user_id}"
            ),
        )

    return InlineKeyboardMarkup(
        [
            [format_button("ebook"), format_button("audiobook")],
            [
                InlineKeyboardButton(
                    "Cancel",
                    callback_data=(
                        f"{REQUEST_FORMAT_CALLBACK}#{request_id}#"
                        f"cancel#{user_id}"
                    ),
                )
            ],
        ]
    )


def _parse_format_selection(data):
    parts = data.split("#")
    if len(parts) != 4 or parts[0] != REQUEST_FORMAT_CALLBACK:
        raise ValueError("Invalid format selection")
    _, request_id, request_format, user_id = parts
    if request_format not in {*REQUEST_FORMAT_LABELS, "cancel"}:
        raise ValueError("Invalid request format")
    try:
        return RequestFormatSelection(
            request_id=ObjectId(request_id),
            request_format=request_format,
            user_id=int(user_id),
        )
    except (TypeError, ValueError) as error:
        raise ValueError("Invalid format selection") from error


async def handle_request_format_callback(bot, query, submit_selected_format):
    """Submit or cancel a request after its owner selects a format."""
    try:
        selection = _parse_format_selection(query.data)
    except ValueError:
        await query.answer("This request selection is invalid.", show_alert=True)
        return
    if query.from_user.id != selection.user_id:
        await query.answer(
            "This format selection does not belong to you.",
            show_alert=True,
        )
        return
    if selection.request_format == "cancel":
        await query.answer("Request cancelled")
        await query.message.edit_text("Your request has been cancelled.")
        return
    source_message = query.message.reply_to_message
    if source_message is None:
        await query.answer("Please send the request again.", show_alert=True)
        return
    if source_message.from_user.id != selection.user_id:
        await query.answer("This request selection is invalid.", show_alert=True)
        return
    label = REQUEST_FORMAT_LABELS[selection.request_format]
    await query.answer(f"{label} selected")
    await query.message.edit_text(f"{label} selected. Submitting request...")
    was_submitted = await submit_selected_format(
        bot,
        source_message,
        selection,
    )
    result = f"{label} selected." if was_submitted else "Request not submitted."
    await query.message.edit_text(result)


__all__ = [
    "REQUEST_FORMAT_LABELS",
    "RequestFormatSelection",
    "handle_request_format_callback",
    "request_format_markup",
]
