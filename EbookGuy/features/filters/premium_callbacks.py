from EbookGuy.features.premium.payments import (
    handle_buy_premium_callback,
    handle_confirm_premium_callback,
)
from EbookGuy.features.premium.views import handle_show_premium_callback

LEGACY_PAYMENT_CALLBACKS = {"crypto_binance", "crypto_other"}


async def maybe_handle_premium_callback(client, query):
    if query.data == "show_premium":
        await handle_show_premium_callback(client, query)
        return True
    if query.data.startswith("buy_premium_"):
        await handle_buy_premium_callback(client, query)
        return True
    if query.data.startswith("confirm_premium_"):
        await handle_confirm_premium_callback(client, query)
        return True
    if query.data.startswith("payment_method_") or query.data in LEGACY_PAYMENT_CALLBACKS:
        await query.answer(
            "This payment option has moved. Please reopen the premium plans.",
            show_alert=True,
        )
        return True
    return False
