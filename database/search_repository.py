"""MongoDB query and pagination operations for user-facing file search."""

import asyncio
import re
import time
from collections import OrderedDict
from dataclasses import dataclass

from database.file_collections import active_file_collections
from info import USE_CAPTION_FILTER


SEARCH_CACHE_TTL_SECONDS = 15
SEARCH_CACHE_MAX_ENTRIES = 256
_SEARCH_CACHE = OrderedDict()


@dataclass(frozen=True)
class SearchRequest:
    """Validated inputs used to retrieve one page of search results."""

    query: str
    max_results: int = 10
    offset: int = 0
    format_type: str | None = None
    result_limit: int = 100
    use_caption_filter: bool = USE_CAPTION_FILTER

    @property
    def page_limit(self) -> int:
        """Return the page size remaining within the configured result cap."""
        remaining = max(0, self.result_limit - self.offset)
        return min(self.max_results, remaining)


def _compile_search_regex(query: str) -> re.Pattern | str:
    normalized_query = query.strip()
    if not normalized_query:
        raw_pattern = "."
    elif " " not in normalized_query:
        raw_pattern = (
            r"(\b|[\.\+\-_])"
            + normalized_query
            + r"(\b|[\.\+\-_])"
        )
    else:
        raw_pattern = normalized_query.replace(
            " ",
            r".*[\s\.\+\-_]",
        )
    try:
        return re.compile(raw_pattern, flags=re.IGNORECASE)
    except re.error:
        return normalized_query


def _build_search_filter(
    query: str,
    format_type: str | None,
    use_caption_filter: bool,
) -> dict[str, object]:
    name_regex = _compile_search_regex(query)
    text_filter = {"file_name": name_regex}
    if use_caption_filter:
        text_filter = {
            "$or": [
                {"file_name": name_regex},
                {"caption": name_regex},
            ]
        }
    audio_pattern = (
        r"\s(mp3|m4a|m4b|aac|ogg|flac|wav|wma|zip)(\s|$)"
    )
    audio_regex = re.compile(audio_pattern, flags=re.IGNORECASE)
    if format_type == "ebook":
        return {
            "$and": [
                text_filter,
                {"file_name": {"$not": audio_regex}},
            ]
        }
    if format_type == "audiobook":
        return {
            "$and": [
                text_filter,
                {"file_name": audio_regex},
            ]
        }
    return text_filter


async def _find_search_files(
    search_filter: dict[str, object],
    request: SearchRequest,
    collections,
    collection_counts=None,
) -> list[dict[str, object]]:
    page_limit = request.page_limit
    if page_limit == 0:
        return []
    if len(collections) == 1:
        cursor = (
            collections[0].find(search_filter)
            .sort("$natural", -1)
            .skip(request.offset)
            .limit(page_limit)
        )
        return await cursor.to_list(length=page_limit)

    primary, secondary = collections
    primary_count = collection_counts[0]
    files = []
    if request.offset < primary_count:
        primary_cursor = (
            primary.find(search_filter)
            .sort("$natural", -1)
            .skip(request.offset)
            .limit(page_limit)
        )
        files.extend(
            await primary_cursor.to_list(length=page_limit)
        )

    if len(files) < page_limit:
        remaining = page_limit - len(files)
        secondary_offset = max(0, request.offset - primary_count)
        secondary_cursor = (
            secondary.find(search_filter)
            .sort("$natural", -1)
            .skip(secondary_offset)
            .limit(remaining)
        )
        files.extend(await secondary_cursor.to_list(length=remaining))
    return files


def clear_search_cache():
    """Discard cached pages after the file index changes."""
    _SEARCH_CACHE.clear()


def _get_cached_result(request):
    cached = _SEARCH_CACHE.get(request)
    if cached is None:
        return None
    expires_at, files, next_offset, total_results = cached
    if expires_at <= time.monotonic():
        _SEARCH_CACHE.pop(request, None)
        return None
    _SEARCH_CACHE.move_to_end(request)
    return list(files), next_offset, total_results


def _cache_result(request, result):
    files, next_offset, total_results = result
    _SEARCH_CACHE[request] = (
        time.monotonic() + SEARCH_CACHE_TTL_SECONDS,
        tuple(files),
        next_offset,
        total_results,
    )
    _SEARCH_CACHE.move_to_end(request)
    while len(_SEARCH_CACHE) > SEARCH_CACHE_MAX_ENTRIES:
        _SEARCH_CACHE.popitem(last=False)


async def get_search_results(
    request: SearchRequest,
) -> tuple[list[dict[str, object]], int | str, int]:
    """Return matching files, the next offset, and total result count."""
    cached = _get_cached_result(request)
    if cached is not None:
        return cached

    search_filter = _build_search_filter(
        request.query,
        request.format_type,
        request.use_caption_filter,
    )
    collections = active_file_collections()
    if len(collections) == 1:
        files, total_results = await asyncio.gather(
            _find_search_files(search_filter, request, collections),
            collections[0].count_documents(search_filter),
        )
    else:
        collection_counts = await asyncio.gather(*(
            collection.count_documents(search_filter)
            for collection in collections
        ))
        files = await _find_search_files(
            search_filter,
            request,
            collections,
            collection_counts,
        )
        total_results = sum(collection_counts)
    total_results = min(total_results, request.result_limit)
    consumed = request.offset + request.page_limit
    next_offset = "" if consumed >= total_results else consumed
    result = files, next_offset, total_results
    _cache_result(request, result)
    return result


__all__ = [
    "SearchRequest",
    "clear_search_cache",
    "get_search_results",
]
