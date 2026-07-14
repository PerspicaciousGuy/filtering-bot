"""Display metadata and category ownership for global bot settings."""

from EbookGuy.shared.settings_descriptions import SETTING_DESCRIPTIONS


CATEGORY_LABELS = {
    "usage": "Usage Limits",
    "access": "Access & Welcome",
    "channels": "Channels",
    "search": "Search",
    "delivery": "Delivery",
    "requests": "Requests",
    "premium": "Premium",
    "operations": "Bot Operation",
}

EDITABLE_CATEGORIES = set(CATEGORY_LABELS)

SETTING_LABELS = {
    "free_daily_limit": "Free downloads per day",
    "premium_daily_limit": "Premium downloads per day",
    "premium_download_cooldown_seconds": "Premium download cooldown",
    "free_max_file_size_mb": "Free maximum file size",
    "premium_max_file_size_mb": "Premium maximum file size",
    "premium_daily_conversion_limit": "Premium conversions per day",
    "file_channel_ids": "File indexing channels",
    "delete_channel_ids": "File deletion channels",
    "index_request_channel_id": "Index-request channel ID",
    "support_chat_id": "Support fallback chat ID",
    "force_subscription_enabled": "Force subscription",
    "required_subscription_channels": "Required subscription channels",
    "welcome_message_enabled": "Custom welcome message",
    "welcome_message_template": "Welcome message template",
    "search_enabled": "Search enabled",
    "results_per_page": "Results per page",
    "max_search_results": "Maximum search results",
    "search_suggestions_enabled": "Search suggestions",
    "search_result_expiry_seconds": "Search result expiry",
    "use_caption_filter": "Search file captions",
    "trending_searches_enabled": "Trending searches",
    "trending_period_days": "Trending period",
    "trending_results_limit": "Trending result count",
    "downloads_enabled": "Downloads enabled",
    "protect_content": "Protect delivered files",
    "auto_delete_enabled": "Auto-delete delivered files",
    "auto_delete_delay_seconds": "Auto-delete delay",
    "custom_file_caption": "File caption template",
    "conversion_enabled": "Audiobook conversion",
    "max_conversion_size_mb": "Maximum conversion size",
    "requests_enabled": "Requests enabled",
    "request_daily_limit": "Requests per day",
    "request_cooldown_seconds": "Request cooldown",
    "allow_duplicate_requests": "Allow duplicate requests",
    "request_channel_id": "Request channel ID",
    "request_notifications_enabled": "Request notifications",
    "request_author_required": "Require author name",
    "request_processing_message": "Processing request message",
    "request_unavailable_message": "Unavailable request message",
    "request_uploaded_message": "Uploaded request message",
    "request_already_available_message": "Already available request message",
    "premium_purchases_enabled": "Premium purchases",
    "stars_payments_enabled": "Telegram Stars payments",
    "premium_30_days_stars": "30-day Stars price",
    "premium_90_days_stars": "90-day Stars price",
    "premium_30_days_inr": "30-day INR price",
    "premium_90_days_inr": "90-day INR price",
    "premium_expiry_notifications_enabled": "Expiry notifications",
    "maintenance_mode": "Maintenance mode",
    "maintenance_message": "Maintenance message",
    "indexing_enabled": "Indexing enabled",
    "broadcasts_enabled": "Broadcasts enabled",
    "log_channel_id": "Log channel ID",
    "support_url": "Support URL",
}

CATEGORY_SETTINGS = {
    "usage": (
        "free_daily_limit",
        "premium_daily_limit",
        "premium_download_cooldown_seconds",
        "free_max_file_size_mb",
        "premium_max_file_size_mb",
        "premium_daily_conversion_limit",
    ),
    "access": (
        "force_subscription_enabled",
        "required_subscription_channels",
        "welcome_message_enabled",
        "welcome_message_template",
    ),
    "channels": (
        "file_channel_ids",
        "delete_channel_ids",
        "request_channel_id",
        "index_request_channel_id",
        "log_channel_id",
        "support_chat_id",
    ),
    "search": (
        "search_enabled",
        "results_per_page",
        "max_search_results",
        "search_suggestions_enabled",
        "search_result_expiry_seconds",
        "use_caption_filter",
        "trending_searches_enabled",
        "trending_period_days",
        "trending_results_limit",
    ),
    "delivery": (
        "downloads_enabled",
        "protect_content",
        "auto_delete_enabled",
        "auto_delete_delay_seconds",
        "custom_file_caption",
        "conversion_enabled",
        "max_conversion_size_mb",
    ),
    "requests": (
        "requests_enabled",
        "request_daily_limit",
        "request_cooldown_seconds",
        "allow_duplicate_requests",
        "request_notifications_enabled",
        "request_author_required",
        "request_processing_message",
        "request_unavailable_message",
        "request_uploaded_message",
        "request_already_available_message",
    ),
    "premium": (
        "premium_purchases_enabled",
        "stars_payments_enabled",
        "premium_30_days_stars",
        "premium_90_days_stars",
        "premium_30_days_inr",
        "premium_90_days_inr",
        "premium_expiry_notifications_enabled",
    ),
    "operations": (
        "maintenance_mode",
        "maintenance_message",
        "indexing_enabled",
        "broadcasts_enabled",
        "support_url",
    ),
}


def get_setting_category(key: str) -> str:
    """Return the category that owns one known setting key."""
    for category, keys in CATEGORY_SETTINGS.items():
        if key in keys:
            return category
    raise KeyError(f"Unknown global setting: {key}")


__all__ = [
    "CATEGORY_LABELS",
    "CATEGORY_SETTINGS",
    "EDITABLE_CATEGORIES",
    "SETTING_DESCRIPTIONS",
    "SETTING_LABELS",
    "get_setting_category",
]
