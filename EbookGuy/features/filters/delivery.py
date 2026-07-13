import asyncio
import re
from collections.abc import Awaitable, Callable, Iterable
from dataclasses import dataclass, field

from pyrogram import Client
from pyrogram.types import InlineKeyboardMarkup, Message

from database.connections_mdb import active_connection
from EbookGuy.features.search.results import AutoFilterRequest, auto_filter
from EbookGuy.shared.filter_parser import parse_stored_buttons
from utils import get_settings, save_group_settings


@dataclass(frozen=True)
class FilterPayload:
    """Stored filter content required to render one Telegram message."""

    reply_text: str | None
    buttons_data: str
    file_id: str
    reply_id: int
    protect_content: bool


@dataclass
class FilterWorkflow:
    """Runtime state shared by post-delivery filter actions."""

    client: Client
    source_message: Message
    sent_message: Message
    settings: dict[str, object]
    repaired_settings: set[str] = field(default_factory=set)


@dataclass(frozen=True)
class StoredFilter:
    """Normalized stored filter data ready for message delivery."""

    reply_text: str | None
    buttons_data: str
    file_id: str


async def find_matching_filter(
    name: str,
    keywords: Iterable[str],
    fetch_filter: Callable[
        [str],
        Awaitable[tuple[str | None, str | None, object, str]],
    ],
) -> StoredFilter | None:
    """Find the longest matching keyword with deliverable stored content."""
    for keyword in reversed(sorted(keywords, key=len)):
        pattern = r"( |^|[^\w])" + re.escape(keyword) + r"( |$|[^\w])"
        if not re.search(pattern, name, flags=re.IGNORECASE):
            continue

        reply_text, buttons_data, _, file_id = await fetch_filter(keyword)
        if buttons_data is None:
            continue
        if reply_text:
            reply_text = reply_text.replace("\\n", "\n").replace(
                "\\t",
                "\t",
            )
        return StoredFilter(reply_text, buttons_data, file_id)
    return None


async def send_filter_message(
    client: Client,
    message: Message,
    payload: FilterPayload,
) -> tuple[Message, bool]:
    """Render stored text or media and return whether the result is media."""
    if payload.file_id == "None":
        reply_markup = None
        if payload.buttons_data != "[]":
            reply_markup = InlineKeyboardMarkup(
                parse_stored_buttons(payload.buttons_data)
            )
        sent_message = await client.send_message(
            message.chat.id,
            payload.reply_text,
            disable_web_page_preview=True,
            reply_markup=reply_markup,
            protect_content=payload.protect_content,
            reply_to_message_id=payload.reply_id,
        )
        return sent_message, False

    if payload.buttons_data == "[]":
        sent_message = await client.send_cached_media(
            message.chat.id,
            payload.file_id,
            caption=payload.reply_text or "",
            protect_content=payload.protect_content,
            reply_to_message_id=payload.reply_id,
        )
        return sent_message, True

    sent_message = await message.reply_cached_media(
        payload.file_id,
        caption=payload.reply_text or "",
        reply_markup=InlineKeyboardMarkup(
            parse_stored_buttons(payload.buttons_data)
        ),
        reply_to_message_id=payload.reply_id,
    )
    return sent_message, True


async def is_setting_enabled(
    workflow: FilterWorkflow,
    key: str,
) -> bool:
    """Read a filter setting, repairing missing legacy settings as enabled."""
    try:
        return bool(workflow.settings[key])
    except KeyError:
        workflow.repaired_settings.add(key)
        group_id = await active_connection(
            str(workflow.source_message.from_user.id)
        )
        await save_group_settings(group_id, key, True)
        workflow.settings = await get_settings(
            workflow.source_message.chat.id
        )
        return bool(workflow.settings[key])


async def run_auto_search(workflow: FilterWorkflow) -> None:
    """Run automatic search using the original filter-triggering message."""
    message = workflow.source_message
    reply_message = await message.reply_text(
        f"<b><i>Searching For {message.text} \U0001F50D</i></b>"
    )
    await auto_filter(
        AutoFilterRequest(
            name=message.text,
            message=message,
            reply_message=reply_message,
        )
    )


async def delete_filter_message(
    workflow: FilterWorkflow,
    delay_seconds: int = 0,
) -> None:
    """Delete a sent filter message when auto-delete is enabled."""
    if not await is_setting_enabled(workflow, "auto_delete"):
        return
    if delay_seconds:
        await asyncio.sleep(delay_seconds)
    await workflow.sent_message.delete()
