"""Direct Telegram Bot API calls for features Pyrofork does not expose yet."""

from aiohttp import ClientError, ClientSession, ClientTimeout

from info import BOT_TOKEN

BOT_API_TIMEOUT_SECONDS = 10


class BotApiError(RuntimeError):
    """Raised when a Bot API request fails or Telegram rejects it."""


async def call_bot_api(method: str, payload: dict[str, object]) -> object:
    """Call one Bot API method and return its result."""
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/{method}"
    timeout = ClientTimeout(total=BOT_API_TIMEOUT_SECONDS)
    try:
        async with ClientSession(timeout=timeout) as session:
            async with session.post(url, json=payload) as response:
                result = await response.json(content_type=None)
    except (ClientError, TimeoutError, TypeError, ValueError):
        raise BotApiError(f"Bot API request {method} failed") from None
    if not isinstance(result, dict) or not result.get("ok"):
        description = (
            result.get("description", "unknown error")
            if isinstance(result, dict)
            else "invalid response"
        )
        raise BotApiError(f"Bot API rejected {method}: {description}")
    return result.get("result")


def inline_button_payload(button) -> dict[str, object] | None:
    """Convert a Pyrogram URL or callback button to Bot API JSON."""
    if button.callback_data is not None:
        return {"text": button.text, "callback_data": button.callback_data}
    if button.url is not None:
        return {"text": button.text, "url": button.url}
    return None


def disabled_button_payload(text: str) -> dict[str, object]:
    """Return a Bot API button that is shown as disabled and does nothing."""
    return {"text": text, "disabled": {}}


__all__ = [
    "BotApiError",
    "call_bot_api",
    "disabled_button_payload",
    "inline_button_payload",
]
