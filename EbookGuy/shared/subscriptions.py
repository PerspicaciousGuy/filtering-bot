"""Telegram channel subscription checks shared by user-facing features."""

import asyncio
import logging
import time
from collections import OrderedDict
from dataclasses import dataclass

from pyrogram import enums
from pyrogram.errors import RPCError, UserNotParticipant
from pymongo.errors import PyMongoError

from database.join_reqs import JoinReqs
from EbookGuy.shared.global_settings import get_global_settings
from info import AUTH_CHANNEL, REQUEST_TO_JOIN_MODE


logger = logging.getLogger(__name__)
join_db = JoinReqs()
MEMBERSHIP_CACHE_TTL_SECONDS = 60
MEMBERSHIP_CACHE_MAX_ENTRIES = 4096
_MEMBERSHIP_CACHE = OrderedDict()


@dataclass(frozen=True)
class SubscriptionRequirement:
    """One missing subscription and the link used to satisfy it."""

    channel: int | str
    title: str
    url: str | None


async def _legacy_join_request_exists(user_id: int, channel: int | str) -> bool:
    if not REQUEST_TO_JOIN_MODE or channel != AUTH_CHANNEL:
        return False
    if not join_db.isActive():
        return False
    try:
        user = await join_db.get_user(user_id)
    except PyMongoError:
        logger.exception("Failed to check force-subscription join request")
        return False
    return bool(user and user.get("user_id") == user_id)


async def _is_channel_member(bot, user_id: int, channel: int | str) -> bool:
    cache_key = (user_id, str(channel))
    expires_at = _MEMBERSHIP_CACHE.get(cache_key)
    if expires_at is not None:
        if expires_at > time.monotonic():
            _MEMBERSHIP_CACHE.move_to_end(cache_key)
            return True
        _MEMBERSHIP_CACHE.pop(cache_key, None)

    if await _legacy_join_request_exists(user_id, channel):
        _cache_membership(cache_key)
        return True
    try:
        member = await bot.get_chat_member(channel, user_id)
    except UserNotParticipant:
        return False
    except RPCError:
        logger.exception("Failed to check subscription for channel %s", channel)
        return False
    is_member = member.status != enums.ChatMemberStatus.BANNED
    if is_member:
        _cache_membership(cache_key)
    return is_member


def _cache_membership(cache_key):
    _MEMBERSHIP_CACHE[cache_key] = (
        time.monotonic() + MEMBERSHIP_CACHE_TTL_SECONDS
    )
    _MEMBERSHIP_CACHE.move_to_end(cache_key)
    while len(_MEMBERSHIP_CACHE) > MEMBERSHIP_CACHE_MAX_ENTRIES:
        _MEMBERSHIP_CACHE.popitem(last=False)


async def _join_url(bot, chat, channel: int | str) -> str | None:
    if chat.username:
        return f"https://t.me/{chat.username}"
    if chat.invite_link:
        return chat.invite_link
    try:
        invite = await bot.create_chat_invite_link(
            chat.id,
            creates_join_request=REQUEST_TO_JOIN_MODE,
        )
    except RPCError:
        logger.exception("Failed to create invite for channel %s", channel)
        return None
    return invite.invite_link


async def get_missing_subscriptions(
    bot,
    user,
    settings: dict[str, object] | None = None,
) -> list[SubscriptionRequirement]:
    """Return configured channels the supplied user has not joined."""
    current_settings = settings or await get_global_settings()
    if not current_settings["force_subscription_enabled"]:
        return []
    channels = list(current_settings["required_subscription_channels"])
    checks = await asyncio.gather(*[
        _missing_requirement(bot, int(user.id), channel)
        for channel in channels
    ])
    return [requirement for requirement in checks if requirement is not None]


async def _missing_requirement(bot, user_id: int, channel: int | str):
    if await _is_channel_member(bot, user_id, channel):
        return None
    try:
        chat = await bot.get_chat(channel)
    except RPCError:
        logger.exception("Failed to load subscription channel %s", channel)
        return SubscriptionRequirement(channel, str(channel), None)
    return SubscriptionRequirement(
        channel=channel,
        title=chat.title or str(channel),
        url=await _join_url(bot, chat, channel),
    )


async def is_subscribed(bot, query) -> bool:
    """Return whether a user satisfies every configured subscription."""
    try:
        return not await get_missing_subscriptions(bot, query.from_user)
    except PyMongoError:
        logger.exception("Failed to load force-subscription settings")
        return False


__all__ = [
    "SubscriptionRequirement",
    "get_missing_subscriptions",
    "is_subscribed",
]
