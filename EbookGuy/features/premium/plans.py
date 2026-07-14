"""Premium plan pricing derived from global bot settings."""


PLAN_DAYS = (30, 90)


def get_stars_price(settings: dict[str, object], days: int) -> int | None:
    """Return the configured Telegram Stars price for a known plan."""
    if days not in PLAN_DAYS:
        return None
    return int(settings[f"premium_{days}_days_stars"])


def get_inr_price(settings: dict[str, object], days: int) -> int | None:
    """Return the configured INR price for a known plan."""
    if days not in PLAN_DAYS:
        return None
    return int(settings[f"premium_{days}_days_inr"])


__all__ = ["PLAN_DAYS", "get_inr_price", "get_stars_price"]
