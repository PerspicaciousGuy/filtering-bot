import datetime
from dataclasses import dataclass

from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from database.users_chats_db import db
from EbookGuy.shared.analytics import track_event
from EbookGuy.shared.global_settings import get_global_settings


BYTES_PER_MB = 1024 * 1024
DOWNLOAD_UPDATE_RETRIES = 3


@dataclass(frozen=True)
class DownloadAccess:
    """Result of evaluating and optionally consuming a download allowance."""

    is_allowed: bool
    is_premium: bool
    count: int
    daily_limit: int
    cooldown_remaining: int = 0
    file_size_limit_mb: int = 0
    denial_reason: str = ""


@dataclass(frozen=True)
class DownloadDecision:
    """An evaluated response and the database fields needed to commit it."""

    access: DownloadAccess
    updates: dict[str, object] | None


def _premium_upgrade_markup():
    return InlineKeyboardMarkup(
        [[
            InlineKeyboardButton(
                "\u2b50 Upgrade to Premium",
                callback_data="show_premium",
            )
        ]]
    )


def _limit_message(access):
    if access.denial_reason == "downloads_disabled":
        return "<b>Downloads Temporarily Disabled</b>\n\nPlease try again later."
    if access.denial_reason == "file_size":
        return (
            "<b>File Too Large</b>\n\n"
            f"Your maximum file size is <b>{access.file_size_limit_mb} MB</b>."
        )
    if access.denial_reason == "busy":
        return "<b>Download Busy</b>\n\nPlease try the download again."
    if access.cooldown_remaining > 0:
        return (
            "<b>Rate Limited</b>\n\n"
            f"Please wait <b>{access.cooldown_remaining} seconds</b> "
            "before your next download."
        )
    if not access.is_premium:
        return (
            "<b>Free Downloads Used</b>\n\n"
            "You have used all your free downloads for today. "
            "Upgrade to the <b>Premium plan</b> for higher daily limits."
        )
    return (
        "<b>Daily Limit Reached</b>\n\n"
        "You have reached the premium limit of "
        f"<b>{access.daily_limit} download(s) per day</b>."
    )


async def send_download_limit_message(message, access):
    """Reply with the applicable rich download-denial message."""
    can_upgrade = (
        not access.is_premium
        and access.denial_reason not in {"downloads_disabled", "busy"}
    )
    await message.reply_text(
        text=_limit_message(access),
        reply_markup=_premium_upgrade_markup() if can_upgrade else None,
    )


async def answer_download_limit_callback(query, access):
    """Send the applicable denial response after callback acknowledgement."""
    await send_download_limit_message(query.message, access)


def _size_denial(is_premium, file_size, limits):
    daily_limit, size_limit = limits
    if size_limit <= 0 or file_size <= size_limit * BYTES_PER_MB:
        return None
    return DownloadAccess(
        False,
        is_premium,
        0,
        daily_limit,
        file_size_limit_mb=size_limit,
        denial_reason="file_size",
    )


def _evaluate_download(profile, file_size, settings):
    now = datetime.datetime.now()
    premium_expiry = profile.get("premium_expiry")
    has_expired = bool(
        profile.get("is_premium")
        and premium_expiry
        and now > premium_expiry
    )
    is_premium = bool(profile.get("is_premium")) and not has_expired
    tier = "premium" if is_premium else "free"
    daily_limit = int(settings[f"{tier}_daily_limit"])
    size_limit = int(settings[f"{tier}_max_file_size_mb"])
    status_update = {"is_premium": False} if has_expired else None

    denied = _size_denial(
        is_premium,
        file_size,
        (daily_limit, size_limit),
    )
    if denied:
        return DownloadDecision(denied, status_update)

    today = str(datetime.date.today())
    current = (
        int(profile.get("daily_downloads", 0))
        if profile.get("last_download_date") == today
        else 0
    )
    cooldown = int(settings["premium_download_cooldown_seconds"])
    last_download = profile.get("last_download_time")
    if is_premium and last_download and cooldown > 0:
        elapsed = (now - last_download).total_seconds()
        if elapsed < cooldown:
            remaining = max(1, cooldown - int(elapsed))
            access = DownloadAccess(
                False, True, current, daily_limit, remaining
            )
            return DownloadDecision(access, status_update)
    if daily_limit > 0 and current >= daily_limit:
        access = DownloadAccess(
            False, is_premium, current, daily_limit
        )
        return DownloadDecision(access, status_update)

    updates = {
        "daily_downloads": current + 1,
        "last_download_date": today,
        "last_download_time": now,
    }
    if status_update:
        updates.update(status_update)
    access = DownloadAccess(
        True,
        is_premium,
        current + 1,
        daily_limit,
    )
    return DownloadDecision(access, updates)


async def _consume_download(user_id, file_size, settings):
    for _attempt in range(DOWNLOAD_UPDATE_RETRIES):
        profile = await db.get_download_profile(user_id)
        if profile is None:
            await db.ensure_download_user(user_id)
            continue
        decision = _evaluate_download(profile, file_size, settings)
        if decision.updates is None:
            return decision.access
        if await db.try_update_download_usage(
            profile,
            decision.updates,
        ):
            return decision.access
    return DownloadAccess(
        False,
        False,
        0,
        0,
        denial_reason="busy",
    )


async def check_and_increment_download(user_id, file_size=0):
    """Check the user's limits, increment an allowed download, and return its state."""
    settings = await get_global_settings()
    if not settings["downloads_enabled"]:
        access = DownloadAccess(
            False,
            False,
            0,
            0,
            denial_reason="downloads_disabled",
        )
        track_event(
            "download.denied",
            user_id,
            is_premium=False,
            reason=access.denial_reason,
        )
        return access
    access = await _consume_download(user_id, file_size, settings)
    track_event(
        "download.completed" if access.is_allowed else "download.denied",
        user_id,
        is_premium=bool(access.is_premium),
        reason=(
            "allowed"
            if access.is_allowed
            else access.denial_reason or "daily_limit"
        ),
    )
    return access


def download_count_text(access):
    """Format the consumed daily allowance after a successful download."""
    limit = access.daily_limit or "Unlimited"
    return f"<b>Downloads today:</b> <code>{access.count}/{limit}</code>"
