"""Versioned JSON serialization and validation for global settings backups."""

from dataclasses import dataclass
from datetime import datetime, timezone
import json

from EbookGuy.shared.settings_defaults import DEFAULT_GLOBAL_SETTINGS
from EbookGuy.shared.settings_validation import validate_setting_value


BACKUP_FORMAT = "filtering-bot-settings"
BACKUP_VERSION = 1
MAX_BACKUP_BYTES = 256 * 1024


@dataclass(frozen=True)
class ParsedSettingsBackup:
    """Validated settings and compatibility details from one backup file."""

    settings: dict[str, object]
    created_at: str
    unknown_keys: tuple[str, ...]
    missing_keys: tuple[str, ...]


def create_settings_backup(
    settings: dict[str, object],
    created_at: datetime | None = None,
) -> bytes:
    """Serialize effective global settings into the current backup format."""
    timestamp = created_at or datetime.now(timezone.utc)
    payload = {
        "format": BACKUP_FORMAT,
        "version": BACKUP_VERSION,
        "created_at": timestamp.isoformat().replace("+00:00", "Z"),
        "settings": {
            key: settings[key]
            for key in DEFAULT_GLOBAL_SETTINGS
        },
    }
    return json.dumps(
        payload,
        ensure_ascii=False,
        indent=2,
        sort_keys=True,
    ).encode("utf-8")


def _validate_created_at(value: object) -> str:
    if type(value) is not str:
        raise ValueError("Backup created_at must be a timestamp.")
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as error:
        raise ValueError("Backup created_at is not a valid timestamp.") from error
    if parsed.tzinfo is None:
        raise ValueError("Backup created_at must include a timezone.")
    return value


def _validate_json_type(key: str, value: object) -> None:
    expected = type(DEFAULT_GLOBAL_SETTINGS[key])
    if type(value) is not expected:
        raise ValueError(
            f"{key} must be stored as {expected.__name__} in the JSON backup."
        )


def parse_settings_backup(data: bytes) -> ParsedSettingsBackup:
    """Parse and strictly validate one versioned settings backup."""
    try:
        payload = json.loads(data.decode("utf-8-sig"))
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise ValueError("The uploaded file is not valid UTF-8 JSON.") from error
    if type(payload) is not dict:
        raise ValueError("The backup must contain one JSON object.")
    if payload.get("format") != BACKUP_FORMAT:
        raise ValueError("This is not a filtering-bot settings backup.")
    if type(payload.get("version")) is not int:
        raise ValueError("Backup version must be a number.")
    if payload["version"] != BACKUP_VERSION:
        raise ValueError(
            f"Backup version {payload['version']} is not supported."
        )
    created_at = _validate_created_at(payload.get("created_at"))
    raw_settings = payload.get("settings")
    if type(raw_settings) is not dict:
        raise ValueError("Backup settings must be a JSON object.")

    known_keys = set(DEFAULT_GLOBAL_SETTINGS)
    unknown_keys = tuple(sorted(set(raw_settings) - known_keys))
    missing_keys = tuple(sorted(known_keys - set(raw_settings)))
    settings = {}
    for key in DEFAULT_GLOBAL_SETTINGS:
        if key not in raw_settings:
            continue
        value = raw_settings[key]
        _validate_json_type(key, value)
        try:
            settings[key] = validate_setting_value(key, value)
        except (KeyError, TypeError, ValueError) as error:
            raise ValueError(f"Invalid value for {key}: {error}") from error

    return ParsedSettingsBackup(
        settings=settings,
        created_at=created_at,
        unknown_keys=unknown_keys,
        missing_keys=missing_keys,
    )


__all__ = [
    "BACKUP_FORMAT",
    "BACKUP_VERSION",
    "MAX_BACKUP_BYTES",
    "ParsedSettingsBackup",
    "create_settings_backup",
    "parse_settings_backup",
]
