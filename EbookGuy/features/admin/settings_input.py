"""Validated administrator input flow for global settings."""

import asyncio
import logging
from dataclasses import dataclass

from pyrogram import filters
from pyrogram.errors import ListenerTimeout, RPCError
from pymongo.errors import PyMongoError

from EbookGuy.features.admin.settings_commands import build_setting_detail
from EbookGuy.shared.global_settings import (
    get_global_settings,
    save_global_setting,
)
from EbookGuy.shared.settings_catalog import SETTING_LABELS
from EbookGuy.shared.settings_schema import (
    is_boolean_setting,
    is_editable_setting,
    setting_input_hint,
    validate_setting_value,
)


logger = logging.getLogger(__name__)
INPUT_TIMEOUT_SECONDS = 120
CONFIRMATION_DISPLAY_SECONDS = 3
_active_admins: set[int] = set()
_input_tasks: set[asyncio.Task] = set()


@dataclass(frozen=True)
class SettingsInput:
    """Context needed to collect and apply one settings value."""

    admin_id: int
    chat_id: int
    message: object
    key: str


def is_settings_input_active(user_id: int) -> bool:
    """Return whether an administrator has an active settings prompt."""
    return user_id in _active_admins


def _input_prompt(context: SettingsInput) -> str:
    label = SETTING_LABELS[context.key]
    return (
        f"Send the new value for <b>{label}</b>.\n\n"
        f"{setting_input_hint(context.key)} Send /cancel to stop."
    )


async def _refresh_setting(context: SettingsInput) -> None:
    settings = await get_global_settings()
    text, markup = build_setting_detail(context.key, settings)
    await context.message.edit_text(text, reply_markup=markup)


async def _delete_messages(messages) -> None:
    for message in messages:
        try:
            await message.delete()
        except RPCError:
            logger.debug("Settings input message was already unavailable")


async def _delete_confirmation(message) -> None:
    await asyncio.sleep(CONFIRMATION_DISPLAY_SECONDS)
    await _delete_messages((message,))


async def _finish_input(prompt, reply, text: str) -> None:
    confirmation = await reply.reply_text(text)
    await _delete_messages((prompt, reply))
    _retain_input_task(_delete_confirmation(confirmation))


async def _apply_input(reply, prompt, context: SettingsInput) -> None:
    raw_value = (reply.text or "").strip()
    if raw_value.lower() == "/cancel":
        await _finish_input(prompt, reply, "Settings update cancelled.")
        return
    try:
        value = validate_setting_value(context.key, raw_value)
    except (KeyError, ValueError) as error:
        await reply.reply_text(str(error))
        return
    previous = await save_global_setting(
        context.key,
        value,
        context.admin_id,
    )
    await _refresh_setting(context)
    await _finish_input(
        prompt,
        reply,
        f"Updated <b>{SETTING_LABELS[context.key]}</b>: "
        f"<code>{previous}</code> -> <code>{value}</code>",
    )


async def _collect_input(client, context: SettingsInput) -> None:
    prompt = None
    try:
        prompt = await client.send_message(
            context.chat_id,
            _input_prompt(context),
        )
        reply = await client.listen(
            filters=filters.text & filters.user(context.admin_id),
            timeout=INPUT_TIMEOUT_SECONDS,
            chat_id=context.chat_id,
            user_id=context.admin_id,
        )
        await _apply_input(reply, prompt, context)
    except ListenerTimeout:
        if prompt is not None:
            await _delete_messages((prompt,))
        notice = await client.send_message(
            context.chat_id,
            "Settings update timed out. Open /settings to try again.",
        )
        _retain_input_task(_delete_confirmation(notice))
    except (PyMongoError, RPCError):
        logger.exception("Failed to collect global settings input")
    finally:
        _active_admins.discard(context.admin_id)


def _retain_input_task(coroutine) -> None:
    task = asyncio.create_task(coroutine)
    _input_tasks.add(task)
    task.add_done_callback(_input_tasks.discard)


async def start_setting_input(client, query, key: str) -> None:
    """Acknowledge and start one administrator settings prompt."""
    admin_id = query.from_user.id
    if not is_editable_setting(key):
        await query.answer("This setting is not editable yet.", show_alert=True)
        return
    if is_boolean_setting(key):
        await query.answer("Use the Enable or Disable button.", show_alert=True)
        return
    if admin_id in _active_admins:
        await query.answer(
            "Finish or cancel your current settings update.",
            show_alert=True,
        )
        return
    context = SettingsInput(
        admin_id=admin_id,
        chat_id=query.message.chat.id,
        message=query.message,
        key=key,
    )
    await query.answer("Send the new value in this chat.")
    _active_admins.add(admin_id)
    _retain_input_task(_collect_input(client, context))


__all__ = ["is_settings_input_active", "start_setting_input"]
