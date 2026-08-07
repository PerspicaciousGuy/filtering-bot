"""Configuration and link construction for manual Premium payments."""

from dataclasses import dataclass
from urllib.parse import urlencode

from pyrogram.types import InlineKeyboardButton

from EbookGuy.features.premium.plans import get_inr_price


@dataclass(frozen=True)
class ManualPaymentDetails:
    """Display and link data for one manually verified payment."""

    provider: str
    provider_label: str
    days: int
    amount_label: str
    destination_label: str
    destination_value: str
    payment_url: str


def is_http_url(value: str) -> bool:
    """Return whether a value can be used as a Telegram HTTP URL button."""
    return value.startswith(("https://", "http://"))


def build_upi_payment_url(days: int, settings: dict[str, object]) -> str:
    """Build the direct UPI URI for a configured Premium plan."""
    amount = int(get_inr_price(settings, days) or 0)
    upi_id = str(settings["upi_id"])
    payee_name = str(settings["upi_payee_name"])
    if (
        not settings["upi_payments_enabled"]
        or not upi_id
        or not payee_name
        or amount <= 0
    ):
        return ""
    query = urlencode(
        {
            "pa": upi_id,
            "pn": payee_name,
            "cu": "INR",
            "am": str(amount),
        }
    )
    return f"upi://pay?{query}"


def _binance_payment_url(
    days: int,
    settings: dict[str, object],
) -> str:
    if not settings["binance_payments_enabled"] or days not in {30, 90}:
        return ""
    url = str(settings[f"binance_pay_url_{days}"])
    return url if is_http_url(url) else ""


def _format_usd_cents(cents: object) -> str:
    whole, fraction = divmod(int(cents), 100)
    return f"{whole}.{fraction:02d}"


def manual_payment_method_buttons(
    days: int,
    settings: dict[str, object],
) -> list[list[InlineKeyboardButton]]:
    """Return configured manual payment method buttons for one plan."""
    buttons = []
    if build_upi_payment_url(days, settings):
        buttons.append(
            [
                InlineKeyboardButton(
                    "Google Pay / UPI",
                    callback_data=f"manual_payment_upi_{days}",
                )
            ]
        )
    if _binance_payment_url(days, settings):
        buttons.append(
            [
                InlineKeyboardButton(
                    "Binance Pay",
                    callback_data=f"manual_payment_binance_{days}",
                )
            ]
        )
    return buttons


def manual_payment_method_names(
    days: int,
    settings: dict[str, object],
) -> list[str]:
    """Return user-facing names for configured manual payment methods."""
    names = []
    if build_upi_payment_url(days, settings):
        names.append("Google Pay / UPI - manual verification")
    if _binance_payment_url(days, settings):
        names.append("Binance Pay - manual verification")
    return names


def get_manual_payment_details(
    provider: str,
    days: int,
    settings: dict[str, object],
) -> ManualPaymentDetails | None:
    """Return configured details for one provider and Premium plan."""
    if provider == "upi":
        payment_url = build_upi_payment_url(days, settings)
        amount = int(get_inr_price(settings, days) or 0)
        if not payment_url:
            return None
        return ManualPaymentDetails(
            provider=provider,
            provider_label="Google Pay / UPI",
            days=days,
            amount_label=f"INR {amount}",
            destination_label="UPI ID",
            destination_value=str(settings["upi_id"]),
            payment_url=payment_url,
        )

    payment_url = _binance_payment_url(days, settings)
    amount = _format_usd_cents(
        settings.get(f"binance_{days}_days_usd_cents", 0)
    )
    if provider != "binance" or not payment_url or not amount:
        return None
    return ManualPaymentDetails(
        provider=provider,
        provider_label="Binance Pay",
        days=days,
        amount_label=f"USD {amount}",
        destination_label="Binance Pay ID",
        destination_value=(
            str(settings["binance_pay_id"]) or "Open the payment link"
        ),
        payment_url=payment_url,
    )


__all__ = [
    "ManualPaymentDetails",
    "build_upi_payment_url",
    "get_manual_payment_details",
    "is_http_url",
    "manual_payment_method_buttons",
    "manual_payment_method_names",
]
