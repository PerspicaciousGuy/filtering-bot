"""Global bot settings catalog and environment-backed defaults."""

from string import Formatter
from urllib.parse import urlparse

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
    "downloads_enabled": {"kind": "boolean"},
    "protect_content": {"kind": "boolean"},
    "auto_delete_enabled": {"kind": "boolean"},
    "auto_delete_delay_seconds": {
        "kind": "integer",
        "minimum": 10,
        "maximum": 86400,
        "hint": "Allowed range: 10 to 86400 seconds.",
    },
    "custom_file_caption": {
        "kind": "caption_template",
        "maximum_length": 1000,
        "hint": (
            "Available fields: {file_name}, {file_size}, {file_caption}, "
            "{filename}, {filesize}, and {duration}."
        ),
    },
    "conversion_enabled": {"kind": "boolean"},
    "max_conversion_size_mb": {
        "kind": "integer",
        "minimum": 0,
        "maximum": 2000,
    },
    "requests_enabled": {"kind": "boolean"},
    "request_daily_limit": {
        "kind": "integer",
        "minimum": 0,
        "maximum": 1000,
    },
    "request_cooldown_seconds": {
        "kind": "integer",
        "minimum": 0,
        "maximum": 86400,
    },
    "allow_duplicate_requests": {"kind": "boolean"},
    "request_channel_id": {
        "kind": "chat_id",
        "hint": "Use 0 to send requests to bot admins, or a negative channel ID.",
    },
    "request_notifications_enabled": {"kind": "boolean"},
    "premium_purchases_enabled": {"kind": "boolean"},
    "stars_payments_enabled": {"kind": "boolean"},
    "premium_30_days_stars": {
        "kind": "integer",
        "minimum": 1,
        "maximum": 1000000,
    },
    "premium_90_days_stars": {
        "kind": "integer",
        "minimum": 1,
        "maximum": 1000000,
    },
    "premium_30_days_inr": {
        "kind": "integer",
        "minimum": 1,
        "maximum": 10000000,
    },
    "premium_90_days_inr": {
        "kind": "integer",
        "minimum": 1,
        "maximum": 10000000,
    },
    "premium_expiry_notifications_enabled": {"kind": "boolean"},
    "maintenance_mode": {"kind": "boolean"},
    "maintenance_message": {
        "kind": "text",
        "minimum_length": 1,
        "maximum_length": 1000,
        "hint": "Enter 1 to 1000 characters.",
    },
    "indexing_enabled": {"kind": "boolean"},
    "broadcasts_enabled": {"kind": "boolean"},
    "log_channel_id": {
        "kind": "chat_id",
        "hint": "Use 0 to disable operational logs, or a negative channel ID.",
    },
    "support_url": {
        "kind": "url",
        "maximum_length": 2048,
        "hint": "Enter a complete HTTPS URL.",
    },
}

CAPTION_TEMPLATE_FIELDS = {
    "file_name",
    "file_size",
    "file_caption",
    "filename",
    "filesize",
    "duration",
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


def _validate_boolean(raw_value: str, rule: dict[str, object]) -> bool:
    normalized = raw_value.strip().lower()
    if normalized in {"true", "on", "yes", "1"}:
        return True
    if normalized in {"false", "off", "no", "0"}:
        return False
    raise ValueError("Use on or off.")


def _validate_integer(raw_value: str, rule: dict[str, object]) -> int:
    try:
        value = int(raw_value.strip())
    except ValueError as error:
        raise ValueError("Enter a whole number.") from error
    minimum = int(rule["minimum"])
    maximum = int(rule["maximum"])
    if value < minimum or value > maximum:
        raise ValueError(f"Enter a value from {minimum} to {maximum}.")
    return value


def _validate_chat_id(raw_value: str, rule: dict[str, object]) -> int:
    try:
        value = int(raw_value.strip())
    except ValueError as error:
        raise ValueError("Enter a numeric Telegram chat ID.") from error
    if value > 0 or value < -999999999999999:
        raise ValueError("Use 0 or a negative Telegram chat ID.")
    return value


def _validate_text(raw_value: str, rule: dict[str, object]) -> str:
    value = raw_value.strip()
    minimum = int(rule.get("minimum_length", 0))
    maximum = int(rule["maximum_length"])
    if len(value) < minimum or len(value) > maximum:
        raise ValueError(f"Enter {minimum} to {maximum} characters.")
    return value


def _validate_caption_template(
    raw_value: str,
    rule: dict[str, object],
) -> str:
    value = _validate_text(raw_value, rule)
    try:
        fields = {
            field_name
            for _, field_name, _, _ in Formatter().parse(value)
            if field_name
        }
    except ValueError as error:
        raise ValueError("The caption template has invalid braces.") from error
    unknown_fields = fields - CAPTION_TEMPLATE_FIELDS
    if unknown_fields:
        unknown = ", ".join(sorted(unknown_fields))
        raise ValueError(f"Unknown caption field: {unknown}.")
    placeholders = {field: "sample" for field in CAPTION_TEMPLATE_FIELDS}
    try:
        value.format(**placeholders)
    except (IndexError, KeyError, TypeError, ValueError) as error:
        raise ValueError("The caption template cannot be formatted.") from error
    return value


def _validate_url(raw_value: str, rule: dict[str, object]) -> str:
    value = _validate_text(raw_value, rule)
    parsed = urlparse(value)
    if (
        parsed.scheme != "https"
        or not parsed.netloc
        or not parsed.hostname
        or any(character.isspace() for character in value)
    ):
        raise ValueError("Enter a complete HTTPS URL.")
    if parsed.username or parsed.password:
        raise ValueError("URLs with embedded credentials are not allowed.")
    return value


SETTING_VALIDATORS = {
    "boolean": _validate_boolean,
    "integer": _validate_integer,
    "chat_id": _validate_chat_id,
    "text": _validate_text,
    "caption_template": _validate_caption_template,
    "url": _validate_url,
}


def validate_setting_value(key: str, raw_value: str) -> object:
    """Validate and normalize one editable setting value."""
    if not is_editable_setting(key):
        raise KeyError(f"Setting is not editable: {key}")
    rule = SETTING_RULES[key]
    validator = SETTING_VALIDATORS[str(rule["kind"])]
    return validator(raw_value, rule)


def setting_input_hint(key: str) -> str:
    """Return the safe input range shown to an administrator."""
    rule = SETTING_RULES[key]
    if "hint" in rule:
        return str(rule["hint"])
    if rule["kind"] == "boolean":
        return "Use on or off."
    minimum = int(rule["minimum"])
    maximum = int(rule["maximum"])
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
