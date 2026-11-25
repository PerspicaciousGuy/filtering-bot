"""Animated message effects for Premium payment confirmations."""

import logging

from pyrogram import raw
from pyrogram.errors import RPCError

logger = logging.getLogger(__name__)

CELEBRATION_EMOTICON = "\U0001f389"
_effect_cache: dict[str, int] = {}


def _pick_effect(effects, emoticon: str) -> int | None:
    for effect in effects:
        if effect.emoticon == emoticon and not effect.premium_required:
            return effect.id
    return None


async def get_celebration_effect_id(client) -> int | None:
    """Return the free party-popper effect ID, or None if unavailable."""
    if CELEBRATION_EMOTICON in _effect_cache:
        return _effect_cache[CELEBRATION_EMOTICON]
    try:
        result = await client.invoke(
            raw.functions.messages.GetAvailableEffects(hash=0)
        )
    except RPCError:
        logger.info("Message effects are unavailable", exc_info=True)
        return None
    effect_id = _pick_effect(getattr(result, "effects", []), CELEBRATION_EMOTICON)
    if effect_id is not None:
        _effect_cache[CELEBRATION_EMOTICON] = effect_id
    return effect_id


async def reply_with_celebration(client, message, text: str) -> None:
    """Reply with a celebration effect, or plainly if Telegram refuses it."""
    effect_id = await get_celebration_effect_id(client)
    if effect_id is not None:
        try:
            await message.reply_text(text, message_effect_id=effect_id)
            return
        except RPCError:
            logger.info("Telegram rejected the message effect", exc_info=True)
    await message.reply_text(text)


__all__ = ["get_celebration_effect_id", "reply_with_celebration"]
