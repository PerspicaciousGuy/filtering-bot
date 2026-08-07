"""Upload, preview, and confirm global settings JSON restores."""

import asyncio
from dataclasses import dataclass
from html import escape
import logging
import time

from pyrogram import filters
from pyrogram.errors import ListenerTimeout, RPCError
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from EbookGuy.features.admin.settings_backup import build_backup_view
from EbookGuy.features.admin.settings_confirmation import (
    is_setting_confirmation_pending,
)
from EbookGuy.features.admin.settings_input import is_settings_input_active
from EbookGuy.features.admin.settings_restore_preview import (
    PendingRestore,
    build_restore_preview,
)
from EbookGuy.features.admin.settings_runtime_validation import (
    validate_runtime_settings,
)
from EbookGuy.shared.global_settings import (
    get_global_settings,
    restore_global_settings,
)
from EbookGuy.shared.settings_backup import (
    BACKUP_VERSION,
    MAX_BACKUP_BYTES,
    parse_settings_backup,
)


CALLBACK_PREFIX = "global_settings:backup"
RESTORE_TIMEOUT_SECONDS = 120
logger = logging.getLogger(__name__)
_restore_tasks: dict[int, asyncio.Task] = {}
_pending_restores: dict[int, "PendingRestore"] = {}


@dataclass(frozen=True)
class RestoreContext:
    """Telegram context for one active backup upload prompt."""

    admin_id: int
    chat_id: int
    message: object
    client: object


def is_settings_restore_active(user_id: int) -> bool:
    """Return whether an administrator is currently uploading a backup."""
    task = _restore_tasks.get(user_id)
    return task is not None and not task.done()


def _restore_markup() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [[InlineKeyboardButton(
            "Cancel",
            callback_data=f"{CALLBACK_PREFIX}:cancel",
        )]]
    )


def _restore_prompt(error: str | None = None) -> str:
    lines = [
        "<b>Restore Settings</b>",
        "",
        "Upload a settings backup JSON file in this chat.",
        f"Maximum file size: {MAX_BACKUP_BYTES // 1024} KB.",
        "Send /cancel to stop.",
    ]
    if error:
        lines.extend(["", f"<b>Not accepted:</b> {escape(error)}"])
    return "\n".join(lines)


async def _delete_message(message) -> None:
    try:
        await message.delete()
    except RPCError:
        logger.debug("Restore upload message was already unavailable")


async def _read_backup_document(client, message) -> bytes:
    document = message.document
    filename = (document.file_name or "").lower()
    if not filename.endswith(".json"):
        raise ValueError("Upload a file whose name ends with .json.")
    if document.file_size and document.file_size > MAX_BACKUP_BYTES:
        raise ValueError("The backup file is larger than 256 KB.")
    downloaded = await client.download_media(message, in_memory=True)
    if downloaded is None:
        raise ValueError("Telegram could not download the backup file.")
    downloaded.seek(0)
    data = downloaded.read(MAX_BACKUP_BYTES + 1)
    if len(data) > MAX_BACKUP_BYTES:
        raise ValueError("The backup file is larger than 256 KB.")
    return data


async def _prepare_restore(context: RestoreContext, upload) -> None:
    parsed = parse_settings_backup(
        await _read_backup_document(context.client, upload)
    )
    current = await get_global_settings()
    candidate = {**current, **parsed.settings}
    changed = {
        key: value
        for key, value in parsed.settings.items()
        if current[key] != value
    }
    await validate_runtime_settings(context.client, candidate, set(changed))
    pending = PendingRestore(
        changes=changed,
        current_values=current,
        parsed=parsed,
        expires_at=time.monotonic() + RESTORE_TIMEOUT_SECONDS,
    )
    _pending_restores[context.admin_id] = pending
    text, markup = build_restore_preview(pending)
    await context.message.edit_text(text, reply_markup=markup)


