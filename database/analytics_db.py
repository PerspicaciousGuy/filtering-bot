"""MongoDB persistence and aggregation for bot analytics events."""

import asyncio


class AnalyticsMixin:
    """Store lightweight events and produce bounded analytics summaries."""

    _analytics_indexes_ready = False
    _analytics_indexes_lock = asyncio.Lock()

    async def ensure_analytics_indexes(self) -> None:
        """Create analytics indexes once per process."""
        if self._analytics_indexes_ready:
            return
        async with self._analytics_indexes_lock:
            if self._analytics_indexes_ready:
                return
            await self.analytics_events.create_index(
                [("event", 1), ("created_at", -1)]
            )
            await self.analytics_events.create_index(
                [("event", 1), ("query", 1), ("created_at", -1)]
            )
            await self.analytics_events.create_index(
                [("user_id", 1), ("created_at", -1)]
            )
            self._analytics_indexes_ready = True

    async def record_analytics_event(self, event: dict[str, object]) -> None:
        """Persist one already-normalized analytics event."""
        await self.analytics_events.insert_one(event)

    @staticmethod
    def _analytics_match(start) -> dict[str, object]:
        if start is None:
            return {}
        return {"created_at": {"$gte": start}}

    async def get_analytics_event_counts(self, start) -> dict[str, int]:
        """Return event counts for a reporting period."""
        pipeline = [
            {"$match": self._analytics_match(start)},
            {"$group": {"_id": "$event", "count": {"$sum": 1}}},
        ]
        rows = await self.analytics_events.aggregate(pipeline).to_list(None)
        return {str(row["_id"]): int(row["count"]) for row in rows}

    async def get_analytics_active_users(self, start) -> int:
        """Return distinct users represented in a reporting period."""
        query = self._analytics_match(start)
        query["user_id"] = {"$ne": None}
        user_ids = await self.analytics_events.distinct("user_id", query)
        return len(user_ids)

    async def get_trending_searches(
        self,
        start,
        limit: int,
    ) -> list[dict[str, object]]:
        """Return the most frequently recorded normalized search queries."""
        match = self._analytics_match(start)
        match.update({"event": "search.executed", "query": {"$ne": ""}})
        pipeline = [
            {"$match": match},
            {
                "$group": {
                    "_id": "$query",
                    "count": {"$sum": 1},
                    "last_searched_at": {"$max": "$created_at"},
                }
            },
            {"$sort": {"count": -1, "last_searched_at": -1, "_id": 1}},
            {"$limit": int(limit)},
        ]
        rows = await self.analytics_events.aggregate(pipeline).to_list(limit)
        return [
            {
                "query": str(row["_id"]),
                "count": int(row["count"]),
                "last_searched_at": row["last_searched_at"],
            }
            for row in rows
        ]

    async def get_payment_analytics(self, start) -> dict[str, int]:
        """Return successful Telegram Stars payment totals."""
        match = self._analytics_match(start)
        match["event"] = "payment.completed"
        pipeline = [
            {"$match": match},
            {
                "$group": {
                    "_id": None,
                    "payments": {"$sum": 1},
                    "stars": {"$sum": {"$ifNull": ["$stars", 0]}},
                }
            },
        ]
        rows = await self.analytics_events.aggregate(pipeline).to_list(1)
        if not rows:
            return {"payments": 0, "stars": 0}
        return {
            "payments": int(rows[0]["payments"]),
            "stars": int(rows[0]["stars"]),
        }


__all__ = ["AnalyticsMixin"]
