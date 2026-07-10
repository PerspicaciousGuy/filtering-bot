import re
from os import environ
from Script import script 

id_pattern = re.compile(r'^.\d+$')


def parse_env_bool(name: str, default: bool = False) -> bool:
    """Parse boolean environment flags from common string values."""
    value = environ.get(name)
    if value is None:
        return default

    normalized = value.strip().lower()
    if normalized in {"1", "true", "yes", "y", "on"}:
        return True
    if normalized in {"0", "false", "no", "n", "off", ""}:
        return False
    return default


# ═══════════════════════════════════════════════════════════════════════════════
# 🤖 SECTION 1: BOT CREDENTIALS
# ═══════════════════════════════════════════════════════════════════════════════
# Get these from https://my.telegram.org/apps

SESSION = environ.get('SESSION', 'EbookGuyBot')          # Session name for the bot
API_ID = int(environ.get('API_ID', ''))                  # Your Telegram API ID
API_HASH = environ.get('API_HASH', '')                   # Your Telegram API Hash
BOT_TOKEN = environ.get('BOT_TOKEN', "")                 # Bot token from @BotFather


# ═══════════════════════════════════════════════════════════════════════════════
# 👤 SECTION 2: ADMINS & USERS
# ═══════════════════════════════════════════════════════════════════════════════
# Who can control the bot? Add Telegram user IDs (space-separated for multiple)

ADMINS = [int(admin) if id_pattern.search(admin) else admin for admin in environ.get('ADMINS', '5850899264').split()]
auth_users = [int(user) if id_pattern.search(user) else user for user in environ.get('AUTH_USERS', '5850899264').split()]
AUTH_USERS = (auth_users + ADMINS) if auth_users else []


# ═══════════════════════════════════════════════════════════════════════════════
# 📢 SECTION 3: CHANNEL & GROUP IDs
# ═══════════════════════════════════════════════════════════════════════════════
# All your Telegram channel/group IDs in one place

# 📋 LOG_CHANNEL: Bot sends new user info here when someone starts the bot
# For the main bot
LOG_CHANNEL = int(environ.get('LOG_CHANNEL', '-1002145018097'))

# For test bot
#LOG_CHANNEL = int(environ.get('LOG_CHANNEL', '-1002458827148'))

# 📁 CHANNELS: Upload files here → Bot auto-saves to database (main file storage)
# For the main bot
CHANNELS = [int(ch) if id_pattern.search(ch) else ch for ch in environ.get('CHANNELS', '-1002042914531').split()]

# For test bot
#CHANNELS = [int(ch) if id_pattern.search(ch) else ch for ch in environ.get('CHANNELS', '-1002393037732').split()]

# 🔒 AUTH_CHANNEL: Force subscribe channel - users must join to use bot
auth_channel = environ.get('AUTH_CHANNEL', '-1002181641962')
AUTH_CHANNEL = int(auth_channel) if auth_channel and id_pattern.search(auth_channel) else None

# 📝 REQST_CHANNEL: User book requests go here (via /request or #request)
reqst_channel = environ.get('REQST_CHANNEL', '-1002447612109')
REQST_CHANNEL = int(reqst_channel) if reqst_channel and id_pattern.search(reqst_channel) else None

# 📥 INDEX_REQ_CHANNEL: Index requests from users
INDEX_REQ_CHANNEL = int(environ.get('INDEX_REQ_CHANNEL', LOG_CHANNEL))

# 💬 SUPPORT_CHAT_ID: Support group - bot won't send files here
support_chat_id = environ.get('SUPPORT_CHAT_ID', '')
SUPPORT_CHAT_ID = int(support_chat_id) if support_chat_id and id_pattern.search(support_chat_id) else None



# 🗑️ DELETE_CHANNELS: Forward files here to delete them from database
# For the main bot
DELETE_CHANNELS = [int(dch) if id_pattern.search(dch) else dch for dch in environ.get('DELETE_CHANNELS', '-1002418225707').split()]


# ═══════════════════════════════════════════════════════════════════════════════
# 🔐 SECTION 4: FORCE SUBSCRIBE SETTINGS
# ═══════════════════════════════════════════════════════════════════════════════

# True = Request-to-join mode (user sends join request, admin approves)
# False = Normal mode (user must join channel directly)
REQUEST_TO_JOIN_MODE = parse_env_bool('REQUEST_TO_JOIN_MODE')

# Show "Try Again" button after joining (only for request-to-join mode)
TRY_AGAIN_BTN = parse_env_bool('TRY_AGAIN_BTN')


