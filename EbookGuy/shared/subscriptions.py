"""Telegram channel subscription checks shared by user-facing features."""

import asyncio
from dataclasses import dataclass
import logging

from pyrogram import enums
from pyrogram.errors import RPCError, UserNotParticipant
from pyrogram.types import InlineKeyboardButton
from pymongo.errors import PyMongoError

from database.join_reqs import JoinReqs
from EbookGuy.shared.global_settings import get_global_settings
from info import AUTH_CHANNEL, REQUEST_TO_JOIN_MODE


logger = logging.getLogger(__name__)
join_db = JoinReqs


@dataclass(frozen=True)
class SubscriptionRequirement:
    """One missing subscription and the link used to satisfy it."""

    channel: int | str
    title: str
    url: str | None


async def pub_is_subscribed(bot, query, channel):
    btn = []
    for channel_id in channel:
        chat = await bot.get_chat(int(channel_id))
        try:
            await bot.get_chat_member(channel_id, query.from_user.id)
        except UserNotParticipant:
            btn.append(
                [InlineKeyboardButton(f"Join {chat.title}", url=chat.invite_link)]
            )
        except RPCError:
            logger.warning("Failed to check public-channel subscription", exc_info=True)
    return btn


async def _legacy_join_request_exists(user_id: int, channel: int | str) -> bool:
    if not REQUEST_TO_JOIN_MODE or channel != AUTH_CHANNEL:
        return False
    if not join_db().isActive():
        return False
    try:
        user = await join_db().get_user(user_id)
    except PyMongoError:
        logger.exception("Failed to check force-subscription join request")
        return False
    return bool(user and user.get("user_id") == user_id)


async def _is_channel_member(bot, user_id: int, channel: int | str) -> bool:
    if await _legacy_join_request_exists(user_id, channel):
        return True
    try:
        member = await bot.get_chat_member(channel, user_id)
    except UserNotParticipant:
        return False
    except RPCError:
        logger.exception("Failed to check subscription for channel %s", channel)
        return False
    return member.status != enums.ChatMemberStatus.BANNED


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
    "pub_is_subscribed",
]
