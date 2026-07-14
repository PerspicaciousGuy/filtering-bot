"""MongoDB persistence for request limits and duplicate detection."""

import asyncio


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


__all__ = ["RequestRecordsMixin"]
