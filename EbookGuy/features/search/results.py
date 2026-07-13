import re

from database.search_repository import SearchRequest, get_search_results
from EbookGuy.features.search.models import AutoFilterRequest, SearchOutcome
from EbookGuy.features.search.page_navigation import handle_next_page
from EbookGuy.features.search.rendering import show_no_results, show_search_results
from EbookGuy.shared.global_settings import get_global_settings


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


def _search_request(search, format_type, settings):
    return SearchRequest(
        search,
        max_results=int(settings["results_per_page"]),
        format_type=format_type,
        result_limit=int(settings["max_search_results"]),
        use_caption_filter=bool(settings["use_caption_filter"]),
    )


async def _search_with_fallback(search, format_type, settings):
    files, offset, total = await get_search_results(
        _search_request(search, format_type, settings)
    )
    if not files and settings["search_suggestions_enabled"]:
        words = search.split()
        for drop_count in range(1, len(words) - 1):
            shorter = " ".join(words[:-drop_count])
            if len(shorter) < 3:
                break
            files, offset, total = await get_search_results(
                _search_request(shorter, format_type, settings)
            )
            if files:
                search = shorter
                break
    return SearchOutcome(
        files=files,
        next_offset=offset,
        total_results=total,
        search=search,
        settings=settings,
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
    settings = await get_global_settings()
    if not settings["search_enabled"]:
        await request.reply_message.edit_text(
            "<b>Search is temporarily disabled.</b>"
        )
        return
    search = _normalize_search(request.name)
    outcome = await _search_with_fallback(
        search,
        request.format_type,
        settings,
    )
    if not outcome.files:
        await show_no_results(request, settings)
        return
    await show_search_results(request, outcome)


__all__ = ["AutoFilterRequest", "auto_filter", "handle_next_page"]
