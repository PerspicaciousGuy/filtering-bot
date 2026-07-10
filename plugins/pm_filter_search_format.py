from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from plugins.pm_filter_search_results import auto_filter
from plugins.pm_filter_search_state import MockMessage, PENDING_SEARCH


async def show_format_selection(message, query_text):
    """Helper function to show format selection buttons"""
    key = f"{message.chat.id}-{message.id}"
    PENDING_SEARCH[key] = {
        'query': query_text,
        'chat_id': message.chat.id,
        'user_id': message.from_user.id if message.from_user else 0,
        'message_id': message.id
    }
    format_btn = [
        [InlineKeyboardButton("📖 Ebook (PDF, EPUB, etc.)", callback_data=f"format_select#ebook#{key}")],
        [InlineKeyboardButton("🎧 Audiobook (MP3, M4B, etc.)", callback_data=f"format_select#audiobook#{key}")],
        [InlineKeyboardButton("📚 All Formats", callback_data=f"format_select#all#{key}")]
    ]
    await message.reply_text(
        f"<b>🔍 Searching For:</b> <i>{query_text}</i>\n\n<b>Please select the format you want:</b>",
        reply_markup=InlineKeyboardMarkup(format_btn)
    )


async def handle_private_text(bot, message):
    content = message.text
    user = message.from_user.first_name
    user_id = message.from_user.id
    if content.startswith("/") or content.startswith("#"): return  # ignore commands and hashtags
    await show_format_selection(message, content)


async def handle_format_selection(bot, query):
    """Handle format selection (ebook/audiobook) callback"""
    try:
        _, format_type, key = query.data.split("#")
    except ValueError:
        return await query.answer("Invalid format selection!", show_alert=True)
    
    pending = PENDING_SEARCH.get(key)
    if not pending:
        return await query.answer("This search has expired. Please search again.", show_alert=True)
    
    # Check if the user who clicked is the one who searched
    if query.from_user.id != pending['user_id'] and pending['user_id'] != 0:
        return await query.answer("This is not your search!", show_alert=True)
    
    # Update the message to show searching
    format_label = "📖 Ebooks" if format_type == "ebook" else "🎧 Audiobooks" if format_type == "audiobook" else "📚 All Formats"
    await query.message.edit_text(f"<b><i>Searching For {pending['query']} ({format_label}) 🔍</i></b>")
    
    # Create mock message using the top-level MockMessage class
    mock_msg = MockMessage(query, pending)
    
    # Call auto_filter with the format type
    ai_search = True
    await auto_filter(bot, pending['query'], mock_msg, query.message, ai_search, format_type=format_type if format_type != "all" else None)


async def handle_switch_format(bot, query):
    """Handle switch format callback when no results found"""
    try:
        _, format_type, key = query.data.split("#")
    except ValueError:
        return await query.answer("Invalid format switch!", show_alert=True)
    
    pending = PENDING_SEARCH.get(key)
    if not pending:
        return await query.answer("This search has expired. Please search again.", show_alert=True)
    
    # Update the message to show searching
    format_label = "📖 Ebooks" if format_type == "ebook" else "🎧 Audiobooks" if format_type == "audiobook" else "📚 All Formats"
    await query.message.edit_text(f"<b><i>Searching For {pending['query']} ({format_label}) 🔍</i></b>")
    
    # Create mock message using the top-level MockMessage class
    mock_msg = MockMessage(query, pending)
    
    # Call auto_filter with the new format type
    ai_search = True
    await auto_filter(bot, pending['query'], mock_msg, query.message, ai_search, format_type=format_type if format_type != "all" else None)
