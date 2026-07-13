"""Display metadata and category ownership for global bot settings."""


CATEGORY_LABELS = {
    "usage": "Usage Limits",
    "search": "Search",
    "delivery": "Delivery",
    "requests": "Requests",
    "premium": "Premium",
    "operations": "Bot Operation",
}

EDITABLE_CATEGORIES = {"usage", "search"}

SETTING_LABELS = {
    "free_daily_limit": "Free downloads per day",
    "premium_daily_limit": "Premium downloads per day",
    "premium_download_cooldown_seconds": "Premium download cooldown",
    "free_max_file_size_mb": "Free maximum file size",
    "premium_max_file_size_mb": "Premium maximum file size",
    "premium_daily_conversion_limit": "Premium conversions per day",
    "search_enabled": "Search enabled",
    "results_per_page": "Results per page",
    "max_search_results": "Maximum search results",
    "search_suggestions_enabled": "Search suggestions",
    "search_result_expiry_seconds": "Search result expiry",
    "use_caption_filter": "Search file captions",
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

SETTING_DESCRIPTIONS = {
    "free_daily_limit": (
        "Maximum indexed-file downloads allowed for each free user per day. "
        "Set it to 0 for unlimited downloads."
    ),
    "premium_daily_limit": (
        "Maximum indexed-file downloads allowed for each premium user per day. "
        "Set it to 0 for unlimited downloads."
    ),
    "premium_download_cooldown_seconds": (
        "Minimum wait between premium downloads, measured in seconds. "
        "Set it to 0 to remove the cooldown."
    ),
    "free_max_file_size_mb": (
        "Largest indexed file a free user may download, measured in MB. "
        "Set it to 0 to allow any size."
    ),
    "premium_max_file_size_mb": (
        "Largest indexed file a premium user may download, measured in MB. "
        "Set it to 0 to allow any size."
    ),
    "premium_daily_conversion_limit": (
        "Maximum audiobook conversions allowed for each premium user per day. "
        "Set it to 0 for unlimited conversions."
    ),
    "search_enabled": (
        "Controls private and inline book search for users. Admin settings remain "
        "available when search is disabled."
    ),
    "results_per_page": (
        "Number of books shown on each private search results page."
    ),
    "max_search_results": (
        "Maximum number of matching books retained for one search and its pages."
    ),
    "search_suggestions_enabled": (
        "Allows the bot to retry broad searches and show suggestion links when "
        "an exact search has no results."
    ),
    "search_result_expiry_seconds": (
        "How long private search results remain available before their message "
        "and cached state are removed."
    ),
    "use_caption_filter": (
        "Includes stored Telegram file captions when matching search terms."
    ),
    "downloads_enabled": "Controls whether users can start file downloads.",
    "protect_content": (
        "Prevents Telegram forwarding and saving for files delivered by the bot."
    ),
    "auto_delete_enabled": (
        "Controls whether delivered files are removed automatically after a delay."
    ),
    "auto_delete_delay_seconds": (
        "Time in seconds before an automatically delivered file is deleted."
    ),
    "custom_file_caption": (
        "Caption template applied to files delivered by the bot."
    ),
    "conversion_enabled": (
        "Controls whether eligible audiobook conversion workflows are available."
    ),
    "max_conversion_size_mb": (
        "Largest source file accepted for conversion, measured in MB."
    ),
    "requests_enabled": "Controls whether users can submit book requests.",
    "request_daily_limit": (
        "Maximum book requests allowed for each user per day."
    ),
    "request_cooldown_seconds": (
        "Minimum wait between book requests, measured in seconds."
    ),
    "allow_duplicate_requests": (
        "Controls whether a title may be requested more than once."
    ),
    "request_channel_id": (
        "Telegram channel that receives submitted book requests."
    ),
    "request_notifications_enabled": (
        "Controls whether request-related notifications are sent."
    ),
    "premium_purchases_enabled": (
        "Controls whether users can start a premium purchase."
    ),
    "stars_payments_enabled": (
        "Controls whether Telegram Stars is offered as a payment method."
    ),
    "premium_30_days_stars": (
        "Telegram Stars price for 30 days of premium access."
    ),
    "premium_90_days_stars": (
        "Telegram Stars price for 90 days of premium access."
    ),
    "premium_30_days_inr": "INR price for 30 days of premium access.",
    "premium_90_days_inr": "INR price for 90 days of premium access.",
    "premium_expiry_notifications_enabled": (
        "Controls whether users are notified before premium access expires."
    ),
    "maintenance_mode": (
        "Temporarily restricts normal user features while maintenance is active."
    ),
    "maintenance_message": (
        "Message shown to users while maintenance mode is active."
    ),
    "indexing_enabled": (
        "Controls whether administrators can add new files to the search index."
    ),
    "broadcasts_enabled": (
        "Controls whether administrator broadcast commands may send messages."
    ),
    "log_channel_id": "Telegram channel used for operational bot logs.",
    "support_url": "Support destination shown to users who need assistance.",
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
    "search": (
        "search_enabled",
        "results_per_page",
        "max_search_results",
        "search_suggestions_enabled",
        "search_result_expiry_seconds",
        "use_caption_filter",
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
        "request_channel_id",
        "request_notifications_enabled",
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
        "log_channel_id",
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
