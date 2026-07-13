"""Global bot settings catalog and environment-backed defaults."""

from info import (
    AUTO_DELETE,
    CACHE_TIME,
    CUSTOM_FILE_CAPTION,
    FREE_DAILY_LIMIT,
    LOG_CHANNEL,
    PM_SEARCH,
    PREMIUM_DAILY_LIMIT,
    PREMIUM_DOWNLOAD_COOLDOWN,
    PREMIUM_PRICES,
    PREMIUM_PRICES_INR,
    PROTECT_CONTENT,
    REQST_CHANNEL,
    SUPPORT_CHAT,
    USE_CAPTION_FILTER,
)
from EbookGuy.shared.settings_catalog import (
    CATEGORY_LABELS,
    CATEGORY_SETTINGS,
    EDITABLE_CATEGORIES,
    SETTING_DESCRIPTIONS,
    SETTING_LABELS,
)

SETTING_RULES = {
    "free_daily_limit": {"kind": "integer", "minimum": 0, "maximum": 1000},
    "premium_daily_limit": {"kind": "integer", "minimum": 0, "maximum": 10000},
    "premium_download_cooldown_seconds": {
        "kind": "integer",
        "minimum": 0,
        "maximum": 86400,
    },
    "free_max_file_size_mb": {
        "kind": "integer",
        "minimum": 0,
        "maximum": 2000,
    },
    "premium_max_file_size_mb": {
        "kind": "integer",
        "minimum": 0,
        "maximum": 2000,
    },
    "premium_daily_conversion_limit": {
        "kind": "integer",
        "minimum": 0,
        "maximum": 1000,
    },
    "search_enabled": {"kind": "boolean"},
    "results_per_page": {
        "kind": "integer",
        "minimum": 1,
        "maximum": 20,
    },
    "max_search_results": {
        "kind": "integer",
        "minimum": 20,
        "maximum": 1000,
    },
    "search_suggestions_enabled": {"kind": "boolean"},
    "search_result_expiry_seconds": {
        "kind": "integer",
        "minimum": 30,
        "maximum": 86400,
    },
    "use_caption_filter": {"kind": "boolean"},
}

DEFAULT_GLOBAL_SETTINGS = {
    "free_daily_limit": FREE_DAILY_LIMIT,
    "premium_daily_limit": PREMIUM_DAILY_LIMIT,
    "premium_download_cooldown_seconds": PREMIUM_DOWNLOAD_COOLDOWN,
    "free_max_file_size_mb": 0,
    "premium_max_file_size_mb": 0,
    "premium_daily_conversion_limit": 3,
    "search_enabled": PM_SEARCH,
    "results_per_page": 10,
    "max_search_results": 100,
    "search_suggestions_enabled": True,
    "search_result_expiry_seconds": CACHE_TIME,
    "use_caption_filter": USE_CAPTION_FILTER,
    "downloads_enabled": True,
    "protect_content": PROTECT_CONTENT,
    "auto_delete_enabled": AUTO_DELETE,
    "auto_delete_delay_seconds": 600,
    "custom_file_caption": CUSTOM_FILE_CAPTION,
    "conversion_enabled": True,
    "max_conversion_size_mb": 0,
    "requests_enabled": True,
    "request_daily_limit": 0,
    "request_cooldown_seconds": 0,
    "allow_duplicate_requests": True,
    "request_channel_id": REQST_CHANNEL or 0,
    "request_notifications_enabled": True,
    "premium_purchases_enabled": True,
    "stars_payments_enabled": True,
    "premium_30_days_stars": PREMIUM_PRICES[30],
    "premium_90_days_stars": PREMIUM_PRICES[90],
    "premium_30_days_inr": PREMIUM_PRICES_INR[30],
    "premium_90_days_inr": PREMIUM_PRICES_INR[90],
    "premium_expiry_notifications_enabled": True,
    "maintenance_mode": False,
    "maintenance_message": "The bot is temporarily unavailable.",
    "indexing_enabled": True,
    "broadcasts_enabled": True,
    "log_channel_id": LOG_CHANNEL,
    "support_url": f"https://t.me/{SUPPORT_CHAT}",
}


def is_known_setting(key: str) -> bool:
    """Return whether a key belongs to the global settings catalog."""
    return key in DEFAULT_GLOBAL_SETTINGS


def is_editable_setting(key: str) -> bool:
    """Return whether a setting is active in the editing dashboard."""
    return key in SETTING_RULES


def validate_setting_value(key: str, raw_value: str) -> object:
    """Validate and normalize one editable setting value."""
    if not is_editable_setting(key):
        raise KeyError(f"Setting is not editable: {key}")
    rule = SETTING_RULES[key]
    if rule["kind"] == "boolean":
        normalized = raw_value.strip().lower()
        if normalized in {"true", "on", "yes", "1"}:
            return True
        if normalized in {"false", "off", "no", "0"}:
            return False
        raise ValueError("Use on or off.")
    try:
        value = int(raw_value.strip())
    except ValueError as error:
        raise ValueError("Enter a whole number.") from error
    if value < rule["minimum"] or value > rule["maximum"]:
        raise ValueError(
            f"Enter a value from {rule['minimum']} to {rule['maximum']}."
        )
    return value


def setting_input_hint(key: str) -> str:
    """Return the safe input range shown to an administrator."""
    rule = SETTING_RULES[key]
    if rule["kind"] == "boolean":
        return "Use on or off."
    minimum = rule["minimum"]
    maximum = rule["maximum"]
    if minimum == 0:
        return f"Use 0 for unlimited. Allowed range: 0 to {maximum}."
    return f"Allowed range: {minimum} to {maximum}."


def is_boolean_setting(key: str) -> bool:
    """Return whether a known setting uses a boolean value."""
    return is_known_setting(key) and isinstance(DEFAULT_GLOBAL_SETTINGS[key], bool)


def normalize_stored_setting(key: str, value: object) -> object:
    """Normalize a database value or fall back to its code default."""
    default = DEFAULT_GLOBAL_SETTINGS[key]
    if is_editable_setting(key):
        try:
            return validate_setting_value(key, str(value))
        except ValueError:
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
