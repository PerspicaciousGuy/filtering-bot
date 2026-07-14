"""Application access helpers for global bot settings."""

import asyncio
from datetime import datetime, timezone
import logging
import time

from pymongo.errors import PyMongoError

from database.users_chats_db import db
from EbookGuy.shared.settings_schema import DEFAULT_GLOBAL_SETTINGS


logger = logging.getLogger(__name__)
GLOBAL_SETTINGS_CACHE_SECONDS = 15
_settings_cache: dict[str, object] | None = None
_settings_cache_expires_at = 0.0
_settings_cache_lock = asyncio.Lock()


def _cache_settings(settings: dict[str, object]) -> None:
    global _settings_cache, _settings_cache_expires_at
    _settings_cache = settings.copy()
    _settings_cache_expires_at = time.monotonic() + GLOBAL_SETTINGS_CACHE_SECONDS


async def get_global_settings() -> dict[str, object]:
    """Load the effective global bot settings."""
    if _settings_cache is not None and time.monotonic() < _settings_cache_expires_at:
        return _settings_cache.copy()
    async with _settings_cache_lock:
        is_cache_valid = (
            _settings_cache is not None
            and time.monotonic() < _settings_cache_expires_at
        )
        if is_cache_valid:
            return _settings_cache.copy()
        settings = await db.get_global_settings()
        _cache_settings(settings)
        return settings.copy()


def get_cached_global_setting(key: str) -> object:
    """Return a cached setting for synchronous formatting helpers."""
    if _settings_cache is None:
        return DEFAULT_GLOBAL_SETTINGS[key]
    return _settings_cache.get(key, DEFAULT_GLOBAL_SETTINGS[key])


async def save_global_setting(
    key: str,
    value: object,
    admin_id: int,
) -> object:
    """Persist and audit one validated global bot setting."""
    settings = await get_global_settings()
    previous_value = settings[key]
    if previous_value == value:
        return previous_value
    await db.update_global_setting(key, value)
    settings[key] = value
    _cache_settings(settings)
    await _record_setting_change(
        _change_record(key, admin_id, (previous_value, value))
    )
    return previous_value


def _change_record(
    key: str,
    admin_id: int,
    values: tuple[object, object],
) -> dict[str, object]:
    return {
        "setting": key,
        "previous_value": values[0],
        "new_value": values[1],
        "admin_id": admin_id,
        "changed_at": datetime.now(timezone.utc),
    }


async def _record_setting_change(entry: dict[str, object]) -> None:
    try:
        await db.record_global_setting_change(entry)
    except PyMongoError:
        logger.exception("Global setting changed but audit logging failed")


async def reset_global_setting(key: str, admin_id: int) -> tuple[object, object]:
    """Remove an override and return its previous and default values."""
    settings = await get_global_settings()
    previous_value = settings[key]
    default_value = DEFAULT_GLOBAL_SETTINGS[key]
    await db.reset_global_setting(key)
    settings[key] = default_value
    _cache_settings(settings)
    if previous_value != default_value:
        await _record_setting_change(
            _change_record(key, admin_id, (previous_value, default_value))
        )
    return previous_value, default_value


def describe_daily_limit(value: object) -> str:
    """Describe a configured daily download allowance."""
    limit = int(value)
    if limit == 0:
        return "Unlimited downloads"
    return f"Up to {limit} downloads per day"


__all__ = [
    "describe_daily_limit",
    "get_cached_global_setting",
    "get_global_settings",
    "reset_global_setting",
    "save_global_setting",
]
