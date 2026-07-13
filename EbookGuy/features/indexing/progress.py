from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from info import FILTER_BY_EXTENSION


def pause_markup():
    return InlineKeyboardMarkup([[
        InlineKeyboardButton(
            "\u23f8\ufe0f Pause",
            callback_data="index_cancel",
        )
    ]])


def format_progress(current, stats, paused=False):
    """Format the current indexing counters."""
    status = "\u23f8\ufe0f **Paused**" if paused else "\U0001f4e5 **Indexing...**"
    filtered = (
        f"\n\U0001f6ab Filtered: `{stats.get('filtered', 0)}`"
        if FILTER_BY_EXTENSION
        else ""
    )
    return (
        f"{status}\n\n"
        f"\U0001f4ca Messages processed: `{current}`\n"
        f"\u2705 Saved: `{stats['total']}`\n"
        f"\U0001f504 Duplicates: `{stats['duplicate']}`\n"
        f"\U0001f5d1\ufe0f Deleted: `{stats['deleted']}`\n"
        f"\U0001f4c4 No media: `{stats['no_media']}`\n"
        f"\u26a0\ufe0f Unsupported: `{stats['unsupported']}`"
        f"{filtered}\n"
        f"\u274c Errors: `{stats['errors']}`"
    )


def paused_text(current, stats):
    return (
        "\u23f8\ufe0f **Indexing Paused!**\n\n"
        f"Progress saved at message #{current}\n"
        "Use /resume to continue.\n\n"
        + format_progress(current, stats, paused=True)
    )


def rate_limit_text(current, stats, wait_time):
    return (
        "\u23f3 **Rate Limited!**\n\n"
        f"Waiting {wait_time} seconds...\n"
        f"Progress saved at message #{current}\n\n"
        + format_progress(current, stats)
    )


def failure_text(current, stats):
    return (
        "**Indexing failed unexpectedly.**\n\n"
        f"Progress saved at message #{current}\n"
        "Use /resume to continue.\n\n"
        + format_progress(current, stats)
    )


def completion_text(current, stats):
    filtered = (
        f"\n\U0001f6ab Filtered out: `{stats['filtered']}`"
        if FILTER_BY_EXTENSION
        else ""
    )
    return (
        "\u2705 **Indexing Complete!**\n\n"
        f"\U0001f4ca Total messages: `{current}`\n"
        f"\u2705 Files saved: `{stats['total']}`\n"
        f"\U0001f504 Duplicates skipped: `{stats['duplicate']}`\n"
        f"\U0001f5d1\ufe0f Deleted messages: `{stats['deleted']}`\n"
        f"\U0001f4c4 Non-media: `{stats['no_media']}`\n"
        f"\u26a0\ufe0f Unsupported: `{stats['unsupported']}`"
        f"{filtered}\n"
        f"\u274c Errors: `{stats['errors']}`"
    )
