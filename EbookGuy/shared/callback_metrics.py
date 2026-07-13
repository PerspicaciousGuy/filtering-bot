import logging
import re
import time
from functools import wraps


logger = logging.getLogger(__name__)
SLOW_CALLBACK_MS = 500


def _callback_prefix(query):
    data = getattr(query, "data", "") or ""
    action, separator, _ = data.partition("#")
    if separator:
        return action or "unknown"
    if action.startswith("next_"):
        return "next"
    return re.sub(r"_\d+$", "", action) or "unknown"


def _log_latency(handler_name, event_type, elapsed_ms):
    log = logger.warning if elapsed_ms >= SLOW_CALLBACK_MS else logger.info
    log(
        "%s latency handler=%s elapsed_ms=%.1f",
        event_type,
        handler_name,
        elapsed_ms,
    )


def measure_callback(handler_name):
    """Measure one callback entrypoint without logging its full payload."""
    def decorator(handler):
        @wraps(handler)
        async def wrapped(client, query):
            started_at = time.perf_counter()
            try:
                return await handler(client, query)
            finally:
                elapsed_ms = (time.perf_counter() - started_at) * 1000
                log = logger.warning if elapsed_ms >= SLOW_CALLBACK_MS else logger.info
                log(
                    "Callback latency handler=%s prefix=%s elapsed_ms=%.1f",
                    handler_name,
                    _callback_prefix(query),
                    elapsed_ms,
                )

        return wrapped

    return decorator


def measure_command(handler_name):
    """Measure a command entrypoint without logging message content."""
    def decorator(handler):
        @wraps(handler)
        async def wrapped(client, message):
            started_at = time.perf_counter()
            try:
                return await handler(client, message)
            finally:
                elapsed_ms = (time.perf_counter() - started_at) * 1000
                _log_latency(handler_name, "Command", elapsed_ms)

        return wrapped

    return decorator
