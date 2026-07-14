"""Early Telegram handlers that enforce global maintenance mode."""

from html import unescape

from pyrogram import Client, filters

from EbookGuy.features.operations.maintenance import get_maintenance_message


@Client.on_message(
    filters.incoming & filters.private & ~filters.successful_payment,
    group=-100,
)
async def maintenance_message(client, message):
    """Stop private user messages while maintenance is active."""
    notice = await get_maintenance_message(message.from_user)
    if notice is None:
        return
    await message.reply_text(notice)
    message.stop_propagation()


@Client.on_callback_query(group=-100)
async def maintenance_callback(client, query):
    """Stop user callbacks while maintenance is active."""
    notice = await get_maintenance_message(query.from_user)
    if notice is None:
        return
    plain_notice = unescape(
        notice.replace("<b>", "").replace("</b>", "")
    )
    await query.answer(plain_notice[:200], show_alert=True)
    query.stop_propagation()


@Client.on_inline_query(group=-100)
async def maintenance_inline_query(client, query):
    """Return no inline results while maintenance is active."""
    notice = await get_maintenance_message(query.from_user)
    if notice is None:
        return
    await query.answer(
        results=[],
        cache_time=0,
        switch_pm_text="Bot maintenance is active",
        switch_pm_parameter="start",
    )
    query.stop_propagation()
