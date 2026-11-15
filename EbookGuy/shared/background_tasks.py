"""Strong references for fire-and-forget asyncio tasks."""

import asyncio


_retained_tasks: set[asyncio.Task] = set()


def retain_task(coroutine) -> None:
    """Run a coroutine in the background and keep it alive until it finishes."""
    task = asyncio.create_task(coroutine)
    _retained_tasks.add(task)
    task.add_done_callback(_retained_tasks.discard)
