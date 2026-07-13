from dataclasses import dataclass


@dataclass(frozen=True)
class AutoFilterRequest:
    name: str
    message: object
    reply_message: object
    format_type: str | None = None


@dataclass(frozen=True)
class SearchOutcome:
    files: list
    next_offset: int | str
    total_results: int
    search: str
    settings: dict


@dataclass(frozen=True)
class NextPageView:
    files: list
    search: str
    prefix: str
    buttons: list


@dataclass(frozen=True)
class PageRequest:
    requester_id: str
    key: str
    offset: int
    search: str
    format_type: str | None
