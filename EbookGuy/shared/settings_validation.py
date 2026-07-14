"""Rules and validators for administrator-editable global settings."""

from html.parser import HTMLParser
import re
from string import Formatter
from urllib.parse import urlparse


CAPTION_TEMPLATE_FIELDS = {
    "file_name",
    "file_size",
    "file_caption",
    "filename",
    "filesize",
    "duration",
}
REQUEST_TEMPLATE_FIELDS = {
    "user_name",
    "book_title",
    "author_name",
    "request_id",
    "reason",
    "download_link",
}
WELCOME_TEMPLATE_FIELDS = {
    "first_name",
    "username",
    "mention",
    "bot_name",
    "library_count",
    "free_limit",
    "support_url",
}
TELEGRAM_HTML_TAGS = {
    "a",
    "b",
    "blockquote",
    "code",
    "del",
    "em",
    "i",
    "ins",
    "pre",
    "s",
    "spoiler",
    "strike",
    "strong",
    "tg-spoiler",
    "u",
}
CHANNEL_USERNAME_PATTERN = re.compile(r"^@[A-Za-z][A-Za-z0-9_]{4,31}$")

SETTING_RULES = {
    "free_daily_limit": {"kind": "integer", "minimum": 0, "maximum": 1000},
    "premium_daily_limit": {"kind": "integer", "minimum": 0, "maximum": 10000},
    "premium_download_cooldown_seconds": {
        "kind": "integer", "minimum": 0, "maximum": 86400,
    },
    "free_max_file_size_mb": {
        "kind": "integer", "minimum": 0, "maximum": 2000,
    },
    "premium_max_file_size_mb": {
        "kind": "integer", "minimum": 0, "maximum": 2000,
    },
    "premium_daily_conversion_limit": {
        "kind": "integer", "minimum": 0, "maximum": 1000,
    },
    "file_channel_ids": {
        "kind": "chat_id_list",
        "maximum_items": 10,
        "hint": (
            "Send up to 10 negative channel IDs or @usernames, separated by "
            "spaces, commas, or new lines. Send 0 to clear the list."
        ),
    },
    "delete_channel_ids": {
        "kind": "chat_id_list",
        "maximum_items": 10,
        "hint": (
            "Send up to 10 negative channel IDs or @usernames, separated by "
            "spaces, commas, or new lines. Send 0 to clear the list."
        ),
    },
    "index_request_channel_id": {
        "kind": "chat_id",
        "hint": (
            "Use 0 to fall back to the log channel, or a negative channel ID."
        ),
    },
    "support_chat_id": {
        "kind": "chat_id",
        "hint": "Use 0 to disable the fallback, or a negative chat ID.",
    },
    "force_subscription_enabled": {"kind": "boolean"},
    "required_subscription_channels": {
        "kind": "chat_id_list",
        "maximum_items": 10,
        "hint": (
            "Send up to 10 negative channel IDs or @usernames, separated by "
            "spaces, commas, or new lines. Send 0 to clear the list."
        ),
    },
    "welcome_message_enabled": {"kind": "boolean"},
    "welcome_message_template": {
        "kind": "message_template",
        "maximum_length": 3500,
        "fields": WELCOME_TEMPLATE_FIELDS,
        "hint": (
            "Available fields: {first_name}, {username}, {mention}, "
            "{bot_name}, {library_count}, {free_limit}, and {support_url}."
        ),
    },
    "search_enabled": {"kind": "boolean"},
    "results_per_page": {"kind": "integer", "minimum": 1, "maximum": 20},
    "max_search_results": {"kind": "integer", "minimum": 20, "maximum": 1000},
    "search_suggestions_enabled": {"kind": "boolean"},
    "search_result_expiry_seconds": {
        "kind": "integer", "minimum": 30, "maximum": 86400,
    },
    "use_caption_filter": {"kind": "boolean"},
    "trending_searches_enabled": {"kind": "boolean"},
    "trending_period_days": {"kind": "integer", "minimum": 1, "maximum": 30},
    "trending_results_limit": {"kind": "integer", "minimum": 1, "maximum": 20},
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
        "kind": "integer", "minimum": 0, "maximum": 2000,
    },
    "requests_enabled": {"kind": "boolean"},
    "request_daily_limit": {"kind": "integer", "minimum": 0, "maximum": 1000},
    "request_cooldown_seconds": {
        "kind": "integer", "minimum": 0, "maximum": 86400,
    },
    "allow_duplicate_requests": {"kind": "boolean"},
    "request_channel_id": {
        "kind": "chat_id",
        "hint": "Use 0 to send requests to bot admins, or a negative channel ID.",
    },
    "request_notifications_enabled": {"kind": "boolean"},
    "request_author_required": {"kind": "boolean"},
    "request_processing_message": {
        "kind": "message_template",
        "maximum_length": 3500,
        "fields": REQUEST_TEMPLATE_FIELDS,
        "hint": (
            "Available fields: {user_name}, {book_title}, {author_name}, "
            "{request_id}, {reason}, and {download_link}."
        ),
    },
    "request_unavailable_message": {
        "kind": "message_template",
        "maximum_length": 3500,
        "fields": REQUEST_TEMPLATE_FIELDS,
        "hint": (
            "Available fields: {user_name}, {book_title}, {author_name}, "
            "{request_id}, {reason}, and {download_link}."
        ),
    },
    "request_uploaded_message": {
        "kind": "message_template",
        "maximum_length": 3500,
        "fields": REQUEST_TEMPLATE_FIELDS,
        "hint": (
            "Available fields: {user_name}, {book_title}, {author_name}, "
            "{request_id}, {reason}, and {download_link}."
        ),
    },
    "request_already_available_message": {
        "kind": "message_template",
        "maximum_length": 3500,
        "fields": REQUEST_TEMPLATE_FIELDS,
        "hint": (
            "Available fields: {user_name}, {book_title}, {author_name}, "
            "{request_id}, {reason}, and {download_link}."
        ),
    },
    "premium_purchases_enabled": {"kind": "boolean"},
    "stars_payments_enabled": {"kind": "boolean"},
    "premium_30_days_stars": {"kind": "integer", "minimum": 1, "maximum": 1000000},
    "premium_90_days_stars": {"kind": "integer", "minimum": 1, "maximum": 1000000},
    "premium_30_days_inr": {"kind": "integer", "minimum": 1, "maximum": 10000000},
    "premium_90_days_inr": {"kind": "integer", "minimum": 1, "maximum": 10000000},
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


