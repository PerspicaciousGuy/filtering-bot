"""Administrator-facing descriptions for global bot settings."""


SETTING_DESCRIPTIONS = {
    "free_daily_limit": (
        "Maximum indexed-file downloads allowed for each free user per day. "
        "Set it to 0 for unlimited downloads."
    ),
    "premium_daily_limit": (
        "Maximum indexed-file downloads allowed for each Premium user per day. "
        "Set it to 0 for unlimited downloads."
    ),
    "premium_download_cooldown_seconds": (
        "Minimum wait between Premium downloads, measured in seconds. "
        "Set it to 0 to remove the cooldown."
    ),
    "free_max_file_size_mb": (
        "Largest indexed file a free user may download, measured in MB. "
        "Set it to 0 to allow any size."
    ),
    "premium_max_file_size_mb": (
        "Largest indexed file a Premium user may download, measured in MB. "
        "Set it to 0 to allow any size."
    ),
    "premium_daily_conversion_limit": (
        "Maximum audiobook conversions allowed for each Premium user per day. "
        "Set it to 0 for unlimited conversions."
    ),
    "file_channel_ids": (
        "Channels whose new ebook and audiobook posts are saved automatically "
        "to the searchable file database. A deletion channel cannot also be "
        "used here."
    ),
    "delete_channel_ids": (
        "Channels whose incoming file posts remove matching records from the "
        "searchable file database. An indexing channel cannot also be used here."
    ),
    "index_request_channel_id": (
        "Telegram channel that receives indexing requests from regular users. "
        "Set it to 0 to use the configured log channel."
    ),
    "support_chat_id": (
        "Fallback Telegram chat that receives request updates when a requester "
        "has blocked the bot. Set it to 0 to disable the fallback."
    ),
    "force_subscription_enabled": (
        "Requires regular users to join every configured subscription channel "
        "before searching, requesting, downloading, or converting files."
    ),
    "required_subscription_channels": (
        "Channels users must join when force subscription is enabled. The bot "
        "must be able to access every configured channel."
    ),
    "welcome_message_enabled": (
        "Uses the configurable welcome template for the private /start screen. "
        "Disable it to use the built-in welcome text."
    ),
    "welcome_message_template": (
        "Telegram HTML template used for the private /start welcome screen."
    ),
    "search_enabled": (
        "Controls private and inline book search for users. Admin settings remain "
        "available when search is disabled."
    ),
    "results_per_page": "Number of books shown on each private search results page.",
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
    "use_caption_filter": "Includes stored file captions when matching search terms.",
    "trending_searches_enabled": (
        "Records normalized search queries for analytics and allows regular users "
        "to view them with /trending_now."
    ),
    "trending_period_days": (
        "Number of recent days included in public and administrator trending lists."
    ),
    "trending_results_limit": (
        "Maximum number of search terms shown in a trending list."
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
    "custom_file_caption": "Caption template applied to files delivered by the bot.",
    "conversion_enabled": (
        "Controls whether eligible audiobook conversion workflows are available."
    ),
    "max_conversion_size_mb": (
        "Largest source file accepted for conversion, measured in MB."
    ),
    "requests_enabled": "Controls whether users can submit book requests.",
    "request_daily_limit": "Maximum book requests allowed for each user per day.",
    "request_cooldown_seconds": (
        "Minimum wait between book requests, measured in seconds."
    ),
    "allow_duplicate_requests": (
        "Controls whether a title may be requested more than once."
    ),
    "request_channel_id": "Telegram channel that receives submitted book requests.",
    "request_notifications_enabled": (
        "Controls whether request-related notifications are sent."
    ),
    "request_author_required": (
        "Requires requests to use the format Book title | Author name."
    ),
    "request_processing_message": (
        "Telegram HTML template sent when a request is being processed."
    ),
    "request_unavailable_message": (
        "Telegram HTML template sent when a requested book is unavailable."
    ),
    "request_uploaded_message": (
        "Telegram HTML template sent after a requested book is uploaded."
    ),
    "request_already_available_message": (
        "Telegram HTML template sent when a requested book already exists."
    ),
    "premium_purchases_enabled": (
        "Controls whether users can start a Premium purchase."
    ),
    "stars_payments_enabled": (
        "Controls whether Telegram Stars is offered as a payment method."
    ),
    "premium_30_days_stars": "Telegram Stars price for 30 days of Premium access.",
    "premium_90_days_stars": "Telegram Stars price for 90 days of Premium access.",
    "premium_30_days_inr": "INR price for 30 days of Premium access.",
    "premium_90_days_inr": "INR price for 90 days of Premium access.",
    "premium_expiry_notifications_enabled": (
        "Controls whether users are notified before Premium access expires."
    ),
    "maintenance_mode": (
        "Temporarily restricts normal user features while maintenance is active."
    ),
    "maintenance_message": "Message shown while maintenance mode is active.",
    "indexing_enabled": (
        "Controls whether administrators can add new files to the search index."
    ),
    "broadcasts_enabled": (
        "Controls whether administrator broadcast commands may send messages."
    ),
    "log_channel_id": "Telegram channel used for operational bot logs.",
    "support_url": "Support destination shown to users who need assistance.",
}


__all__ = ["SETTING_DESCRIPTIONS"]
