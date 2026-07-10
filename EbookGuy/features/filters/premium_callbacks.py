async def maybe_handle_premium_callback(client, query):
    if query.data == "show_premium":
        from plugins.premium import show_premium_callback

        await show_premium_callback(client, query)
        return True
    if query.data.startswith("buy_premium_"):
        from plugins.premium import buy_premium_callback

        await buy_premium_callback(client, query)
        return True
    if query.data.startswith("confirm_premium_"):
        from plugins.premium import confirm_premium_callback

        await confirm_premium_callback(client, query)
        return True
    if query.data.startswith("payment_method_"):
        from plugins.premium import payment_method_callback

        await payment_method_callback(client, query)
        return True
    if query.data == "crypto_binance":
        from plugins.premium import crypto_binance_callback

        await crypto_binance_callback(client, query)
        return True
    if query.data == "crypto_other":
        from plugins.premium import crypto_other_callback

        await crypto_other_callback(client, query)
        return True
    return False