# ═══════════════════════════════════════════════════════════════════════════════
# 🗄️ SECTION 5: DATABASE (MongoDB)
# ═══════════════════════════════════════════════════════════════════════════════

DATABASE_URI = environ.get('DATABASE_URI', "")           # Main MongoDB connection string
DATABASE_NAME = environ.get('DATABASE_NAME', "booksnew") # Database name
COLLECTION_NAME = environ.get('COLLECTION_NAME', 'ebookguy')  # Collection for files

# Multiple Database Support (for large file collections)
MULTIPLE_DATABASE = parse_env_bool('MULTIPLE_DATABASE')

# Only needed if MULTIPLE_DATABASE = True
O_DB_URI = environ.get('O_DB_URI', "")    # Other data (users, settings)
F_DB_URI = environ.get('F_DB_URI', "")    # File data (primary)
S_DB_URI = environ.get('S_DB_URI', "")    # File data (secondary - when primary is full)


# ═══════════════════════════════════════════════════════════════════════════════
# 🔗 SECTION 6: LINKS & URLs
# ═══════════════════════════════════════════════════════════════════════════════

GRP_LNK = environ.get('GRP_LNK', 'https://t.me/ebookguy')        # Your group link
CHNL_LNK = environ.get('CHNL_LNK', 'https://t.me/ebookguy')      # Your channel link
SUPPORT_CHAT = environ.get('SUPPORT_CHAT', 'codeconvo')          # Support username (without @)
OWNER_LNK = environ.get('OWNER_LNK', 'https://t.me/ebookguy')    # Owner's profile link

# Affiliate/Promo Button Links
BTN_URL_2 = environ.get('BTN_URL_2', 'https://t.me/EbookGuy/14')
BTN_URL_3 = environ.get('BTN_URL_3', 'https://t.me/InsideAds_bot/open?startapp=r_959095428')
#BTN_URL_4 = environ.get('BTN_URL_4', '')  # Reserved for future button

# ═══════════════════════════════════════════════════════════════════════════════
# 📱 SECTION 7: START BUTTON CONFIGURATION
# ═══════════════════════════════════════════════════════════════════════════════
# Centralized button configuration - change names and URLs in one place

START_BUTTONS = [
    {"label": "🔥 Our Main Channel 🔥", "url": CHNL_LNK},
    {"label": "📚 How to Search Book Properly", "url": BTN_URL_2},
    {"label": "� Grow Your Telegram Channel", "url": BTN_URL_3},
    # {"label": "💖 His Secret Obsession", "url": BTN_URL_4},  # Reserved
]


# ═══════════════════════════════════════════════════════════════════════════════
# 💰 SECTION 7: PREMIUM SYSTEM (Telegram Stars)
# ═══════════════════════════════════════════════════════════════════════════════

# Free user daily download limit
FREE_DAILY_LIMIT = int(environ.get('FREE_DAILY_LIMIT', 2))
PREMIUM_DAILY_LIMIT = int(environ.get('PREMIUM_DAILY_LIMIT', 20))
PREMIUM_DOWNLOAD_COOLDOWN = int(environ.get('PREMIUM_DOWNLOAD_COOLDOWN', 30))  # seconds between downloads

# Premium pricing in Telegram Stars (2-tier pricing)
PREMIUM_PRICES = {
    30: 100,    # 30 Days (1 Month) - 100 Stars (~$1.99 USD)
    90: 250,    # 90 Days (3 Months) - 250 Stars (~$4.99 USD)
}

# INR pricing for UPI/PayPal (shown only in UPI menu)
PREMIUM_PRICES_INR = {
    30: 150,    # 30 Days (1 Month) - ₹150
    90: 350,    # 90 Days (3 Months) - ₹350
}

# ═══════════════════════════════════════════════════════════════════════════════
# 💳 SECTION 7a: PAYMENT METHODS CONFIGURATION (External links handled off-bot)
# ═══════════════════════════════════════════════════════════════════════════════

# Payment website for users to select payment method
PAYMENT_WEBSITE = environ.get('PAYMENT_WEBSITE', 'https://ebookguy.vercel.app/')  # Website with payment methods

# Payment method details (provide your external payment pages/links)
PAYPAL_ID = environ.get('PAYPAL_ID', 'paypal.me/yourname')           # PayPal.me link
UPI_ID = environ.get('UPI_ID', 'your-upi-id')                        # Your UPI ID (e.g., name@bank)
CRYPTO_WALLET = environ.get('CRYPTO_WALLET', '')                     # USDT/Bitcoin address
CRYPTO_TYPE = environ.get('CRYPTO_TYPE', 'usdt')                     # usdt or bitcoin
BINANCE_PAY_ID = environ.get('BINANCE_PAY_ID', '')                   # Binance Pay ID


