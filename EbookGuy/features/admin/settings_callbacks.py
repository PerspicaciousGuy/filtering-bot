"""Callback navigation for the global settings dashboard."""

import asyncio
import logging

from pymongo.errors import PyMongoError
from pyrogram.errors import MessageNotModified, RPCError

from EbookGuy.features.admin.analytics import show_analytics
from EbookGuy.features.admin.settings_actions import (
    reset_download_limits,
    show_download_reset_confirmation,
)
from EbookGuy.features.admin.settings_backup import (
    download_settings_backup,
    show_settings_backup,
)
from EbookGuy.features.admin.settings_restore import (
    cancel_settings_restore,
    confirm_settings_restore,
    start_settings_restore,
)
from EbookGuy.features.admin.settings_commands import (
    build_category_view,
    build_setting_detail,
    build_settings_dashboard,
)
from EbookGuy.features.admin.settings_confirmation import (
    SettingChangeRequest,
    cancel_setting_change,
    confirm_setting_change,
    requires_setting_confirmation,
    stage_setting_confirmation,
)
from EbookGuy.features.admin.settings_input import start_setting_input
from EbookGuy.features.admin.settings_runtime_validation import (
    validate_runtime_setting,
)
from EbookGuy.shared.global_settings import (
    get_global_settings,
    reset_global_setting,
    save_global_setting,
)
from EbookGuy.shared.settings_catalog import CATEGORY_LABELS
from EbookGuy.shared.settings_schema import (
    DEFAULT_GLOBAL_SETTINGS,
    is_boolean_setting,
    is_editable_setting,
    is_known_setting,
)
from info import ADMINS

logger = logging.getLogger(__name__)
ACCESS_DENIED_MESSAGE = "Only bot admins can use these settings."


def _is_bot_admin(user) -> bool:
    identifiers = {str(admin).lower() for admin in ADMINS}
    user_id = str(getattr(user, "id", ""))
    username = str(getattr(user, "username", "")).lower()
    return user_id in identifiers or username in identifiers


async def _show_category(query, category: str) -> None:
    if category not in CATEGORY_LABELS:
        await query.answer("Unknown settings category.", show_alert=True)
        return
    text, markup = build_category_view(category)
    await asyncio.gather(
        query.answer(),
        query.message.edit_text(text, reply_markup=markup),
    )


async def _show_setting(query, key: str) -> None:
    if not is_known_setting(key):
        await query.answer("Unknown setting.", show_alert=True)
        return
    await query.answer()
    settings = await get_global_settings()
    text, markup = build_setting_detail(key, settings)
    await query.message.edit_text(text, reply_markup=markup)


async def _set_boolean_value(client, query, payload: str) -> None:
    if ":" not in payload:
        await query.answer("Unknown setting value.", show_alert=True)
        return
    key, raw_value = payload.rsplit(":", 1)
    if not is_editable_setting(key) or not is_boolean_setting(key):
        await query.answer("This setting is not editable yet.", show_alert=True)
        return
    if raw_value not in {"0", "1"}:
        await query.answer("Unknown setting value.", show_alert=True)
        return
    value = raw_value == "1"
    try:
        await validate_runtime_setting(client, key, value)
    except ValueError as error:
        await query.answer(str(error), show_alert=True)
        return
    await query.answer()
    settings = await get_global_settings()
    await save_global_setting(key, value, query.from_user.id)
    settings[key] = value
    text, markup = build_setting_detail(key, settings)
    await query.message.edit_text(text, reply_markup=markup)


async def _reset_setting(query, key: str) -> None:
    if not is_editable_setting(key) or is_boolean_setting(key):
        await query.answer("This setting cannot be reset here.", show_alert=True)
        return
    if requires_setting_confirmation(key):
        settings = await get_global_settings()
        await query.answer("Review the payment setting change.")
        await stage_setting_confirmation(
            SettingChangeRequest(
                admin_id=query.from_user.id,
                key=key,
                previous_value=settings[key],
                new_value=DEFAULT_GLOBAL_SETTINGS[key],
                message=query.message,
                is_reset=True,
            )
        )
        return
    await query.answer()
    await reset_global_setting(key, query.from_user.id)
    settings = await get_global_settings()
    text, markup = build_setting_detail(key, settings)
    await query.message.edit_text(text, reply_markup=markup)


async def _route_settings_callback(client, query) -> None:
    data = query.data
    if data.startswith("global_settings:category:"):
        await _show_category(query, data.rsplit(":", 1)[-1])
    elif data.startswith("global_settings:setting:"):
        await _show_setting(query, data.rsplit(":", 1)[-1])
    elif data.startswith("global_settings:value:"):
        payload = data.removeprefix("global_settings:value:")
        await _set_boolean_value(client, query, payload)
    elif data.startswith("global_settings:reset:"):
        await _reset_setting(query, data.rsplit(":", 1)[-1])
    elif data.startswith("global_settings:edit:"):
        await start_setting_input(client, query, data.rsplit(":", 1)[-1])
    elif data.startswith("global_settings:payment_change:confirm:"):
        key = data.rsplit(":", 1)[-1]
        await confirm_setting_change(client, query, key)
    elif data.startswith("global_settings:payment_change:cancel:"):
        key = data.rsplit(":", 1)[-1]
        await cancel_setting_change(query, key)
    elif data == "global_settings:action:reset_downloads":
        await show_download_reset_confirmation(query)
    elif data == "global_settings:confirm:reset_downloads":
        await reset_download_limits(query)
    elif data.startswith("global_settings:analytics:"):
        payload = data.removeprefix("global_settings:analytics:")
        parts = payload.split(":")
        if len(parts) != 2:
            await query.answer("Unknown analytics view.", show_alert=True)
        else:
            await show_analytics(query, parts[0], parts[1])
    elif data == "global_settings:backup:home":
        await show_settings_backup(query)
    elif data == "global_settings:backup:download":
        await download_settings_backup(query)
    elif data == "global_settings:backup:restore":
        await start_settings_restore(client, query)
    elif data == "global_settings:backup:confirm":
        await confirm_settings_restore(query)
    elif data == "global_settings:backup:cancel":
        await cancel_settings_restore(query)
    elif data == "global_settings:home":
        text, markup = build_settings_dashboard()
        await asyncio.gather(
            query.answer(),
            query.message.edit_text(text, reply_markup=markup),
        )
    elif data == "global_settings:close":
        await query.answer()
        await query.message.delete()
    else:
        await query.answer("Unknown settings action.", show_alert=True)


async def handle_settings_callback(client, query) -> None:
    """Handle an admin settings navigation callback."""
    if not _is_bot_admin(query.from_user):
        await query.answer(ACCESS_DENIED_MESSAGE, show_alert=True)
        return

    try:
        await _route_settings_callback(client, query)
    except PyMongoError:
        logger.exception("Failed to update global settings")
        try:
            await query.answer("Settings are temporarily unavailable.", show_alert=True)
        except RPCError:
            logger.exception("Failed to send the global settings database error")
    except MessageNotModified:
        logger.debug("Global settings view is already current")
    except RPCError:
        logger.exception("Failed to navigate global settings")


__all__ = ["handle_settings_callback"]
