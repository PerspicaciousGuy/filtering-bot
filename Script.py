class script(object):
    LOGO = """
Filter Bot
"""


    # Contact Information

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



    LOG_TEXT_P = """#NewUser
ID - <code>{}</code>
Name - {}"""

    ALRT_TXT = """Hello {},
This is not your request,
Request yours..."""

    OLD_ALRT_TXT = """Hey {},
You are using one of my old messages, 
Please send the request again."""

    NO_FILE_EXIST = "<b><i>No such file exist.</b></i>"
    GET_FILE_AGAIN = "✅ Get File Again ✅"
    IMPORTANT_DELETE_MSG = "<blockquote><b><u>❗️❗️❗️IMPORTANT❗️️❗️❗️</u></b>\n\nThis message will be deleted in <b><u>10 mins</u> 🫥 <i></b>(due to copyright issues)</i>.\n\n<b><i>Please forward this message to your saved messages or any private chat.</i></b></blockquote>"
    FILE_DELETED_BTN = "<b>✅ File Deleted, If you want the file CLick on below button.</b>"
    
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

    DOWNLOAD_COUNT = "📥 Downloaded ({}/{})"
    DOWNLOAD_COUNT_PREMIUM = "📥 Downloaded (Premium ∞)"

    # Payment Methods Messages




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