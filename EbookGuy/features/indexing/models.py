from dataclasses import dataclass


@dataclass(frozen=True)
class IndexRequest:
    last_message_id: int
    chat_id: int | str
    status_message: object
    bot: object
    should_resume: bool = False


@dataclass
class IndexState:
    current_message: int
    start_from: int
    stats: dict
    last_update: float
