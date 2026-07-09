# AI Coding Agent Instructions for EbookGuy Bot

## Project Overview

**EbookGuy** is a Telegram bot for distributing ebooks and audiobooks with premium monetization via Telegram Stars. It uses:
- **Pyrogram** (Pyrogram fork) for Telegram integration
- **MongoDB** for file indexing and user data persistence
- **Motor** async MongoDB driver
- **Plugin system** for modular command handlers
- **Multi-client support** for load balancing across multiple bot instances

## Architecture & Key Components

### 1. Core Bot Structure (`bot.py`, `EbookGuy/bot/clients.py`)
- **Single Entry Point**: `bot.py` loads plugins from `plugins/*.py` and initializes the Pyrogram client
- **Multi-Client Patterns**: `EbookGuy/bot/clients.py` manages load-balanced bot instances with workload tracking in `work_loads` dict
- **Clients Registry**: `multi_clients` dict stores active client instances by ID; client 0 is always the default bot
- **Web Server**: Built-in aiohttp server on `PORT` for Heroku keepalive (see `EbookGuy/util/keepalive.py`)

### 2. Configuration Hierarchy
- **`info.py`**: All environment variables, API keys, channel IDs, premium pricing, DB URIs - read first for any config question
- **`Script.py`**: All user-facing text messages (multilingual support possible via imports)
- **`logging.conf`**: Logging configuration (suppresses Pyrogram/cinemagoer logs)
- **Pattern**: Settings should go in `info.py` sections (marked with emoji headers), text goes in `Script.py`

### 3. Database Layer (`database/`)
- **`users_chats_db.py`**: Async MongoDB via Motor - user info, groups, premium status, daily download limits
- **`ia_filterdb.py`**: File indexing/search using MongoDB text indexes and file collections
- **`connections_mdb.py`**: Connection management between users and channels
- **`filters_mdb.py`, `gfilters_mdb.py`**: Custom and global filters for search
- **`join_reqs.py`**: Join request tracking for force-subscribe channels
- **Pattern**: All DB methods are async (`async def`), use `motor.motor_asyncio` for I/O; see `Database` class pattern in `users_chats_db.py`

### 4. Plugin System (`plugins/`)
- **Auto-loading**: `bot.py` loads all `.py` files from `plugins/` directory on startup
- **Disabled Plugins**: Use `.disabled` suffix to exclude files (e.g., `filters.py.disabled`)
- **Handler Pattern**: Each plugin registers Pyrogram handlers using `@EbookGuyBot.on_message()` or `@EbookGuyBot.on_callback_query()` decorators
- **Key Plugins**:
  - `commands.py`: All `/start`, `/premium`, `/stats` commands with download limit checking (see `check_and_increment_download()`)
  - `pm_filter.py`: Private message filtering and file search results
  - `channel.py`: Channel file indexing when messages arrive in monitored channels
  - `premium.py`: Star payment handling and premium subscription logic
  - `broadcast.py`: Admin broadcast to users/groups
  - `Extra/`: Utility functions like alive check, repo info

### 5. Utility Modules (`EbookGuy/util/`)
- **`config_parser.py`**: Parses environment variables for multi-client bot tokens (via `TokenParser`)
- **`file_properties.py`**: Gets file name, hash, and size from Telegram documents
- **`human_readable.py`**: Formats file sizes for display (e.g., "1.5 MB")
- **`render_template.py`**: Jinja2 template rendering for web (uses `template/` HTML files)
- **`keepalive.py`**: Pings web server to keep bot alive on Heroku

## Critical Developer Workflows

### Running the Bot Locally
```bash
# Set environment variables (see info.py sections)
export BOT_TOKEN="..." API_ID="..." API_HASH="..." DATABASE_URI="..."
python bot.py
```

### Deploying to Heroku/Docker
```bash
docker build -t ebookguy-bot .
docker run -d -p 8080:8080 --env-file .env ebookguy-bot
```
- Uses `Procfile` for Heroku process definition
- `heroku.yml` for Heroku container deployment
- Non-root user in `Dockerfile` for security

### Testing Premium/Download Limits
- Use `check_and_increment_download()` in `plugins/commands.py` to verify premium status (via `db.get_premium_status()`) or free limit (via `db.get_daily_downloads()`)
- Test auto-delete via `send_auto_delete_message()` helper

