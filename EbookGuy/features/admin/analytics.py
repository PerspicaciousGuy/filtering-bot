"""Administrator analytics views embedded in the settings dashboard."""

import asyncio
from datetime import datetime, timezone
from html import escape

from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from database.users_chats_db import db
from EbookGuy.shared.analytics import analytics_period_start


CALLBACK_PREFIX = "global_settings:analytics"
ANALYTICS_PERIODS = {
    "today": (1, "Today"),
    "7d": (7, "7 Days"),
    "30d": (30, "30 Days"),
    "all": (None, "All Time"),
}
ANALYTICS_VIEWS = {
    "overview": "Overview",
    "users": "Users",
    "searches": "Searches",
    "downloads": "Downloads",
    "requests": "Requests",
    "conversions": "Conversions",
    "premium": "Premium",
    "payments": "Payments",
}


async def _load_snapshot(period: str) -> dict[str, object]:
    days = ANALYTICS_PERIODS[period][0]
    if period == "today":
        now = datetime.now(timezone.utc).replace(tzinfo=None)
        start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    else:
        start = analytics_period_start(days)
    await db.ensure_analytics_indexes()
    (
        event_counts,
        active_users,
        total_users,
        premium_users,
        request_statuses,
        payment_totals,
        trending,
    ) = await asyncio.gather(
        db.get_analytics_event_counts(start),
        db.get_analytics_active_users(start),
        db.total_users_count(),
        db.get_premium_stats(),
        db.get_request_status_counts(start),
        db.get_payment_analytics(start),
        db.get_trending_searches(start, 5),
    )
    return {
        "events": event_counts,
        "active_users": active_users,
        "total_users": total_users,
        "premium_users": premium_users,
        "request_statuses": request_statuses,
        "payments": payment_totals,
        "trending": trending,
    }


def _metric(label: str, value: object) -> str:
    return f"<b>{label}:</b> <code>{value}</code>"


def _request_count(requests: dict[str, int], *statuses: str) -> int:
    return sum(requests.get(status, 0) for status in statuses)


def _overview_lines(snapshot: dict[str, object]) -> list[str]:
    events = snapshot["events"]
    return [
        _metric("Total users", snapshot["total_users"]),
        _metric("Active users", snapshot["active_users"]),
        _metric("New users", events.get("user.registered", 0)),
        _metric("Searches", events.get("search.executed", 0)),
        _metric("Downloads", events.get("download.completed", 0)),
        _metric("Conversions", events.get("conversion.completed", 0)),
        _metric("Requests", events.get("request.submitted", 0)),
        _metric("Stars payments", snapshot["payments"]["payments"]),
    ]


def _request_lines(
    events: dict[str, int],
    requests: dict[str, int],
) -> list[str]:
    return [
        _metric("Submitted", events.get("request.submitted", 0)),
        _metric("Pending", requests.get("pending", 0)),
        _metric(
            "Processing",
            _request_count(requests, "processing", "accepted"),
        ),
        _metric(
            "Unavailable",
            _request_count(requests, "unavailable", "rejected"),
        ),
        _metric(
            "Uploaded",
            _request_count(requests, "uploaded", "completed"),
        ),
        _metric("Already Available", requests.get("already_available", 0)),
    ]


def _view_lines(view: str, snapshot: dict[str, object]) -> list[str]:
    events = snapshot["events"]
    requests = snapshot["request_statuses"]
    if view == "users":
        return [
            _metric("Total users", snapshot["total_users"]),
            _metric("Active users", snapshot["active_users"]),
            _metric("New users", events.get("user.registered", 0)),
            _metric("Active Premium users", snapshot["premium_users"]),
        ]
    if view == "searches":
        lines = [_metric("Searches", events.get("search.executed", 0)), ""]
        lines.append("<b>Top searches</b>")
        for index, row in enumerate(snapshot["trending"], start=1):
            lines.append(
                f"{index}. <code>{escape(str(row['query']))}</code> "
                f"({row['count']})"
            )
        if not snapshot["trending"]:
            lines.append("No search events recorded.")
        return lines
    if view == "downloads":
        return [
            _metric("Completed", events.get("download.completed", 0)),
            _metric("Denied", events.get("download.denied", 0)),
        ]
    if view == "requests":
        return _request_lines(events, requests)
    if view == "conversions":
        return [
            _metric("Completed", events.get("conversion.completed", 0)),
            _metric("Failed", events.get("conversion.failed", 0)),
        ]
    if view == "premium":
        return [
            _metric("Active Premium users", snapshot["premium_users"]),
            _metric("Stars activations", events.get("payment.completed", 0)),
        ]
    if view == "payments":
        return [
            _metric("Successful Stars payments", snapshot["payments"]["payments"]),
            _metric("Stars received", snapshot["payments"]["stars"]),
        ]
    return _overview_lines(snapshot)


def _analytics_markup(view: str, period: str) -> InlineKeyboardMarkup:
    period_buttons = [
        InlineKeyboardButton(
            (f"* {label}" if key == period else label),
            callback_data=f"{CALLBACK_PREFIX}:{view}:{key}",
        )
        for key, (_, label) in ANALYTICS_PERIODS.items()
    ]
    view_buttons = [
        InlineKeyboardButton(
            (f"* {label}" if key == view else label),
            callback_data=f"{CALLBACK_PREFIX}:{key}:{period}",
        )
        for key, label in ANALYTICS_VIEWS.items()
    ]
    rows = [period_buttons]
    rows.extend(
        [view_buttons[index:index + 2] for index in range(0, len(view_buttons), 2)]
    )
    rows.append(
        [InlineKeyboardButton("Back", callback_data="global_settings:home")]
    )
    return InlineKeyboardMarkup(rows)


async def show_analytics(query, view: str, period: str) -> None:
    """Load and render one administrator analytics page."""
    if view not in ANALYTICS_VIEWS or period not in ANALYTICS_PERIODS:
        await query.answer("Unknown analytics view.", show_alert=True)
        return
    snapshot = await _load_snapshot(period)
    period_label = ANALYTICS_PERIODS[period][1]
    title = ANALYTICS_VIEWS[view]
    lines = [f"<b>Analytics - {title}</b>", f"Period: {period_label}", ""]
    lines.extend(_view_lines(view, snapshot))
    await query.answer()
    await query.message.edit_text(
        "\n".join(lines),
        reply_markup=_analytics_markup(view, period),
    )


__all__ = ["show_analytics"]
