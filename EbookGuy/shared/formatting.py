import logging

from pyrogram import enums

from info import CUSTOM_FILE_CAPTION, MAX_LIST_ELM
from EbookGuy.shared.state import temp

logger = logging.getLogger(__name__)


def get_size(size):
    units = ["Bytes", "KB", "MB", "GB", "TB", "PB", "EB"]
    size = float(size)
    i = 0
    while size >= 1024.0 and i < len(units):
        i += 1
        size /= 1024.0
    return "%.2f %s" % (size, units[i])


def format_file_caption(file_name, file_size, file_caption=None):
    """Apply the configured file-caption template to normalized metadata."""
    if not CUSTOM_FILE_CAPTION:
        return file_caption
    try:
        return CUSTOM_FILE_CAPTION.format(
            file_name=file_name or "",
            file_size=file_size or "",
            file_caption=file_caption or "",
            filename=file_name or "",
            filesize=file_size or "",
            duration="",
        )
    except (AttributeError, KeyError, TypeError, ValueError):
        logger.warning("Could not format the custom file caption", exc_info=True)
        return file_caption


def split_list(l, n):
    for i in range(0, len(l), n):
        yield l[i:i + n]  

def list_to_str(k):
    if not k:
        return "N/A"
    elif len(k) == 1:
        return str(k[0])
    elif MAX_LIST_ELM:
        k = k[:int(MAX_LIST_ELM)]
        return ' '.join(f'{elem}, ' for elem in k)
    else:
        return ' '.join(f'{elem}, ' for elem in k)

def last_online(from_user):
    time = ""
    if from_user.is_bot:
        time += "🤖 Bot :("
    elif from_user.status == enums.UserStatus.RECENTLY:
        time += "Recently"
    elif from_user.status == enums.UserStatus.LAST_WEEK:
        time += "Within the last week"
    elif from_user.status == enums.UserStatus.LAST_MONTH:
        time += "Within the last month"
    elif from_user.status == enums.UserStatus.LONG_AGO:
        time += "A long time ago :("
    elif from_user.status == enums.UserStatus.ONLINE:
        time += "Currently Online"
    elif from_user.status == enums.UserStatus.OFFLINE:
        time += from_user.last_online_date.strftime("%a, %d %b %Y, %H:%M:%S")
    return time


def get_cap(files, search, pre='file'):
    cap = f"<b>The Result for => {search}\n\n⚠️ After 5 minutes this message will be Automatically Deleted 🗑️\n\n</b>"
    cap += "<b><u>📚 Your Book Files 👇</u></b>\n\n"
    for file in files:
        cap += f"<b>📁 <a href='https://telegram.me/{temp.U_NAME}?start={pre}_{file['file_id']}'>[{get_size(file['file_size'])}] {' '.join(filter(lambda x: not x.startswith('[') and not x.startswith('@') and not x.startswith('www.'), file['file_name'].split()))}\n\n</a></b>"
    return cap
