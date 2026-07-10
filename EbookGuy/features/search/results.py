import asyncio
import logging
import math
import re
from datetime import datetime, timedelta
from urllib.parse import quote_plus

import pytz
from pyrogram.errors import MessageNotModified
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from Script import script
from database.ia_filterdb import get_search_results
from info import BUTTON_MODE, CUSTOM_FILE_CAPTION, MAX_B_TN
from EbookGuy.features.search.state import FRESH, PENDING_SEARCH
from utils import get_cap, get_settings, get_size, save_group_settings, temp

logger = logging.getLogger(__name__)
logger.setLevel(logging.ERROR)


async def handle_next_page(bot, query):
    ident, req, key, offset = query.data.split("_")
    curr_time = datetime.now(pytz.timezone('Asia/Kolkata')).time()
    if int(req) not in [query.from_user.id, 0]:
        return await query.answer(script.ALRT_TXT.format(query.from_user.first_name), show_alert=True)
    try:
        offset = int(offset)
    except:
        offset = 0
    
    # FRESH now stores dict with 'query' and 'format_type'
    fresh_data = FRESH.get(key)
    if not fresh_data:
        await query.answer(script.OLD_ALRT_TXT.format(query.from_user.first_name),show_alert=True)
        return
    
    # Handle both old format (string) and new format (dict)
    if isinstance(fresh_data, dict):
        search = fresh_data.get('query')
        format_type = fresh_data.get('format_type')
    else:
        search = fresh_data
        format_type = None

    files, n_offset, total = await get_search_results(query.message.chat.id, search, offset=offset, filter=True, format_type=format_type)
    try:
        n_offset = int(n_offset)
    except:
        n_offset = 0

    if not files:
        return
    temp.GETALL[key] = files
    temp.SHORT[query.from_user.id] = query.message.chat.id
    settings = await get_settings(query.message.chat.id)
    pre = 'filep' if settings['file_secure'] else 'file'
    btn = []
    if BUTTON_MODE:
        btn = [
            [
                InlineKeyboardButton(
                    text=f"[{get_size(file['file_size'])}] {' '.join(filter(lambda x: not x.startswith('[') and not x.startswith('@') and not x.startswith('www.'), file['file_name'].split()))}", callback_data=f'{pre}#{file["file_id"]}'
                ),
            ]
            for file in files
        ]

    
    try:
        if settings['max_btn']:
            if 0 < offset <= 10:
                off_set = 0
            elif offset == 0:
                off_set = None
            else:
                off_set = offset - 10
            if n_offset == 0:
                btn.append(
                    [InlineKeyboardButton("⌫ Back", callback_data=f"next_{req}_{key}_{off_set}"), InlineKeyboardButton(f"{math.ceil(int(offset)/10)+1} / {math.ceil(total/10)}", callback_data="pages")]
                )
            elif off_set is None:
                btn.append([InlineKeyboardButton("Page", callback_data="pages"), InlineKeyboardButton(f"{math.ceil(int(offset)/10)+1} / {math.ceil(total/10)}", callback_data="pages"), InlineKeyboardButton("Next ➪", callback_data=f"next_{req}_{key}_{n_offset}")])
            else:
                btn.append(
                    [
                        InlineKeyboardButton("⌫ Back", callback_data=f"next_{req}_{key}_{off_set}"),
                        InlineKeyboardButton(f"{math.ceil(int(offset)/10)+1} / {math.ceil(total/10)}", callback_data="pages"),
                        InlineKeyboardButton("Next ➪", callback_data=f"next_{req}_{key}_{n_offset}")
                    ],
                )
        else:
            if 0 < offset <= int(MAX_B_TN):
                off_set = 0
            elif offset == 0:
                off_set = None
            else:
                off_set = offset - int(MAX_B_TN)
            if n_offset == 0:
                btn.append(
                    [InlineKeyboardButton("⌫ Back", callback_data=f"next_{req}_{key}_{off_set}"), InlineKeyboardButton(f"{math.ceil(int(offset)/int(MAX_B_TN))+1} / {math.ceil(total/int(MAX_B_TN))}", callback_data="pages")]
                )
            elif off_set is None:
                btn.append([InlineKeyboardButton("Page", callback_data="pages"), InlineKeyboardButton(f"{math.ceil(int(offset)/int(MAX_B_TN))+1} / {math.ceil(total/int(MAX_B_TN))}", callback_data="pages"), InlineKeyboardButton("Next ➪", callback_data=f"next_{req}_{key}_{n_offset}")])
            else:
                btn.append(
                    [
                        InlineKeyboardButton("⌫ Back", callback_data=f"next_{req}_{key}_{off_set}"),
                        InlineKeyboardButton(f"{math.ceil(int(offset)/int(MAX_B_TN))+1} / {math.ceil(total/int(MAX_B_TN))}", callback_data="pages"),
                        InlineKeyboardButton("Next ➪", callback_data=f"next_{req}_{key}_{n_offset}")
                    ],
                )
    except KeyError:
        await save_group_settings(query.message.chat.id, 'max_btn', True)
        if 0 < offset <= 10:
            off_set = 0
        elif offset == 0:
            off_set = None
        else:
            off_set = offset - 10
        if n_offset == 0:
            btn.append(
                [InlineKeyboardButton("⌫ Back", callback_data=f"next_{req}_{key}_{off_set}"), InlineKeyboardButton(f"{math.ceil(int(offset)/10)+1} / {math.ceil(total/10)}", callback_data="pages")]
            )
        elif off_set is None:
            btn.append([InlineKeyboardButton("Page", callback_data="pages"), InlineKeyboardButton(f"{math.ceil(int(offset)/10)+1} / {math.ceil(total/10)}", callback_data="pages"), InlineKeyboardButton("Next ➪", callback_data=f"next_{req}_{key}_{n_offset}")])
        else:
            btn.append(
                [
                    InlineKeyboardButton("⌫ Back", callback_data=f"next_{req}_{key}_{off_set}"),
                    InlineKeyboardButton(f"{math.ceil(int(offset)/10)+1} / {math.ceil(total/10)}", callback_data="pages"),
                    InlineKeyboardButton("Next ➪", callback_data=f"next_{req}_{key}_{n_offset}")
                ],
            )
    if not BUTTON_MODE:
        cur_time = datetime.now(pytz.timezone('Asia/Kolkata')).time()
        time_difference = timedelta(hours=cur_time.hour, minutes=cur_time.minute, seconds=(cur_time.second+(cur_time.microsecond/1000000))) - timedelta(hours=curr_time.hour, minutes=cur_time.minute, seconds=(cur_time.second+(cur_time.microsecond/1000000)))
        remaining_seconds = "{:.2f}".format(time_difference.total_seconds())
        cap = await get_cap(settings, remaining_seconds, files, query, total, search, pre)
        try:
            await query.message.edit_text(text=cap, reply_markup=InlineKeyboardMarkup(btn), disable_web_page_preview=True)
        except MessageNotModified:
            pass
    else:
        try:
            await query.edit_message_reply_markup(
                reply_markup=InlineKeyboardMarkup(btn)
            )
        except MessageNotModified:
            pass
    await query.answer()