class _TelegramHTMLValidator(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self._open_tags: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag not in TELEGRAM_HTML_TAGS:
            raise ValueError(f"Unsupported Telegram HTML tag: {tag}.")
        if tag != "a" and attrs:
            raise ValueError(f"HTML attributes are not allowed on {tag}.")
        if tag == "a":
            attribute_names = {name for name, _ in attrs}
            if attribute_names != {"href"}:
                raise ValueError("Links must contain only an href attribute.")
        self._open_tags.append(tag)

    def handle_endtag(self, tag: str) -> None:
        if not self._open_tags or self._open_tags.pop() != tag:
            raise ValueError("Telegram HTML tags are not correctly nested.")

    def ensure_closed(self) -> None:
        if self._open_tags:
            raise ValueError("Telegram HTML contains an unclosed tag.")


def _validate_boolean(raw_value: object, rule: dict[str, object]) -> bool:
    normalized = str(raw_value).strip().lower()
    if normalized in {"true", "on", "yes", "1"}:
        return True
    if normalized in {"false", "off", "no", "0"}:
        return False
    raise ValueError("Use on or off.")


def _validate_integer(raw_value: object, rule: dict[str, object]) -> int:
    try:
        value = int(str(raw_value).strip())
    except ValueError as error:
        raise ValueError("Enter a whole number.") from error
    minimum = int(rule["minimum"])
    maximum = int(rule["maximum"])
    if value < minimum or value > maximum:
        raise ValueError(f"Enter a value from {minimum} to {maximum}.")
    return value


def _validate_chat_id(raw_value: object, rule: dict[str, object]) -> int:
    try:
        value = int(str(raw_value).strip())
    except ValueError as error:
        raise ValueError("Enter a numeric Telegram chat ID.") from error
    if value > 0 or value < -999999999999999:
        raise ValueError("Use 0 or a negative Telegram chat ID.")
    return value


def _channel_tokens(raw_value: object) -> list[object]:
    if isinstance(raw_value, (list, tuple)):
        return list(raw_value)
    value = str(raw_value).strip()
    if not value or value.casefold() in {"0", "none", "off"}:
        return []
    return value.replace(",", " ").split()


def _validate_chat_id_list(
    raw_value: object,
    rule: dict[str, object],
) -> list[int | str]:
    channels: list[int | str] = []
    for token in _channel_tokens(raw_value):
        value = str(token).strip()
        if CHANNEL_USERNAME_PATTERN.fullmatch(value):
            channel: int | str = value
        else:
            try:
                channel = int(value)
            except ValueError as error:
                raise ValueError(f"Invalid channel identifier: {value}.") from error
            if channel >= 0 or channel < -999999999999999:
                raise ValueError(f"Channel IDs must be negative: {value}.")
        if channel not in channels:
            channels.append(channel)
    maximum_items = int(rule["maximum_items"])
    if len(channels) > maximum_items:
        raise ValueError(f"Enter no more than {maximum_items} channels.")
    return channels


def _validate_text(raw_value: object, rule: dict[str, object]) -> str:
    value = str(raw_value).strip()
    minimum = int(rule.get("minimum_length", 0))
    maximum = int(rule["maximum_length"])
    if len(value) < minimum or len(value) > maximum:
        raise ValueError(f"Enter {minimum} to {maximum} characters.")
    return value


def _template_fields(value: str) -> set[str]:
    try:
        return {
            field_name
            for _, field_name, _, _ in Formatter().parse(value)
            if field_name
        }
    except ValueError as error:
        raise ValueError("The template has invalid braces.") from error


def _format_template(value: str, allowed_fields: set[str]) -> None:
    placeholders = {field: "sample" for field in allowed_fields}
    try:
        value.format(**placeholders)
    except (IndexError, KeyError, TypeError, ValueError) as error:
        raise ValueError("The template cannot be formatted.") from error


def _validate_template(
    raw_value: object,
    rule: dict[str, object],
) -> str:
    value = _validate_text(raw_value, rule)
    allowed_fields = set(rule["fields"])
    unknown_fields = _template_fields(value) - allowed_fields
    if unknown_fields:
        unknown = ", ".join(sorted(unknown_fields))
        raise ValueError(f"Unknown template field: {unknown}.")
    _format_template(value, allowed_fields)
    return value


def _validate_caption_template(
    raw_value: object,
    rule: dict[str, object],
) -> str:
    caption_rule = {**rule, "fields": CAPTION_TEMPLATE_FIELDS}
    return _validate_template(raw_value, caption_rule)


def _validate_message_template(
    raw_value: object,
    rule: dict[str, object],
) -> str:
    value = _validate_template(raw_value, rule)
    parser = _TelegramHTMLValidator()
    try:
        parser.feed(value)
        parser.close()
        parser.ensure_closed()
    except ValueError:
        raise
    except Exception as error:
        raise ValueError("The Telegram HTML is invalid.") from error
    return value


def _validate_url(raw_value: object, rule: dict[str, object]) -> str:
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
    "chat_id_list": _validate_chat_id_list,
    "text": _validate_text,
    "caption_template": _validate_caption_template,
    "message_template": _validate_message_template,
    "url": _validate_url,
}


def validate_setting_value(key: str, raw_value: object) -> object:
    """Validate and normalize one editable setting value."""
    if key not in SETTING_RULES:
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


__all__ = [
    "SETTING_RULES",
    "setting_input_hint",
    "validate_setting_value",
]
