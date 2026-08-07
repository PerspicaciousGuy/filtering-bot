# EbookGuy Filtering Bot

A private Telegram filtering bot for searching, requesting, downloading, and
converting ebooks and audiobooks. It includes administrator-controlled runtime
settings, download limits, Telegram Stars subscriptions, analytics, channel
indexing, and Docker deployment.

## Features

### Search and delivery

- Private-chat ebook and audiobook search
- Paginated results with configurable result limits and expiry
- Search suggestions, trending searches, and caption filtering
- Configurable free and Premium download limits
- Configurable file-size limits, cooldowns, content protection, and auto-delete
- Premium EPUB, PDF, and MOBI conversion through Calibre
- Force-subscription checks for one or more Telegram channels

### Administration

- `/settings` dashboard for limits, channels, search, delivery, requests,
  Premium, manual payment destinations, messages, analytics, and operational
  controls
- Versioned JSON settings backup, validated restore preview, and confirmed
  restore from the `/settings` dashboard
- File-channel indexing with checkpoint and resume support
- File deletion and duplicate detection
- User broadcasts and direct admin messages
- Book request workflow with Processing, Uploaded, Already Available, and
  Unavailable statuses
- Runtime analytics for users, searches, downloads, requests, conversions, and
  Telegram Stars payments

### Payments

- Native Telegram Stars invoices
- Price, user, currency, and payload validation during checkout
- Durable, idempotent Premium activation
- Google Pay / UPI details with a safe unsupported-link fallback
- Direct Binance Pay links
- Manual proof instructions for externally completed payments
- Optional external payment portal fallback
- Admin commands for manual Premium activation and transaction inspection

See [PAYMENTS.md](PAYMENTS.md) for the complete payment flow.

## Requirements

- Python 3.10
- MongoDB
- Telegram API credentials from `my.telegram.org`
- A bot token from BotFather
- Calibre and its `ebook-convert` command for format conversion

Docker installs Calibre automatically. Local installations must provide
`ebook-convert` on `PATH` before conversion can work.

## Configuration

Copy `.env.example` to `.env` and replace the placeholder values.

The following variables are required:

| Variable | Purpose |
| --- | --- |
| `API_ID` | Telegram API application ID |
| `API_HASH` | Telegram API application hash |
| `BOT_TOKEN` | BotFather token |
| `DATABASE_URI` | MongoDB connection string |
| `ADMINS` | Space-separated Telegram user IDs allowed to administer the bot |

Important optional variables include:

| Variable | Purpose |
| --- | --- |
| `LOG_CHANNEL` | Restart, user, and operational log destination |
| `CHANNELS` | Telegram channels indexed for files |
| `AUTH_CHANNEL` | Force-subscription channel |
| `REQST_CHANNEL` | Book request destination |
| `PAYMENT_WEBSITE` | External payment portal shown alongside Telegram Stars |
| `PORT` | HTTP health server port, default `8080` |
| `MULTIPLE_DATABASE` | Enable separate MongoDB connections |

Use `.env.example` as the complete environment-variable reference. Never commit
`.env`, MongoDB credentials, bot tokens, or Pyrogram `.session` files.

Administrators can change most operational values through `/settings`. These
overrides are stored in MongoDB and take precedence over environment defaults.

## Local Development

### Windows PowerShell

```powershell
py -3.10 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --requirement requirements.lock
Copy-Item .env.example .env
python bot.py
```

### Linux or macOS

```bash
python3.10 -m venv .venv
source .venv/bin/activate
python -m pip install --requirement requirements.lock
cp .env.example .env
python bot.py
```

The service is ready when `GET /ready` returns HTTP `200`.

## Deployment

The production image:

- Uses Python 3.10
- Installs the exact versions in `requirements.lock`
- Runs as a non-root user
- Keeps the Telegram session in memory
- Exposes liveness and readiness endpoints
- Stops background tasks and Telegram clients during shutdown

```bash
docker build -t filtering-bot .
docker run --detach \
  --name filtering-bot \
  --publish 8080:8080 \
  --env-file .env \
  filtering-bot
```

See [DEPLOYMENT.md](DEPLOYMENT.md) for production configuration, CI, health
checks, secret rotation, and the deployment checklist.

## Health Endpoints

| Endpoint | Meaning |
| --- | --- |
| `/health` | Process is running |
| `/ready` | Telegram and required startup initialization completed |

Load balancers and container platforms should use `/ready` for readiness
checks. The Docker image already defines this health check.

## Commands

### Users

| Command | Description |
| --- | --- |
| `/start` | Open the bot and begin searching |
| `/plan` | View Premium plans and payment methods |
| `/mystatus` | View Premium status and remaining usage |
| `/request Title \| Author` | Submit a book request |
| `/trending_now` | View recent trending searches |
| `/id` | Display the user's Telegram ID |
| `/info` | Display Telegram account information |
| `/alive` | Check whether the bot is running |
| `/ping` | Measure bot response time |

### Administrators

| Command | Description |
| --- | --- |
| `/settings` | Manage global runtime settings and analytics |
| `/stats` | Display current bot and database statistics |
| `/broadcast` | Broadcast a replied message to users |
| `/send` | Send a message to a specific user |
| `/logs` | Retrieve current runtime logs |
| `/restart` | Restart the bot process |
| `/addpremium <user_id> <days>` | Grant or extend Premium manually |
| `/removepremium <user_id>` | Remove Premium |
| `/premiumusers` | List Premium users |
| `/stars` | Display the bot's Telegram Stars balance |
| `/starhistory [limit]` | Display recorded Stars transactions |

### File management

| Command | Description |
| --- | --- |
| `/index` | Index messages from a Telegram channel |
| `/resume` | Resume an interrupted indexing operation |
| `/setskip` | Configure indexing skip behavior |
| `/delete` | Delete one indexed file |
| `/deleteall` | Delete all indexed files after confirmation |
| `/deletefiles` | Delete files matching the cleanup workflow |
| `/duplicates` | Find duplicate indexed files |
| `/channel` | List configured indexed channels |

## Project Structure

| Path | Responsibility |
| --- | --- |
| `plugins/` | Pyrogram handler registration |
| `EbookGuy/features/` | Search, downloads, requests, Premium, indexing, and admin behavior |
| `EbookGuy/shared/` | Shared settings, parsing, delivery, analytics, and state |
| `EbookGuy/bot/` | Telegram client initialization |
| `EbookGuy/util/` | Infrastructure utilities |
| `database/` | MongoDB collections and persistence services |
| `tests/` | Regression tests |
| `.github/workflows/ci.yml` | Dependency, test, credential, and image checks |

## Verification

```bash
python -m compileall -q bot.py Script.py utils.py EbookGuy database plugins tests
python -m unittest discover -s tests -v
python -m pip check
```

CI additionally audits locked dependencies, rejects tracked credentials, and
builds the Docker image.

## License

MIT License.