# ═══════════════════════════════════════════════════════════════════════════════
# ⚙️ SECTION 8: FEATURE TOGGLES (True/False)
# ═══════════════════════════════════════════════════════════════════════════════

PM_SEARCH = parse_env_bool('PM_SEARCH', True)           # Allow search in private messages
AUTO_FFILTER = parse_env_bool('AUTO_FFILTER', True)     # Auto-filter in groups
AUTO_DELETE = parse_env_bool('AUTO_DELETE', True)       # Auto-delete search results after 5 min
BUTTON_MODE = parse_env_bool('BUTTON_MODE')             # Show files as buttons (False = text-link list, True = inline buttons)
MAX_BTN = parse_env_bool('MAX_BTN', True)               # Limit buttons per page

MELCOW_NEW_USERS = parse_env_bool('MELCOW_NEW_USERS', True)    # Welcome new users in groups
PROTECT_CONTENT = parse_env_bool('PROTECT_CONTENT')            # Disable forwarding bot messages
PUBLIC_FILE_STORE = parse_env_bool('PUBLIC_FILE_STORE')        # Anyone can use file store
NO_RESULTS_MSG = parse_env_bool("NO_RESULTS_MSG", True)        # Show "no results" message
USE_CAPTION_FILTER = parse_env_bool('USE_CAPTION_FILTER', True) # Search in file captions too



# Indexing Settings
FILTER_BY_EXTENSION = parse_env_bool('FILTER_BY_EXTENSION', True)  # Only index ebooks/audiobooks
EBOOK_EXTENSIONS = environ.get('EBOOK_EXTENSIONS', 'epub pdf mobi azw azw3 djvu').split()
AUDIOBOOK_EXTENSIONS = environ.get('AUDIOBOOK_EXTENSIONS', 'mp3 m4a m4b zip rar 7z').split()
ALLOWED_EXTENSIONS = EBOOK_EXTENSIONS + AUDIOBOOK_EXTENSIONS


# ═══════════════════════════════════════════════════════════════════════════════
# 🎨 SECTION 9: APPEARANCE & MISC
# ═══════════════════════════════════════════════════════════════════════════════

# Start message picture(s) - space-separated for multiple
PICS = (environ.get('PICS', 'https://files.catbox.moe/xmntht.png')).split()

# Bot reactions when user starts
REACTIONS = ["🤝", "😇", "🤗", "😍", "👍", "🎅", "😐", "🥰", "🤩", "😱", "🤣", "😘", "👏", "😛", "😈", "🎉", "⚡️", "🫡", "🤓", "😎", "🏆", "🔥", "🤭", "🌚", "🆒", "👻", "😁"]

# Captions for files
CUSTOM_FILE_CAPTION = environ.get("CUSTOM_FILE_CAPTION", f"{script.CAPTION}")
MSG_ALRT = environ.get('MSG_ALRT', 'Hello My Dear Friends ❤️')


# ═══════════════════════════════════════════════════════════════════════════════
# 🖥️ SECTION 10: SERVER & TECHNICAL
# ═══════════════════════════════════════════════════════════════════════════════

ON_HEROKU = 'DYNO' in environ                              # Auto-detect Heroku deployment
PING_INTERVAL = int(environ.get("PING_INTERVAL", "1200"))  # Keep-alive ping interval (seconds)
PORT = int(environ.get("PORT", "8080"))                    # Web server port
URL = environ.get("URL", "http://localhost:8080/")         # Bot URL
CACHE_TIME = int(environ.get('CACHE_TIME', 1800))          # Cache duration (seconds)
MAX_B_TN = environ.get("MAX_B_TN", "5")                    # Max buttons per row
MAX_LIST_ELM = environ.get("MAX_LIST_ELM", None)           # Max list elements


# ═══════════════════════════════════════════════════════════════════════════════
# 🔧 SECTION 11: DATABASE URI ASSIGNMENT (Don't modify unless you know what you're doing)
# ═══════════════════════════════════════════════════════════════════════════════

if MULTIPLE_DATABASE == False:
    USER_DB_URI = DATABASE_URI
    OTHER_DB_URI = DATABASE_URI
    FILE_DB_URI = DATABASE_URI
    SEC_FILE_DB_URI = DATABASE_URI
else:
    USER_DB_URI = DATABASE_URI     # User data storage
    OTHER_DB_URI = O_DB_URI        # Other data storage
    FILE_DB_URI = F_DB_URI         # Primary file storage
    SEC_FILE_DB_URI = S_DB_URI     # Secondary file storage (overflow)



