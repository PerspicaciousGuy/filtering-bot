"""Presentation helpers for validated settings restore previews."""

from dataclasses import dataclass
from html import escape

from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from EbookGuy.shared.settings_backup import ParsedSettingsBackup
from EbookGuy.shared.settings_catalog import SETTING_LABELS


CALLBACK_PREFIX = "global_settings:backup"
MAX_PREVIEW_ROWS = 12


@dataclass(frozen=True)
class PendingRestore:
    """Validated changes awaiting explicit administrator confirmation."""

    changes: dict[str, object]
    current_values: dict[str, object]
    parsed: ParsedSettingsBackup
    expires_at: float


def _preview_value(value: object) -> str:
    text = str(value).replace("\n", " ")
    if len(text) > 45:
        text = f"{text[:45]}..."
    return escape(text)


def build_restore_preview(
    pending: PendingRestore,
) -> tuple[str, InlineKeyboardMarkup]:
    """Build a bounded summary and confirmation controls for a restore."""
    changed_items = list(pending.changes.items())
    lines = [
        "<b>Restore Settings Preview</b>",
        "",
        f"<b>Changed:</b> {len(changed_items)}",
        (
            f"<b>Unchanged:</b> "
            f"{len(pending.parsed.settings) - len(changed_items)}"
        ),
        f"<b>Ignored unknown:</b> {len(pending.parsed.unknown_keys)}",
        f"<b>Missing and preserved:</b> {len(pending.parsed.missing_keys)}",
    ]
    if changed_items:
        lines.extend(["", "<b>Changes:</b>"])
        for key, new_value in changed_items[:MAX_PREVIEW_ROWS]:
            lines.append(
                f"- {escape(SETTING_LABELS[key])}: "
                f"<code>{_preview_value(pending.current_values[key])}</code> "
                f"-> <code>{_preview_value(new_value)}</code>"
            )
        remaining = len(changed_items) - MAX_PREVIEW_ROWS
        if remaining > 0:
            lines.append(f"- ...and {remaining} more")
    if pending.parsed.unknown_keys:
        names = ", ".join(pending.parsed.unknown_keys[:8])
        lines.extend(["", f"<b>Ignored:</b> <code>{escape(names)}</code>"])

    rows = []
    if changed_items:
        rows.append([InlineKeyboardButton(
            "Confirm Restore",
            callback_data=f"{CALLBACK_PREFIX}:confirm",
        )])
    rows.append([InlineKeyboardButton(
        "Cancel",
        callback_data=f"{CALLBACK_PREFIX}:cancel",
    )])
    return "\n".join(lines), InlineKeyboardMarkup(rows)


__all__ = ["PendingRestore", "build_restore_preview"]
