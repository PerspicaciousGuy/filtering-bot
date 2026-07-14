"""Environment-backed defaults for global bot settings."""

from info import (
    AUTH_CHANNEL,
    AUTO_DELETE,
    CACHE_TIME,
    CHANNELS,
    CUSTOM_FILE_CAPTION,
    DELETE_CHANNELS,
    FREE_DAILY_LIMIT,
    INDEX_REQ_CHANNEL,
    LOG_CHANNEL,
    PM_SEARCH,
    PREMIUM_DAILY_LIMIT,
    PREMIUM_DOWNLOAD_COOLDOWN,
    PREMIUM_PRICES,
    PREMIUM_PRICES_INR,
    PROTECT_CONTENT,
    REQST_CHANNEL,
    SUPPORT_CHAT,
    SUPPORT_CHAT_ID,
    USE_CAPTION_FILTER,
)


DEFAULT_WELCOME_TEMPLATE = """<b>Hello {mention},</b>

Welcome to your personal <b>Digital Library</b>.

Search {library_count}+ ebooks and audiobooks by sending a title or author.
Free users receive <b>{free_limit} download(s) per day</b>.

Use /plan for Premium access or visit {support_url} for support."""

DEFAULT_REQUEST_PROCESSING_MESSAGE = """<b>Hello {user_name},</b>

Your request for <b>{book_title}</b> by <b>{author_name}</b> is now processing.
We will notify you when its availability is confirmed."""

DEFAULT_REQUEST_UNAVAILABLE_MESSAGE = """<b>Hello {user_name},</b>

Your request for <b>{book_title}</b> by <b>{author_name}</b> is unavailable.
<b>Reason:</b> {reason}"""

DEFAULT_REQUEST_UPLOADED_MESSAGE = """<b>Hello {user_name},</b>

Your request for <b>{book_title}</b> by <b>{author_name}</b> has been uploaded.
{download_link}"""

DEFAULT_REQUEST_ALREADY_AVAILABLE_MESSAGE = """<b>Hello {user_name},</b>

Your request for <b>{book_title}</b> by <b>{author_name}</b> is already available.
{download_link}"""

LEGACY_GLOBAL_SETTING_ALIASES = {
    "request_processing_message": "request_accepted_message",
    "request_unavailable_message": "request_rejected_message",
    "request_uploaded_message": "request_completed_message",
}

DEFAULT_GLOBAL_SETTINGS = {
    "free_daily_limit": FREE_DAILY_LIMIT,
    "premium_daily_limit": PREMIUM_DAILY_LIMIT,
    "premium_download_cooldown_seconds": PREMIUM_DOWNLOAD_COOLDOWN,
    "free_max_file_size_mb": 0,
    "premium_max_file_size_mb": 0,
    "premium_daily_conversion_limit": 3,
    "file_channel_ids": list(CHANNELS),
    "delete_channel_ids": list(DELETE_CHANNELS),
    "index_request_channel_id": INDEX_REQ_CHANNEL or 0,
    "support_chat_id": SUPPORT_CHAT_ID or 0,
    "force_subscription_enabled": bool(AUTH_CHANNEL),
    "required_subscription_channels": (
        [AUTH_CHANNEL] if AUTH_CHANNEL else []
    ),
    "welcome_message_enabled": True,
    "welcome_message_template": DEFAULT_WELCOME_TEMPLATE,
    "search_enabled": PM_SEARCH,
    "results_per_page": 10,
    "max_search_results": 100,
    "search_suggestions_enabled": True,
    "search_result_expiry_seconds": CACHE_TIME,
    "use_caption_filter": USE_CAPTION_FILTER,
    "trending_searches_enabled": True,
    "trending_period_days": 7,
    "trending_results_limit": 10,
    "downloads_enabled": True,
    "protect_content": PROTECT_CONTENT,
    "auto_delete_enabled": AUTO_DELETE,
    "auto_delete_delay_seconds": 600,
    "custom_file_caption": CUSTOM_FILE_CAPTION,
    "conversion_enabled": True,
    "max_conversion_size_mb": 0,
    "requests_enabled": True,
    "request_daily_limit": 0,
    "request_cooldown_seconds": 0,
    "allow_duplicate_requests": True,
    "request_channel_id": REQST_CHANNEL or 0,
    "request_notifications_enabled": True,
    "request_author_required": False,
    "request_processing_message": DEFAULT_REQUEST_PROCESSING_MESSAGE,
    "request_unavailable_message": DEFAULT_REQUEST_UNAVAILABLE_MESSAGE,
    "request_uploaded_message": DEFAULT_REQUEST_UPLOADED_MESSAGE,
    "request_already_available_message": DEFAULT_REQUEST_ALREADY_AVAILABLE_MESSAGE,
    "premium_purchases_enabled": True,
    "stars_payments_enabled": True,
    "premium_30_days_stars": PREMIUM_PRICES[30],
    "premium_90_days_stars": PREMIUM_PRICES[90],
    "premium_30_days_inr": PREMIUM_PRICES_INR[30],
    "premium_90_days_inr": PREMIUM_PRICES_INR[90],
    "premium_expiry_notifications_enabled": True,
    "maintenance_mode": False,
    "maintenance_message": "The bot is temporarily unavailable.",
    "indexing_enabled": True,
    "broadcasts_enabled": True,
    "log_channel_id": LOG_CHANNEL,
    "support_url": f"https://t.me/{SUPPORT_CHAT}",
}


__all__ = ["DEFAULT_GLOBAL_SETTINGS", "LEGACY_GLOBAL_SETTING_ALIASES"]
