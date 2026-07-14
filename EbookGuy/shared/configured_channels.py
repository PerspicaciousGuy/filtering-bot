"""Runtime helpers for settings-backed Telegram channel lists."""

from pyrogram import filters

from EbookGuy.shared.global_settings import get_global_settings


def configured_channels(
    settings: dict[str, object],
    setting_key: str,
) -> tuple[int | str, ...]:
    """Return one channel setting as an immutable sequence."""
    value = settings[setting_key]
    if isinstance(value, (list, tuple)):
        return tuple(value)
    if value in {None, 0, ""}:
        return ()
    return (value,)


async def _matches_configured_channel(
    channel_filter: object,
    _client: object,
    message: object,
) -> bool:
    settings = await get_global_settings()
    channels = configured_channels(settings, channel_filter.setting_key)
    if message.chat.id in channels:
        return True
    username = getattr(message.chat, "username", None)
    if not username:
        return False
    normalized_username = username.casefold()
    return any(
        isinstance(channel, str)
        and channel.lstrip("@").casefold() == normalized_username
        for channel in channels
    )


def configured_channel_filter(setting_key: str) -> filters.Filter:
    """Create a Pyrogram filter backed by one channel-list setting."""
    return filters.create(
        _matches_configured_channel,
        name=f"ConfiguredChannel_{setting_key}",
        setting_key=setting_key,
    )


__all__ = ["configured_channel_filter", "configured_channels"]
