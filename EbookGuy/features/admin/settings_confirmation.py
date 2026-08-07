"""Confirmation flow for payment destination setting changes."""

from dataclasses import dataclass
from html import escape
import time

from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from EbookGuy.features.admin.settings_commands import build_setting_detail
from EbookGuy.features.admin.settings_runtime_validation import (
    validate_runtime_setting,
)
from EbookGuy.shared.global_settings import (
    get_global_settings,
    reset_global_setting,
    save_global_setting,
)
from EbookGuy.shared.settings_catalog import SETTING_LABELS


CALLBACK_PREFIX = "global_settings:payment_change"
CONFIRMATION_TIMEOUT_SECONDS = 120
PROTECTED_PAYMENT_SETTINGS = frozenset({
    "upi_id",
    "upi_payee_name",
    "binance_pay_id",
    "binance_pay_url_30",
    "binance_pay_url_90",
})
_pending_changes: dict[int, "PendingSettingChange"] = {}


@dataclass(frozen=True)
class SettingChangeRequest:
    """Validated payment setting change ready for confirmation."""

    admin_id: int
    key: str
    previous_value: object
    new_value: object
    message: object
    is_reset: bool = False


@dataclass(frozen=True)
class PendingSettingChange:
    """Payment setting change awaiting an administrator decision."""

    key: str
    previous_value: object
    new_value: object
    expires_at: float
    is_reset: bool


def requires_setting_confirmation(key: str) -> bool:
    """Return whether a setting controls a payment destination."""
    return key in PROTECTED_PAYMENT_SETTINGS


def is_setting_confirmation_pending(admin_id: int) -> bool:
    """Return whether an unexpired payment setting change is waiting."""
    pending = _pending_changes.get(admin_id)
    if pending is None:
        return False
    if time.monotonic() >= pending.expires_at:
        _pending_changes.pop(admin_id, None)
        return False
    return True


def _preview_value(value: object) -> str:
    text = str(value) or "Not configured"
    if len(text) > 120:
        text = f"{text[:120]}..."
    return escape(text)


async def stage_setting_confirmation(request: SettingChangeRequest) -> None:
    """Store and display a confirmation preview for one payment change."""
    pending = PendingSettingChange(
        key=request.key,
        previous_value=request.previous_value,
        new_value=request.new_value,
        expires_at=time.monotonic() + CONFIRMATION_TIMEOUT_SECONDS,
        is_reset=request.is_reset,
    )
    _pending_changes[request.admin_id] = pending
    markup = InlineKeyboardMarkup(
        [
            [InlineKeyboardButton(
                "Confirm Change",
                callback_data=f"{CALLBACK_PREFIX}:confirm:{request.key}",
            )],
            [InlineKeyboardButton(
                "Cancel",
                callback_data=f"{CALLBACK_PREFIX}:cancel:{request.key}",
            )],
        ]
    )
    await request.message.edit_text(
        "<b>Confirm Payment Setting Change</b>\n\n"
        f"<b>{escape(SETTING_LABELS[request.key])}</b>\n\n"
        f"<b>Current:</b> <code>{_preview_value(request.previous_value)}</code>\n"
        f"<b>New:</b> <code>{_preview_value(request.new_value)}</code>\n\n"
        "Changing payment destinations can redirect user payments.",
        reply_markup=markup,
    )


def _get_pending(admin_id: int, key: str) -> PendingSettingChange | None:
    if not is_setting_confirmation_pending(admin_id):
        return None
    pending = _pending_changes[admin_id]
    return pending if pending.key == key else None


async def _show_setting(query, key: str) -> None:
    settings = await get_global_settings()
    text, markup = build_setting_detail(key, settings)
    await query.message.edit_text(text, reply_markup=markup)


async def confirm_setting_change(client, query, key: str) -> None:
    """Apply one confirmed payment destination change."""
    if not requires_setting_confirmation(key):
        await query.answer("Unknown payment setting.", show_alert=True)
        return
    admin_id = query.from_user.id
    pending = _get_pending(admin_id, key)
    if pending is None:
        await query.answer("This confirmation expired.", show_alert=True)
        await _show_setting(query, key)
        return
    try:
        await validate_runtime_setting(client, key, pending.new_value)
    except ValueError as error:
        await query.answer(str(error), show_alert=True)
        return
    if pending.is_reset:
        await reset_global_setting(key, admin_id)
    else:
        await save_global_setting(key, pending.new_value, admin_id)
    _pending_changes.pop(admin_id, None)
    await query.answer("Payment setting updated")
    await _show_setting(query, key)


async def cancel_setting_change(query, key: str) -> None:
    """Discard one pending payment destination change."""
    if not requires_setting_confirmation(key):
        await query.answer("Unknown payment setting.", show_alert=True)
        return
    admin_id = query.from_user.id
    pending = _get_pending(admin_id, key)
    if pending is None:
        await query.answer("This confirmation expired.", show_alert=True)
    else:
        _pending_changes.pop(admin_id, None)
        await query.answer("Change cancelled")
    await _show_setting(query, key)


__all__ = [
    "SettingChangeRequest",
    "cancel_setting_change",
    "confirm_setting_change",
    "is_setting_confirmation_pending",
    "requires_setting_confirmation",
    "stage_setting_confirmation",
]
