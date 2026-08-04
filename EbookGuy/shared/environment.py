"""Environment loading and validation helpers."""

from collections.abc import Iterable
from os import environ

from dotenv import load_dotenv


class ConfigurationError(RuntimeError):
    """Raised when required runtime configuration is missing or invalid."""


def load_and_validate_environment(required_names: Iterable[str]) -> None:
    """Load local values and reject missing production configuration."""
    load_dotenv()
    missing = [
        name
        for name in required_names
        if not str(environ.get(name, "")).strip()
    ]
    if missing:
        names = ", ".join(sorted(missing))
        raise ConfigurationError(
            f"Missing required environment variables: {names}"
        )


def required_int_environment(name: str) -> int:
    """Return one required integer environment value."""
    raw_value = str(environ[name]).strip()
    try:
        return int(raw_value)
    except ValueError as error:
        raise ConfigurationError(
            f"Environment variable {name} must be an integer"
        ) from error


def parse_identifiers(raw_value: str) -> list[int | str]:
    """Parse space-separated Telegram IDs or usernames."""
    identifiers: list[int | str] = []
    for token in raw_value.split():
        value = token.strip()
        if not value:
            continue
        identifiers.append(
            int(value) if value.lstrip("-").isdigit() else value
        )
    return identifiers


def parse_optional_identifier(raw_value: str) -> int | str | None:
    """Parse one optional Telegram ID or username."""
    identifiers = parse_identifiers(raw_value)
    return identifiers[0] if identifiers else None


__all__ = [
    "ConfigurationError",
    "load_and_validate_environment",
    "parse_identifiers",
    "parse_optional_identifier",
    "required_int_environment",
]
