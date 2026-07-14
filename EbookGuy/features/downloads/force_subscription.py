"""User prompts for globally configured force-subscription channels."""

from dataclasses import dataclass

from pyrogram import enums
from pyrogram.errors import RPCError
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from pymongo.errors import PyMongoError

from Script import script
from EbookGuy.shared.subscriptions import get_missing_subscriptions
from utils import temp


@dataclass(frozen=True)
class SubscriptionPrompt:
    """Context used to render one force-subscription prompt."""

    message: object
    user: object
    payload: str


def _retry_button(payload: str) -> InlineKeyboardButton:
    try:
        prefix, file_id = payload.split("_", 1)
        return InlineKeyboardButton(
            script.TRY_AGAIN_BTN,
            callback_data=f"checksub#{prefix}#{file_id}",
        )
    except ValueError:
        return InlineKeyboardButton(
            script.TRY_AGAIN_BTN,
            url=f"https://t.me/{temp.U_NAME}?start={payload}",
        )


def _subscription_markup(requirements, payload: str) -> InlineKeyboardMarkup:
    buttons = [
        [InlineKeyboardButton(f"Join {item.title}", url=item.url)]
        for item in requirements
        if item.url
    ]
    if payload != "subscribe":
        buttons.append([_retry_button(payload)])
    return InlineKeyboardMarkup(buttons)


async def _send_subscription_prompt(
    client,
    prompt: SubscriptionPrompt,
) -> bool:
    missing = await get_missing_subscriptions(client, prompt.user)
    if not missing:
        return False
    if any(item.url is None for item in missing):
        await prompt.message.reply_text(script.FORCE_SUB_ADMIN_ERROR)
        return True
    await prompt.message.reply_text(
        "<b>Join all required channels to continue.</b>\n\n"
        "After joining, try the action again.",
        reply_markup=_subscription_markup(missing, prompt.payload),
        parse_mode=enums.ParseMode.HTML,
    )
    return True


def _start_payload(message) -> str:
    command = getattr(message, "command", None) or []
    return command[1] if len(command) > 1 else "subscribe"


async def enforce_subscription(client, message, payload: str | None = None) -> bool:
    """Prompt an unsubscribed private-message user and stop the current action."""
    try:
        return await _send_subscription_prompt(
            client,
            SubscriptionPrompt(
                message=message,
                user=message.from_user,
                payload=payload or _start_payload(message),
            ),
        )
    except (PyMongoError, RPCError):
        await message.reply_text(script.FORCE_SUB_ERROR)
        return True


async def enforce_callback_subscription(client, query) -> bool:
    """Prompt an unsubscribed callback user and acknowledge the callback."""
    try:
        was_blocked = await _send_subscription_prompt(
            client,
            SubscriptionPrompt(
                message=query.message,
                user=query.from_user,
                payload="subscribe",
            ),
        )
        if was_blocked:
            await query.answer()
        return was_blocked
    except (PyMongoError, RPCError):
        await query.answer(script.FORCE_SUB_ERROR, show_alert=True)
        return True


__all__ = ["enforce_callback_subscription", "enforce_subscription"]