async def _collect_restore(context: RestoreContext) -> None:
    try:
        while True:
            upload = await context.client.listen(
                filters=(
                    (filters.document | filters.command("cancel"))
                    & filters.user(context.admin_id)
                ),
                timeout=RESTORE_TIMEOUT_SECONDS,
                chat_id=context.chat_id,
                user_id=context.admin_id,
            )
            if upload.text and upload.text.lower().startswith("/cancel"):
                await _delete_message(upload)
                text, markup = build_backup_view()
                await context.message.edit_text(text, reply_markup=markup)
                return
            try:
                await _prepare_restore(context, upload)
            except ValueError as error:
                await context.message.edit_text(
                    _restore_prompt(str(error)),
                    reply_markup=_restore_markup(),
                )
                await _delete_message(upload)
                continue
            await _delete_message(upload)
            return
    except ListenerTimeout:
        await context.message.edit_text(
            "<b>Restore Timed Out</b>\n\nOpen Backup & Restore to try again.",
            reply_markup=InlineKeyboardMarkup(
                [[InlineKeyboardButton(
                    "Back",
                    callback_data=f"{CALLBACK_PREFIX}:home",
                )]]
            ),
        )
    except asyncio.CancelledError:
        raise
    except RPCError:
        logger.exception("Failed while collecting a settings backup")
    finally:
        task = asyncio.current_task()
        if _restore_tasks.get(context.admin_id) is task:
            _restore_tasks.pop(context.admin_id, None)


async def start_settings_restore(client, query) -> None:
    """Start an expiring admin-only backup upload prompt."""
    admin_id = query.from_user.id
    if (
        is_settings_input_active(admin_id)
        or is_settings_restore_active(admin_id)
        or is_setting_confirmation_pending(admin_id)
    ):
        await query.answer(
            "Finish or cancel your current settings update.",
            show_alert=True,
        )
        return
    _pending_restores.pop(admin_id, None)
    await query.answer("Upload the JSON backup in this chat.")
    await query.message.edit_text(
        _restore_prompt(),
        reply_markup=_restore_markup(),
    )
    context = RestoreContext(
        admin_id=admin_id,
        chat_id=query.message.chat.id,
        message=query.message,
        client=client,
    )
    task = asyncio.create_task(_collect_restore(context))
    _restore_tasks[admin_id] = task


def _get_pending_restore(admin_id: int) -> PendingRestore | None:
    pending = _pending_restores.get(admin_id)
    if pending is not None and time.monotonic() >= pending.expires_at:
        _pending_restores.pop(admin_id, None)
        return None
    return pending


async def confirm_settings_restore(query) -> None:
    """Apply one previously validated restore preview."""
    admin_id = query.from_user.id
    pending = _get_pending_restore(admin_id)
    if pending is None:
        await query.answer("This restore preview expired.", show_alert=True)
        text, markup = build_backup_view()
        await query.message.edit_text(text, reply_markup=markup)
        return
    details = {
        "backup_version": BACKUP_VERSION,
        "backup_created_at": pending.parsed.created_at,
        "changed_settings": sorted(pending.changes),
        "changed_count": len(pending.changes),
        "ignored_unknown_count": len(pending.parsed.unknown_keys),
        "missing_preserved_count": len(pending.parsed.missing_keys),
    }
    changed_count = await restore_global_settings(
        pending.changes,
        admin_id,
        details,
    )
    _pending_restores.pop(admin_id, None)
    await query.answer("Settings restored")
    await query.message.edit_text(
        "<b>Settings Restored</b>\n\n"
        f"Applied <b>{changed_count}</b> setting change(s).",
        reply_markup=InlineKeyboardMarkup(
            [[InlineKeyboardButton(
                "Back to Backup & Restore",
                callback_data=f"{CALLBACK_PREFIX}:home",
            )]]
        ),
    )


async def cancel_settings_restore(query) -> None:
    """Cancel an active upload or pending restore preview."""
    admin_id = query.from_user.id
    task = _restore_tasks.pop(admin_id, None)
    if task is not None and not task.done():
        task.cancel()
    _pending_restores.pop(admin_id, None)
    text, markup = build_backup_view()
    await query.answer("Restore cancelled")
    await query.message.edit_text(text, reply_markup=markup)


__all__ = [
    "cancel_settings_restore",
    "confirm_settings_restore",
    "is_settings_restore_active",
    "start_settings_restore",
]
