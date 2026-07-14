"""MongoDB persistence for request limits and duplicate detection."""

import asyncio
from dataclasses import dataclass
from bson import ObjectId


@dataclass(frozen=True)
class RequestStatusUpdate:
    """Persistence values for one request status transition."""

    request_id: str
    status: str
    admin_id: int
    changed_at: object


class RequestRecordsMixin:
    """Store and query submitted book requests."""

    _request_indexes_ready = False
    _request_indexes_lock = asyncio.Lock()

    async def ensure_request_indexes(self) -> None:
        """Create indexes used by request policy checks once per process."""
        if self._request_indexes_ready:
            return
        async with self._request_indexes_lock:
            if self._request_indexes_ready:
                return
            await self.book_requests.create_index(
                [("user_id", 1), ("request_date", 1)]
            )
            await self.book_requests.create_index(
                [("user_id", 1), ("submitted_at", -1)]
            )
            await self.book_requests.create_index("normalized_content")
            await self.book_requests.create_index(
                [("status", 1), ("submitted_at", -1)]
            )
            self._request_indexes_ready = True

    async def get_daily_request_count(
        self,
        user_id: int,
        request_date: str,
    ) -> int:
        """Return one user's submitted request count for a UTC date."""
        return await self.book_requests.count_documents(
            {"user_id": int(user_id), "request_date": request_date}
        )

    async def get_last_request(self, user_id: int) -> dict | None:
        """Return the user's most recent submitted request."""
        return await self.book_requests.find_one(
            {"user_id": int(user_id)},
            sort=[("submitted_at", -1)],
        )

    async def request_exists(self, normalized_content: str) -> bool:
        """Return whether a normalized title has already been submitted."""
        request = await self.book_requests.find_one(
            {"normalized_content": normalized_content},
            {"_id": 1},
        )
        return request is not None

    async def record_request(self, request: dict[str, object]) -> None:
        """Persist a successfully forwarded book request."""
        await self.book_requests.insert_one(request)

    async def get_request_record(self, request_id: str) -> dict | None:
        """Return one request by its public hexadecimal identifier."""
        try:
            object_id = ObjectId(request_id)
        except (TypeError, ValueError):
            return None
        return await self.book_requests.find_one({"_id": object_id})

    async def update_request_status(
        self,
        update: RequestStatusUpdate,
    ) -> bool:
        """Persist one administrator request-status transition."""
        try:
            object_id = ObjectId(update.request_id)
        except (TypeError, ValueError):
            return False
        result = await self.book_requests.update_one(
            {"_id": object_id},
            {
                "$set": {
                    "status": update.status,
                    "status_changed_by": int(update.admin_id),
                    "status_changed_at": update.changed_at,
                }
            },
        )
        return result.matched_count == 1

    async def get_request_status_counts(self, start) -> dict[str, int]:
        """Return persisted request counts grouped by current status."""
        match = {} if start is None else {"submitted_at": {"$gte": start}}
        pipeline = [
            {"$match": match},
            {
                "$group": {
                    "_id": {"$ifNull": ["$status", "pending"]},
                    "count": {"$sum": 1},
                }
            },
        ]
        rows = await self.book_requests.aggregate(pipeline).to_list(None)
        return {str(row["_id"]): int(row["count"]) for row in rows}


__all__ = ["RequestRecordsMixin", "RequestStatusUpdate"]
