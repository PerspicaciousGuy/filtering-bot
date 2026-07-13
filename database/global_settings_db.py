"""MongoDB persistence for global bot settings."""

from EbookGuy.shared.settings_schema import (
    DEFAULT_GLOBAL_SETTINGS,
    is_known_setting,
    normalize_stored_setting,
)


GLOBAL_SETTINGS_ID = "bot"


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
        return {**DEFAULT_GLOBAL_SETTINGS, **known_values}

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
        await self.global_settings.update_one(
            {"_id": GLOBAL_SETTINGS_ID},
            {"$unset": {f"values.{key}": ""}},
        )

    async def record_global_setting_change(self, entry: dict[str, object]) -> None:
        """Append one administrator settings change to the audit collection."""
        await self.global_settings_audit.insert_one(entry)


__all__ = ["GlobalSettingsMixin"]
