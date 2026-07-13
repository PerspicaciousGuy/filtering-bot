"""Callback navigation for the global settings dashboard."""

import logging

from pyrogram.errors import RPCError
from pymongo.errors import PyMongoError

from info import ADMINS
from EbookGuy.features.admin.settings_commands import (
    build_category_view,
    build_setting_detail,
    build_settings_dashboard,
)
from EbookGuy.features.admin.settings_input import start_setting_input
from EbookGuy.shared.global_settings import (
    get_global_settings,
    reset_global_setting,
    save_global_setting,
)
from EbookGuy.shared.settings_catalog import CATEGORY_LABELS, SETTING_LABELS
from EbookGuy.shared.settings_schema import (
    is_boolean_setting,
    is_editable_setting,
    is_known_setting,
)


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
    await query.answer()
    text, markup = build_category_view(category)
    await query.message.edit_text(text, reply_markup=markup)


async def _show_setting(query, key: str) -> None:
    if not is_known_setting(key):
        await query.answer("Unknown setting.", show_alert=True)
        return
    settings = await get_global_settings()
    text, markup = build_setting_detail(key, settings)
    await query.answer()
    await query.message.edit_text(text, reply_markup=markup)


async def _set_boolean_value(query, payload: str) -> None:
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
    settings = await get_global_settings()
    await save_global_setting(key, value, query.from_user.id)
    settings[key] = value
    text, markup = build_setting_detail(key, settings)
    state = "Enabled" if value else "Disabled"
    await query.answer(f"{SETTING_LABELS[key]}: {state}")
    await query.message.edit_text(text, reply_markup=markup)


async def _reset_setting(query, key: str) -> None:
    if not is_editable_setting(key) or is_boolean_setting(key):
        await query.answer("This setting cannot be reset here.", show_alert=True)
        return
    previous, default = await reset_global_setting(key, query.from_user.id)
    settings = await get_global_settings()
    text, markup = build_setting_detail(key, settings)
    notice = "Already using the default" if previous == default else "Default restored"
    await query.answer(notice)
    await query.message.edit_text(text, reply_markup=markup)


async def _route_settings_callback(client, query) -> None:
    data = query.data
    if data.startswith("global_settings:category:"):
        await _show_category(query, data.rsplit(":", 1)[-1])
    elif data.startswith("global_settings:setting:"):
        await _show_setting(query, data.rsplit(":", 1)[-1])
    elif data.startswith("global_settings:value:"):
        payload = data.removeprefix("global_settings:value:")
        await _set_boolean_value(query, payload)
    elif data.startswith("global_settings:reset:"):
        await _reset_setting(query, data.rsplit(":", 1)[-1])
    elif data.startswith("global_settings:edit:"):
        await start_setting_input(client, query, data.rsplit(":", 1)[-1])
    elif data == "global_settings:home":
        await query.answer()
        text, markup = build_settings_dashboard()
        await query.message.edit_text(text, reply_markup=markup)
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
    except RPCError:
        logger.exception("Failed to navigate global settings")


__all__ = ["handle_settings_callback"]
