import asyncio, logging, os

from Script import script
from pyrogram.types import *
from database.ia_filterdb import get_file_details
from database.users_chats_db import db
from info import *
from utils import get_size

logger = logging.getLogger(__name__)

async def handle_convert_menu_callback(client, query):
    _, pre, file_id = query.data.split("#", 2)
    user_id = query.from_user.id

    is_premium, _ = await db.get_premium_status(user_id)
    if not is_premium:
        btn = [
            [InlineKeyboardButton("⭐ Upgrade to Premium", callback_data="show_premium")],
            [InlineKeyboardButton("⬅️ Back", callback_data=f"convert_back#{pre}#{file_id}")]
        ]
        await query.message.edit_text(
            "<b>🔒 Premium Feature</b>\n\nConverting books between formats is available for <b>Premium subscribers</b> only.\n\nUpgrade to unlock!",
            reply_markup=InlineKeyboardMarkup(btn)
        )
        return

    remaining = await db.get_remaining_conversions(user_id)
    if remaining <= 0:
        return await query.answer("Daily conversion limit reached (3/day). Try again tomorrow!", show_alert=True)

    files_ = await get_file_details(file_id)
    if not files_:
        return await query.answer("File not found.", show_alert=True)

    CONVERTIBLE = ['epub', 'pdf', 'mobi']
    detected_ext = next((w for w in reversed(files_['file_name'].lower().split()) if w in CONVERTIBLE), None)
    if not detected_ext:
        return await query.answer("Could not detect file format for conversion.", show_alert=True)

    targets = [fmt for fmt in CONVERTIBLE if fmt != detected_ext]
    btn = [[InlineKeyboardButton(f"📄 To {fmt.upper()}", callback_data=f"do_convert#{pre}#{file_id}#{fmt}")] for fmt in targets]
    btn.append([InlineKeyboardButton("⬅️ Back", callback_data=f"convert_back#{pre}#{file_id}")])

    clean_title = ' '.join(filter(lambda x: not x.startswith('[') and not x.startswith('@'), files_['file_name'].split()))
    await query.message.edit_text(
        f"<b>🔄 Convert Format</b>\n\n📖 <b>{clean_title}</b>\nSource format: <code>{detected_ext.upper()}</code>\n\nChoose target format:\n<i>({remaining} conversion(s) remaining today)</i>",
        reply_markup=InlineKeyboardMarkup(btn)
    )

async def handle_do_convert_callback(client, query):
    parts = query.data.split("#", 3)
    _, pre, file_id, target_fmt = parts
    user_id = query.from_user.id

    files_ = await get_file_details(file_id)
    if not files_:
        return await query.answer("File not found.", show_alert=True)

    CONVERTIBLE = ['epub', 'pdf', 'mobi']
    src_ext = next((w for w in reversed(files_['file_name'].lower().split()) if w in CONVERTIBLE), None)
    if not src_ext:
        return await query.answer("Could not detect source format.", show_alert=True)

    await query.message.edit_text(f"⏳ <b>Converting {src_ext.upper()} → {target_fmt.upper()}...</b>\n\nThis may take up to 30 seconds.")

    input_path = f"/tmp/{file_id}.{src_ext}"
    output_path = f"/tmp/{file_id}.{target_fmt}"

    try:
        await client.download_media(file_id, file_name=input_path)

        proc = await asyncio.create_subprocess_exec(
            "ebook-convert", input_path, output_path,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        await asyncio.wait_for(proc.communicate(), timeout=120)

        if not os.path.exists(output_path):
            await query.message.edit_text("❌ <b>Conversion failed.</b> The file may be DRM-protected or corrupted.")
            return

        clean_title = ' '.join(filter(lambda x: not x.startswith('[') and not x.startswith('@'), files_['file_name'].split()))
        send_file_name = f"{clean_title} [@freeaudiobooksbot].{target_fmt}"
        caption = f"<code>{send_file_name}</code>\n<b>Converted:</b> {src_ext.upper()} → {target_fmt.upper()}"

        await query.message.delete()
        msg = await client.send_document(
            chat_id=user_id,
            document=output_path,
            file_name=send_file_name,
            caption=caption,
            protect_content=True if pre == 'filep' else False
        )
        await db.increment_conversions(user_id)
        remaining = await db.get_remaining_conversions(user_id)
        count_msg = await msg.reply(f"✅ <b>Conversion complete!</b>\n<i>({remaining} conversion(s) remaining today)</i>\n\n" + script.IMPORTANT_DELETE_MSG)
        await asyncio.sleep(600)
        await msg.delete()
        await count_msg.delete()

    except asyncio.TimeoutError:
        await query.message.edit_text("❌ <b>Conversion timed out.</b> Please try again.")
    except Exception:
        logger.exception("Failed to convert file")
        await query.message.edit_text("<b>Conversion failed.</b> Please try again later.")
    finally:
        for path in [input_path, output_path]:
            if os.path.exists(path):
                os.remove(path)

async def handle_convert_back_callback(client, query):
    _, pre, file_id = query.data.split("#", 2)
    files_ = await get_file_details(file_id)
    if not files_:
        return await query.answer("File not found.", show_alert=True)

    title = files_["file_name"]
    size = get_size(files_["file_size"])
    clean_title = ' '.join(filter(lambda x: not x.startswith('[') and not x.startswith('@'), title.split()))
    CONVERTIBLE = ['epub', 'pdf', 'mobi', 'azw', 'azw3']
    detected_ext = next((w for w in reversed(title.lower().split()) if w in CONVERTIBLE), None)

    btn = [[InlineKeyboardButton("📥 Download", callback_data=f"download_book#{pre}#{file_id}")]]
    if detected_ext:
        btn.append([InlineKeyboardButton("🔄 Convert Format", callback_data=f"convert_menu#{pre}#{file_id}")])

    await query.message.edit_text(
        text=f"<b>📖 {clean_title}</b>\n<b>📦 Size:</b> {size}",
        reply_markup=InlineKeyboardMarkup(btn)
    )
