class script(object):
    LOGO = """
Filter Bot
"""

    BTN_LABEL_1 = "🔥 Our Main Channel 🔥"
    BTN_LABEL_2 = "📚 How to Search Book Properly"
    BTN_LABEL_3 = "🔥 Fat Burning Kitchen"
    BTN_LABEL_4 = "💖 His Secret Obsession"

    # Contact Information
    OWNER = "Justinnix"  # Change to your Telegram username
    SUPPORT_USERNAME = "Justinnix"  # Change to your support username

    RESTART_TXT = """
<b>Bot Restarted!</b>
<b>Date:</b> {}
<b>Time:</b> {}
"""

    START_TXT = """<b>👋 Hello {},</b>

Welcome to your personal <b>Digital Library</b> 📚.

I can help you find <b>E-Books</b> and <b>Audiobooks</b> in seconds.
📦 <b>Library:</b> {}+ books & audiobooks

<b>🚀 How to use me:</b>
Simply type the <b>Book Name</b> or <b>Author Name</b> and I will search my library for you.

🆓 Free users get <b>1 download/day</b>. Use /plan for unlimited access.

<i>👇 Join our channels for updates & support.</i>"""



    CAPTION = """<b>File Name:</b> {filename}
<b>Size:</b> {filesize}
<b>Duration:</b> {duration}"""

    MELCOW_ENG = """<b>👋 Hello {},\n\nWelcome to {} 📚.\n\nI can help you find E-Books and Audiobooks in seconds.</b>"""

    LOG_TEXT_G = """#NewGroup
Group = {}(<code>{}</code>)
Total Members = <code>{}</code>
Added By - {}"""

    LOG_TEXT_P = """#NewUser
ID - <code>{}</code>
Name - {}"""

    ALRT_TXT = """Hello {},
This is not your request,
Request yours..."""

    OLD_ALRT_TXT = """Hey {},
You are using one of my old messages, 
Please send the request again."""

    MVE_NT_FND = "I couldn't find any book/audiobook with that name."
    TOP_ALRT_MSG = "Checking for results..."
    PLEASE_WAIT = "<b>Please wait...</b>"
    UNABLE_TO_OPEN_FILE = "UNABLE TO OPEN FILE."
    INVALID_LINK = "<b>Invalid link or expired link</b>"
    NO_FILE_EXIST = "<b><i>No such file exist.</b></i>"
    SEARCH_AGAIN = "<b>Please Search Again in Group</b>"
    GET_FILE_AGAIN = "✅ Get File Again ✅"
    IMPORTANT_DELETE_MSG = "<blockquote><b><u>❗️❗️❗️IMPORTANT❗️️❗️❗️</u></b>\n\nThis message will be deleted in <b><u>10 mins</u> 🫥 <i></b>(due to copyright issues)</i>.\n\n<b><i>Please forward this message to your saved messages or any private chat.</i></b></blockquote>"
    FILE_DELETED_BTN = "<b>✅ File Deleted, If you want the file CLick on below button.</b>"
    MSG_DELETED = "<b>✅ Your message is successfully deleted</b>"
    
    BACKUP_CHANNEL_NOT_JOINED = "**🕵️ You have not joined my backup channel. First join channel then try again**"
    BACKUP_CHANNEL_NOT_JOINED_2 = "**🕵️ You have not joined my backup channel. First join channel**"
    FORCE_SUB_ADMIN_ERROR = "Make sure Bot is admin in Forcesub channel"
    FORCE_SUB_ERROR = "something wrong with force subscribe."
    BACKUP_CHANNEL_BTN = "Backup Channel"
    TRY_AGAIN_BTN = "↻ Try Again"
    
    NO_RESULTS_MSG = """<b>❌ No Results Found</b>

We couldn't find <b>"{}"</b> in our Library.

<b>👇 Try these steps:</b>
1. Check spelling on <a href="https://www.google.com/search?q={}+book">Google</a>.
2. Search for the <b>Author</b> instead.
3. Still can't find it? Type <code>/request {}</code> with book name & author to notify admins."""

    # Premium System Messages
    LIMIT_REACHED = """<b>❌ Daily Limit Reached!</b>

You've used all your <b>{}</b> free downloads for today.

<b>⭐ Upgrade to Premium for:</b>
✅ Unlimited downloads
✅ No daily limits
✅ Direct access to all files

<i>Your limit resets at midnight.</i>"""

    DOWNLOAD_COUNT = "📥 Downloaded ({}/{})"
    DOWNLOAD_COUNT_PREMIUM = "📥 Downloaded (Premium ∞)"

    # Payment Methods Messages
    PAYMENT_METHODS = """<b>💳 Select Payment Method</b>

Choose your preferred way to purchase Premium:"""

    PAYPAL_PAYMENT = """<b>💳 PayPal Payment</b>

Your PayPal ID: <code>{paypal_id}</code>

<b>Instructions:</b>
1. Send payment to the PayPal ID above
2. Include your User ID: <code>{user_id}</code>
3. Screenshot the transaction
4. Forward to support with your User ID

<i>Your premium will be activated within 24 hours of verification.</i>"""

    UPI_PAYMENT = """<b>🏦 UPI Payment</b>

Your UPI ID: <code>{upi_id}</code>

<b>Instructions:</b>
1. Open your UPI app and send payment
2. Use your User ID as reference: <code>{user_id}</code>
3. Forward the receipt to support
4. Include your User ID

<i>Your premium will be activated within 24 hours of verification.</i>"""

    CRYPTO_PAYMENT = """<b>₿ Cryptocurrency Payment</b>

💰 <b>Wallet Address ({crypto_type}):</b>
<code>{wallet_address}</code>

<b>Instructions:</b>
1. Send {crypto_type} to the wallet above
2. Use your User ID as reference: <code>{user_id}</code>
3. Forward the transaction hash to support

<i>Your premium will be activated within 24 hours of verification.</i>"""

    REQ_UPLOADED = """<b>Great news {}! 📚</b>

The book you requested has been added to our <b>Digital Library</b>.

<i>You can now search for it directly in this bot!</i>"""

    REQ_UNAVAILABLE = """<b>Hello {}, 😔</b>

We searched everywhere, but unfortunately, this book is currently unavailable in our archives.

<i>We will keep looking and update it if we find it!</i>"""

    REQ_ALREADY_EXIST = """<b>Hello {}! 📖</b>

Good news! This book is already available in our <b>Digital Library</b>.

<i>Please search for it again here in the bot.</i>"""

    REQ_PROCESSING = """<b>Hello {}, ⏳</b>

Your request has been received by our librarians.

<i>We are currently processing it and will notify you once it's added to the shelves!</i>"""