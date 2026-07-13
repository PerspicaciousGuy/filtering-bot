import re

from database.ia_filterdb import SearchRequest, get_search_results
from EbookGuy.features.search.models import AutoFilterRequest, SearchOutcome
from EbookGuy.features.search.page_navigation import handle_next_page
from EbookGuy.features.search.rendering import show_no_results, show_search_results
from utils import get_settings


IGNORED_SEARCH_WORDS = {
    "in", "upload", "full", "horror", "thriller", "mystery", "print", "file",
}
IGNORED_MESSAGE_PATTERN = re.compile(
    r"(^/|^,|^!|^\.|^[\U0001F600-\U000E007F]).*"
)
REQUEST_WORD_PATTERN = re.compile(
    r"\b(pl(i|e)*?(s|z+|ease|se|ese|(e+)s(e)?)|"
    r"((send|snd|giv(e)?|gib)(\sme)?)|new|latest|bro|bruh|"
    r"broh|helo|that|find|link|any(one)|with\ssubtitle(s)?)",
    flags=re.IGNORECASE,
)


def _normalize_search(name):
    words = (
        word for word in name.lower().split()
        if word not in IGNORED_SEARCH_WORDS
    )
    search = " ".join(words)
    search = REQUEST_WORD_PATTERN.sub("", search)
    search = re.sub(r"\s+", " ", search).strip()
    return search.replace("-", " ").replace(":", "").replace(".", "")


async def _search_with_fallback(message, search, format_type):
    files, offset, total = await get_search_results(
        SearchRequest(search, format_type=format_type)
    )
    if not files:
        words = search.split()
        for drop_count in range(1, len(words) - 1):
            shorter = " ".join(words[:-drop_count])
            if len(shorter) < 3:
                break
            files, offset, total = await get_search_results(
                SearchRequest(shorter, format_type=format_type)
            )
            if files:
                search = shorter
                break
    return SearchOutcome(
        files=files,
        next_offset=offset,
        total_results=total,
        search=search,
        settings=await get_settings(message.chat.id),
    )


async def auto_filter(request):
    """Search and render results for one normalized request."""
    text = request.message.text
    if (
        text.startswith("/")
        or IGNORED_MESSAGE_PATTERN.match(text)
        or len(text) >= 100
    ):
        return
    search = _normalize_search(request.name)
    outcome = await _search_with_fallback(
        request.message, search, request.format_type
    )
    if not outcome.files:
        await show_no_results(request)
        return
    await show_search_results(request, outcome)


__all__ = ["AutoFilterRequest", "auto_filter", "handle_next_page"]
