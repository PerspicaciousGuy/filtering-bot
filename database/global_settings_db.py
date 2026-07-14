"""MongoDB persistence for global bot settings."""

from EbookGuy.shared.settings_schema import (
    DEFAULT_GLOBAL_SETTINGS,
    is_known_setting,
    normalize_stored_setting,
)
from EbookGuy.shared.settings_defaults import LEGACY_GLOBAL_SETTING_ALIASES


GLOBAL_SETTINGS_ID = "bot"


def _legacy_setting_values(stored: dict[str, object]) -> dict[str, object]:
    values = {}
    for key, legacy_key in LEGACY_GLOBAL_SETTING_ALIASES.items():
        if key not in stored and legacy_key in stored:
            values[key] = normalize_stored_setting(key, stored[legacy_key])
    return values


class GlobalSettingsMixin:
    """Store one global settings document for the bot."""

    async def get_global_settings(self) -> dict[str, object]:
        """Return stored global values merged with current defaults."""
        document = await self.global_settings.find_one(
            {"_id": GLOBAL_SETTINGS_ID},
            {"_id": 0, "values": 1},
        )
        stored = document.get("values", {}) if document else {}
        known_values = {
            key: normalize_stored_setting(key, value)
            for key, value in stored.items()
            if is_known_setting(key)
        }
        legacy_values = _legacy_setting_values(stored)
        return {**DEFAULT_GLOBAL_SETTINGS, **legacy_values, **known_values}

    async def update_global_setting(self, key: str, value: object) -> None:
        """Persist one known global setting."""
        if not is_known_setting(key):
            raise KeyError(f"Unknown global setting: {key}")
        await self.global_settings.update_one(
            {"_id": GLOBAL_SETTINGS_ID},
            {"$set": {f"values.{key}": value}},
            upsert=True,
        )

    async def reset_global_setting(self, key: str) -> None:
        """Remove one stored override so its configured default applies."""
        if not is_known_setting(key):
            raise KeyError(f"Unknown global setting: {key}")
        unset_values = {f"values.{key}": ""}
        legacy_key = LEGACY_GLOBAL_SETTING_ALIASES.get(key)
        if legacy_key:
            unset_values[f"values.{legacy_key}"] = ""
        await self.global_settings.update_one(
            {"_id": GLOBAL_SETTINGS_ID},
            {"$unset": unset_values},
        )

    async def record_global_setting_change(self, entry: dict[str, object]) -> None:
        """Append one administrator settings change to the audit collection."""
        await self.global_settings_audit.insert_one(entry)


__all__ = ["GlobalSettingsMixin"]
