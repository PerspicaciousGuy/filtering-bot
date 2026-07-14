"""Public command rendering for recent trending searches."""

from html import escape

from pymongo.errors import PyMongoError

from EbookGuy.features.downloads.force_subscription import enforce_subscription
from EbookGuy.shared.analytics import load_trending_searches
from EbookGuy.shared.global_settings import get_global_settings


async def handle_trending_command(client, message) -> None:
    """Show configured trending searches to a regular private-chat user."""
    if await enforce_subscription(client, message):
        return
    settings = await get_global_settings()
    if not settings["trending_searches_enabled"]:
        await message.reply_text("Trending searches are currently disabled.")
        return
    try:
        rows = await load_trending_searches(settings)
    except PyMongoError:
        await message.reply_text("Trending searches are temporarily unavailable.")
        return
    if not rows:
        await message.reply_text("No trending searches are available yet.")
        return
    period_days = int(settings["trending_period_days"])
    lines = [f"<b>Trending Searches - Last {period_days} Days</b>", ""]
    for position, row in enumerate(rows, start=1):
        count = int(row["count"])
        lines.append(
            f"<b>{position}.</b> <code>{escape(str(row['query']))}</code> "
            f"- {count} search{'es' if count != 1 else ''}"
        )
    await message.reply_text("\n".join(lines))


__all__ = ["handle_trending_command"]
