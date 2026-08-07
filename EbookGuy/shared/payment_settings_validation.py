"""Validation for administrator-configured manual payment destinations."""

import re
from urllib.parse import urlparse


UPI_ID_PATTERN = re.compile(
    r"^[A-Za-z0-9][A-Za-z0-9._-]{1,99}@[A-Za-z][A-Za-z0-9.-]{1,63}$"
)


def _optional_value(raw_value: object) -> str:
    value = str(raw_value).strip()
    return "" if value.casefold() in {"", "0", "none", "off"} else value


def validate_upi_id(raw_value: object, rule: dict[str, object]) -> str:
    """Validate an optional UPI virtual payment address."""
    value = _optional_value(raw_value)
    if value and not UPI_ID_PATTERN.fullmatch(value):
        raise ValueError("Enter a valid UPI ID such as name@bank.")
    return value


def validate_optional_text(
    raw_value: object,
    rule: dict[str, object],
) -> str:
    """Validate optional bounded payment display text."""
    value = _optional_value(raw_value)
    maximum = int(rule["maximum_length"])
    if len(value) > maximum:
        raise ValueError(f"Enter no more than {maximum} characters.")
    return value


def validate_optional_digits(
    raw_value: object,
    rule: dict[str, object],
) -> str:
    """Validate an optional numeric payment identifier."""
    value = _optional_value(raw_value)
    maximum = int(rule["maximum_length"])
    if value and (not value.isdecimal() or len(value) > maximum):
        raise ValueError("Enter a valid numeric payment ID.")
    return value


def validate_binance_url(
    raw_value: object,
    rule: dict[str, object],
) -> str:
    """Validate an optional HTTPS URL hosted by Binance."""
    value = _optional_value(raw_value)
    if not value:
        return ""
    if len(value) > 2048 or any(character.isspace() for character in value):
        raise ValueError("Enter a complete HTTPS Binance URL.")
    parsed = urlparse(value)
    hostname = parsed.hostname or ""
    if parsed.scheme != "https" or not parsed.netloc or parsed.username:
        raise ValueError("Enter a complete HTTPS Binance URL.")
    if parsed.password:
        raise ValueError("URLs with embedded credentials are not allowed.")
    if hostname != "binance.com" and not hostname.endswith(".binance.com"):
        raise ValueError("Enter an HTTPS URL hosted by binance.com.")
    return value


__all__ = [
    "validate_binance_url",
    "validate_optional_digits",
    "validate_optional_text",
    "validate_upi_id",
]
