"""MongoDB query and pagination operations for user-facing file search."""

import re
from dataclasses import dataclass

from database.file_collections import col, sec_col
from info import MULTIPLE_DATABASE, USE_CAPTION_FILTER


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
) -> list[dict[str, object]]:
    page_limit = request.page_limit
    if page_limit == 0:
        return []
    if not MULTIPLE_DATABASE:
        cursor = (
            col.find(search_filter)
            .sort("$natural", -1)
            .skip(request.offset)
            .limit(page_limit)
        )
        return await cursor.to_list(length=page_limit)

    primary_count = await col.count_documents(search_filter)
    files = []
    if request.offset < primary_count:
        primary_cursor = (
            col.find(search_filter)
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
            sec_col.find(search_filter)
            .sort("$natural", -1)
            .skip(secondary_offset)
            .limit(remaining)
        )
        files.extend(await secondary_cursor.to_list(length=remaining))
    return files


async def get_search_results(
    request: SearchRequest,
) -> tuple[list[dict[str, object]], int | str, int]:
    """Return matching files, the next offset, and total result count."""
    search_filter = _build_search_filter(
        request.query,
        request.format_type,
        request.use_caption_filter,
    )
    files = await _find_search_files(search_filter, request)
    total_results = await col.count_documents(search_filter)
    if MULTIPLE_DATABASE:
        total_results += await sec_col.count_documents(search_filter)
    total_results = min(total_results, request.result_limit)
    consumed = request.offset + request.page_limit
    next_offset = "" if consumed >= total_results else consumed
    return files, next_offset, total_results


__all__ = ["SearchRequest", "get_search_results"]
