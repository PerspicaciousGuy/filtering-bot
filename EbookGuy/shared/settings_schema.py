"""Compatibility API for global bot setting definitions and validation."""

from EbookGuy.shared.settings_catalog import (
    CATEGORY_LABELS,
    CATEGORY_SETTINGS,
    EDITABLE_CATEGORIES,
    SETTING_DESCRIPTIONS,
    SETTING_LABELS,
)
from EbookGuy.shared.settings_defaults import DEFAULT_GLOBAL_SETTINGS
from EbookGuy.shared.settings_validation import (
    SETTING_RULES,
    setting_input_hint,
    validate_setting_value,
)


def is_known_setting(key: str) -> bool:
    """Return whether a key belongs to the global settings catalog."""
    return key in DEFAULT_GLOBAL_SETTINGS


def is_editable_setting(key: str) -> bool:
    """Return whether a setting is active in the editing dashboard."""
    return key in SETTING_RULES


def is_boolean_setting(key: str) -> bool:
    """Return whether a known setting uses a boolean value."""
    return is_known_setting(key) and isinstance(DEFAULT_GLOBAL_SETTINGS[key], bool)


def normalize_stored_setting(key: str, value: object) -> object:
    """Normalize a database value or fall back to its code default."""
    default = DEFAULT_GLOBAL_SETTINGS[key]
    if is_editable_setting(key):
        try:
            return validate_setting_value(key, value)
        except (TypeError, ValueError):
            return default
    if type(value) is type(default):
        return value
    return default


__all__ = [
    "CATEGORY_LABELS",
    "CATEGORY_SETTINGS",
    "DEFAULT_GLOBAL_SETTINGS",
    "EDITABLE_CATEGORIES",
    "SETTING_DESCRIPTIONS",
    "SETTING_LABELS",
    "SETTING_RULES",
    "is_editable_setting",
    "is_boolean_setting",
    "is_known_setting",
    "normalize_stored_setting",
    "setting_input_hint",
    "validate_setting_value",
]