async def auto_filter(client, name, msg, reply_msg, ai_search, format_type=None):
    curr_time = datetime.now(pytz.timezone('Asia/Kolkata')).time()
    message = msg
    if message.text.startswith("/"): return  # ignore commands
    if re.findall("((^\/|^,|^!|^\.|^[\U0001F600-\U000E007F]).*)", message.text):
        return
    if len(message.text) < 100:
        search = name
        search = search.lower()
        find = search.split(" ")
        search = ""
        removes = ["in", "upload", "full", "horror", "thriller", "mystery", "print", "file"]
        for x in find:
            if x in removes:
                continue
            else:
                search = search + x + " "
        search = re.sub(r"\b(pl(i|e)*?(s|z+|ease|se|ese|(e+)s(e)?)|((send|snd|giv(e)?|gib)(\sme)?)|new|latest|bro|bruh|broh|helo|that|find|link|any(one)|with\ssubtitle(s)?)", "", search, flags=re.IGNORECASE)
        search = re.sub(r"\s+", " ", search).strip()
        search = search.replace("-", " ")
        search = search.replace(":", "")
        search = search.replace(".", "")
        files, offset, total_results = await get_search_results(message.chat.id, search, offset=0, filter=True, format_type=format_type)
        settings = await get_settings(message.chat.id)
        # Fallback: progressively drop words from the end until results found
        if not files:
            words = search.split()
            for drop in range(1, len(words) - 1):
                shorter = " ".join(words[:-drop])
                if len(shorter) < 3:
                    break
                files, offset, total_results = await get_search_results(message.chat.id, shorter, offset=0, filter=True, format_type=format_type)
                if files:
                    search = shorter
                    break
        if not files:
            google_search_url = f"https://www.google.com/search?q={quote_plus(name)}+book"
            btn = [[InlineKeyboardButton("🔍 Check Spelling on Google", url=google_search_url)]]
            
            # Add switch format button if a specific format was selected
            key = f"{message.chat.id}-{message.id}"
            if format_type == "ebook":
                # Keep the search in PENDING_SEARCH for switch_format to use
                PENDING_SEARCH[key] = {
                    'query': name,
                    'chat_id': message.chat.id,
                    'user_id': message.from_user.id if message.from_user else 0,
                    'message_id': message.id
                }
                btn.insert(0, [InlineKeyboardButton("🎧 Try Audiobook Instead", callback_data=f"switch_format#audiobook#{key}")])
                btn.append([InlineKeyboardButton("📚 Search All Formats", callback_data=f"switch_format#all#{key}")])
            elif format_type == "audiobook":
                PENDING_SEARCH[key] = {
                    'query': name,
                    'chat_id': message.chat.id,
                    'user_id': message.from_user.id if message.from_user else 0,
                    'message_id': message.id
                }
                btn.insert(0, [InlineKeyboardButton("📖 Try Ebook Instead", callback_data=f"switch_format#ebook#{key}")])
                btn.append([InlineKeyboardButton("📚 Search All Formats", callback_data=f"switch_format#all#{key}")])
            
            format_label = " (📖 Ebooks)" if format_type == "ebook" else " (🎧 Audiobooks)" if format_type == "audiobook" else ""
            return await reply_msg.edit_text(
                text=f"<b>❌ No results found for:</b> <i>{name}</i>{format_label}\n\n" + script.NO_RESULTS_MSG.format(name, name, name),
                reply_markup=InlineKeyboardMarkup(btn),
                disable_web_page_preview=True
            )
    else:
        return
    pre = 'filep' if settings['file_secure'] else 'file'
    key = f"{message.chat.id}-{message.id}"
    req = message.from_user.id if message.from_user else 0
    # Store both search query and format_type for pagination
    FRESH[key] = {'query': search, 'format_type': format_type}
    temp.GETALL[key] = files
    temp.SHORT[message.from_user.id] = message.chat.id
    btn = []
    if BUTTON_MODE:
        btn = [
            [
                InlineKeyboardButton(
                    text=f"[{get_size(file['file_size'])}] {' '.join(filter(lambda x: not x.startswith('[') and not x.startswith('@') and not x.startswith('www.'), file['file_name'].split()))}", callback_data=f'{pre}#{file["file_id"]}'
                ),
            ]
            for file in files
        ]

    if offset != "":
        try:
            if settings['max_btn']:
                btn.append(
                    [InlineKeyboardButton("Page", callback_data="pages"), InlineKeyboardButton(text=f"1/{math.ceil(int(total_results)/10)}",callback_data="pages"), InlineKeyboardButton(text="Next ➪",callback_data=f"next_{req}_{key}_{offset}")]
                )
            else:
                btn.append(
                    [InlineKeyboardButton("Page", callback_data="pages"), InlineKeyboardButton(text=f"1/{math.ceil(int(total_results)/int(MAX_B_TN))}",callback_data="pages"), InlineKeyboardButton(text="Next ➪",callback_data=f"next_{req}_{key}_{offset}")]
                )
        except KeyError:
            await save_group_settings(message.chat.id, 'max_btn', True)
            btn.append(
                [InlineKeyboardButton("Page", callback_data="pages"), InlineKeyboardButton(text=f"1/{math.ceil(int(total_results)/10)}",callback_data="pages"), InlineKeyboardButton(text="Next ➪",callback_data=f"next_{req}_{key}_{offset}")]
            )
    else:
        btn.append(
            [InlineKeyboardButton(text="No More Pages Available",callback_data="pages")]
        )
    cur_time = datetime.now(pytz.timezone('Asia/Kolkata')).time()
    time_difference = timedelta(hours=cur_time.hour, minutes=cur_time.minute, seconds=(cur_time.second+(cur_time.microsecond/1000000))) - timedelta(hours=curr_time.hour, minutes=cur_time.minute, seconds=(cur_time.second+(cur_time.microsecond/1000000)))
    remaining_seconds = "{:.2f}".format(time_difference.total_seconds())
    
    if BUTTON_MODE:
        cap = f"<b>The Result for => {search}\n\n⚠️ After 5 minutes this message will be Automatically Deleted 🗑️\n\n</b>"
    else:
        cap = f"<b>The Result for => {search}\n\n⚠️ After 5 minutes this message will be Automatically Deleted 🗑️\n\n</b>"
        cap+="<b><u>📚 Your Book Files 👇</u></b>\n\n"
        for file in files:
            cap += f"<b>📁 <a href='https://telegram.me/{temp.U_NAME}?start={pre}_{file['file_id']}'>[{get_size(file['file_size'])}] {' '.join(filter(lambda x: not x.startswith('[') and not x.startswith('@') and not x.startswith('www.'), file['file_name'].split()))}\n\n</a></b>"

    search_results_message = await reply_msg.edit_text(text=cap, reply_markup=InlineKeyboardMarkup(btn), disable_web_page_preview=True)
    
    try:
        if settings['auto_delete']:
            await asyncio.sleep(300)
            await search_results_message.delete()
            await message.delete()
    except KeyError:
        await save_group_settings(message.chat.id, 'auto_delete', True)
        await asyncio.sleep(300)
        await search_results_message.delete()
        await message.delete()
