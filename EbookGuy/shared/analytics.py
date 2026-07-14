"""Non-blocking event tracking and trending-search helpers."""

import asyncio
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
import logging

from pymongo.errors import PyMongoError

from database.users_chats_db import db


logger = logging.getLogger(__name__)
_analytics_tasks: set[asyncio.Task] = set()


@dataclass(frozen=True)
class SearchAnalyticsEvent:
    """Normalized data recorded for one user search."""

    user_id: int
    query: str
    result_count: int
    source: str


def _utc_now() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


async def _record_event(event: dict[str, object]) -> None:
    try:
        await db.record_analytics_event(event)
    except PyMongoError:
        logger.exception("Failed to record analytics event")


def track_event(
    event_name: str,
    user_id: int | None = None,
    **details: object,
) -> None:
    """Schedule one analytics write without delaying the user response."""
    event = {
        **details,
        "event": event_name,
        "user_id": int(user_id) if user_id is not None else None,
        "created_at": _utc_now(),
    }
    task = asyncio.create_task(_record_event(event))
    _analytics_tasks.add(task)
    task.add_done_callback(_analytics_tasks.discard)


def track_search(
    settings: dict[str, object],
    event: SearchAnalyticsEvent,
) -> None:
    """Record a normalized search when trending collection is enabled."""
    if not settings["trending_searches_enabled"]:
        return
    normalized_query = " ".join(event.query.casefold().split())
    if not normalized_query:
        return
    track_event(
        "search.executed",
        event.user_id,
        query=normalized_query,
        result_count=max(0, int(event.result_count)),
        source=event.source,
    )


def analytics_period_start(days: int | None) -> datetime | None:
    """Return the inclusive UTC start for a bounded analytics period."""
    if days is None:
        return None
    return _utc_now() - timedelta(days=days)


async def load_trending_searches(
    settings: dict[str, object],
) -> list[dict[str, object]]:
    """Load the configured public trending-search list."""
    if not settings["trending_searches_enabled"]:
        return []
    await db.ensure_analytics_indexes()
    start = analytics_period_start(int(settings["trending_period_days"]))
    return await db.get_trending_searches(
        start,
        int(settings["trending_results_limit"]),
    )


__all__ = [
    "analytics_period_start",
    "load_trending_searches",
    "SearchAnalyticsEvent",
    "track_event",
    "track_search",
]