### Adding a New Command
1. Create new handler in `plugins/commands.py` or new plugin file
2. Use `@EbookGuyBot.on_message(filters.command("mycommand"))` decorator
3. Access config from `info.py` imports, text from `Script.py`
4. Use async DB methods from `database/` modules
5. Send responses via `client.send_message()` or `callback_query.edit_message_text()`

## Project-Specific Patterns & Conventions

### Download Limit & Premium Logic
- **Free Users**: Limited to `FREE_DAILY_LIMIT` downloads per 24h (tracked in MongoDB per user per day)
- **Premium Users**: Unlimited downloads if premium not expired
- **Always Check**: Call `check_and_increment_download(user_id)` before sending files; returns `(can_download, is_premium, count)`
- **Auto-Delete**: Sent files auto-delete after 10 minutes via `send_auto_delete_message()` to comply with copyright

### Force Subscribe (Request-to-Join Mode)
- **`AUTH_CHANNEL`**: Users must join this channel to use bot
- **`REQUEST_TO_JOIN_MODE`**: If True, users send join requests instead of joining directly
- **`TRY_AGAIN_BTN`**: Show retry button after user joins
- **Check**: Use `pub_is_subscribed()` utility in `utils.py` for validation

### Temp Data Storage
- **`temp` class in `utils.py`**: Global in-memory storage for session data (BANNED_USERS, BOT, SETTINGS, etc.)
- **Pattern**: Use sparingly; prefer MongoDB for persistence, temp for request-scoped data only

### Multi-Client Load Balancing
- **`work_loads[client_id]`**: Tracks requests per client; use lowest load client for file operations
- **`multi_clients[0]`**: Always the default bot; additional clients have IDs 1, 2, etc.
- **Pattern**: Check `len(multi_clients)` > 1 to detect multi-client mode

### Button/Markup Convention
- **`BTN_URL_REGEX`** in `utils.py` parses markdown-style buttons: `[Label](buttonurl://URL)`
- **Inline Buttons**: Use `InlineKeyboardButton` + `InlineKeyboardMarkup` from Pyrogram
- **Max Buttons**: Respect `MAX_B_TN` from `info.py` to avoid Telegram limits

## Key Files & Their Roles

| File | Purpose |
|------|---------|
| [info.py](info.py) | **Central config**: API keys, channels, DB URI, premium prices |
| [Script.py](Script.py) | **All user messages**: Edit for language/tone changes |
| [bot.py](bot.py) | **Entry point**: Initializes bot, loads plugins, starts web server |
| [utils.py](utils.py) | **Core helpers**: Subscription check, button parsing, ban management |
| [plugins/commands.py](plugins/commands.py) | **Main handlers**: /start, /premium, /stats, file search |
| [database/users_chats_db.py](database/users_chats_db.py) | **User data**: Persistent MongoDB storage via Motor async driver |
| [database/ia_filterdb.py](database/ia_filterdb.py) | **File indexing**: Searches and retrieves files from channels |
| [EbookGuy/bot/clients.py](EbookGuy/bot/clients.py) | **Multi-client mgmt**: Initializes additional bot instances for load balancing |

## External Dependencies & Integration Points

- **Pyrogram**: Telegram API (pyrofork variant); use async/await patterns throughout
- **MongoDB + Motor**: Async driver required; all DB methods are `async def`
- **Telegram Stars**: Native payment via `Client.send_invoice()` (handled in `premium.py`)
- **Heroku Deployment**: Set `ON_HEROKU` env var to enable keepalive pinging
- **YouTube Integration**: Partial support via `youtube-dl`, `youtube_search` (check `plugins/` for usage)
- **OpenAI API**: Available in requirements; not yet actively used in core plugins

## Common Gotchas & Important Notes

1. **Async/Await**: All I/O is async (DB, Telegram API); use `await` for all Motor operations and Pyrogram methods
2. **Environment Variables**: Bot won't start without `API_ID`, `API_HASH`, `BOT_TOKEN`, `DATABASE_URI`; see `info.py` parsing
3. **Plugin Loading Order**: Plugins load in glob order; naming matters for load priority
4. **MongoDB Indexes**: File search relies on text indexes created in `ia_filterdb`; check for index errors if search fails
5. **Workload Tracking**: Multi-client mode requires manual `work_loads` updates; don't forget to decrement after request completes
6. **Copyright Auto-Delete**: Feature is non-negotiable; files must delete after 10 min regardless of user request
