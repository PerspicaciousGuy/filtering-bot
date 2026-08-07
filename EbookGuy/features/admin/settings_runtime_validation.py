"""Runtime validation for settings that depend on Telegram state."""

from pyrogram import enums
from pyrogram.errors import RPCError

from EbookGuy.shared.global_settings import get_global_settings


CHANNEL_SETTINGS = {
    "delete_channel_ids",
    "file_channel_ids",
    "index_request_channel_id",
    "log_channel_id",
    "request_channel_id",
    "required_subscription_channels",
    "support_chat_id",
}
PAYMENT_SETTINGS = {
    "upi_payments_enabled",
    "upi_id",
    "upi_payee_name",
    "binance_payments_enabled",
    "binance_pay_id",
    "binance_pay_url_30",
    "binance_pay_url_90",
    "binance_30_days_usd_cents",
    "binance_90_days_usd_cents",
}


async def _validate_configured_channels(
    client: object,
    channels: list[int | str],
) -> None:
    bot = await client.get_me()
    for channel in channels:
        try:
            chat = await client.get_chat(channel)
            member = await client.get_chat_member(chat.id, bot.id)
        except RPCError as error:
            raise ValueError(
                f"The bot cannot access configured channel {channel}."
            ) from error
        if chat.type not in {
            enums.ChatType.CHANNEL,
            enums.ChatType.SUPERGROUP,
        }:
            raise ValueError(f"Target {channel} is not a channel or supergroup.")
        if member.status not in {
            enums.ChatMemberStatus.ADMINISTRATOR,
            enums.ChatMemberStatus.OWNER,
        }:
            raise ValueError(
                f"Make the bot an administrator in {chat.title}."
            )


def _setting_channels(value: object) -> list[int | str]:
    if isinstance(value, list):
        return value
    return [] if value == 0 else [int(value)]


async def _validate_source_channel_overlap(
    key: str,
    channels: list[int | str],
) -> None:
    other_keys = {
        "file_channel_ids": "delete_channel_ids",
        "delete_channel_ids": "file_channel_ids",
    }
    if key not in other_keys:
        return
    settings = await get_global_settings()
    other_channels = _setting_channels(settings[other_keys[key]])
    overlap = set(channels).intersection(other_channels)
    if overlap:
        channel = next(iter(overlap))
        raise ValueError(
            f"Channel {channel} cannot index and delete files at the same time."
        )


async def validate_runtime_setting(
    client: object,
    key: str,
    value: object,
) -> None:
    """Validate a setting that requires live Telegram information."""
    if key in CHANNEL_SETTINGS:
        channels = _setting_channels(value)
        await _validate_source_channel_overlap(key, channels)
        await _validate_configured_channels(client, channels)
    if key in PAYMENT_SETTINGS:
        settings = await get_global_settings()
        settings[key] = value
        _validate_manual_payment_settings(settings)


def _validate_manual_payment_settings(settings: dict[str, object]) -> None:
    if settings["upi_payments_enabled"]:
        if not settings["upi_id"] or not settings["upi_payee_name"]:
            raise ValueError(
                "Configure the UPI ID and payee name before enabling UPI."
            )
    if settings["binance_payments_enabled"]:
        if not settings["binance_pay_url_30"] or not settings["binance_pay_url_90"]:
            raise ValueError(
                "Configure both Binance plan URLs before enabling Binance Pay."
            )


async def validate_runtime_settings(
    client: object,
    settings: dict[str, object],
    changed_keys: set[str],
) -> None:
    """Validate restored channel settings against their combined final state."""
    changed_channel_keys = CHANNEL_SETTINGS.intersection(changed_keys)
    if not changed_channel_keys:
        channels = []
    else:
        file_channels = _setting_channels(settings["file_channel_ids"])
        delete_channels = _setting_channels(settings["delete_channel_ids"])
        overlap = set(file_channels).intersection(delete_channels)
        if overlap:
            channel = next(iter(overlap))
            raise ValueError(
                f"Channel {channel} cannot index and delete files at the same time."
            )
        channels = []
        for key in changed_channel_keys:
            for channel in _setting_channels(settings[key]):
                if channel not in channels:
                    channels.append(channel)
    if channels:
        await _validate_configured_channels(client, channels)
    if PAYMENT_SETTINGS.intersection(changed_keys):
        _validate_manual_payment_settings(settings)


__all__ = ["validate_runtime_setting", "validate_runtime_settings"]
