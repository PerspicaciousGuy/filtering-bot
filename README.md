# EbookGuy Bot — v1.2

A private Telegram bot for searching, downloading, and converting ebooks and audiobooks with premium monetization via Telegram Stars.

## 📋 Changelog

### v1.2
- **Format Conversion** (Premium): Convert EPUB, PDF, and MOBI files between each other directly in the bot via Calibre. 3 conversions/day for premium users.
- **Smarter Search**: Progressive word-drop fallback — if a search returns no results, the bot automatically retries with shorter queries.
- **Live Stats**: `/stats` command tracks total users, library size, and daily downloads in real time.
- **Codebase Cleanup**: Removed ~280 lines of dead code and 27 unused pip packages. Fixed `/delete` admin command crash.

### v1.1
- Text-link search results (no inline buttons)
- Deep link prefix fix
- Pagination caption cleanup

---

## 🚀 Features

### Core
- **Private bot**: 1-on-1 experience, no group spam
- **Format selection**: Choose Ebook or Audiobook before searching
- **Smart search**: Pagination + progressive word-drop fallback for author name queries
- **Auto-delete**: Files deleted after 10 minutes (copyright compliance)
- **Force subscribe**: Require channel membership before access

### Premium (Telegram Stars ⭐)
- **1 free download/day** for free users
- **20 downloads/day** for premium users (30s cooldown between downloads)
- **3 format conversions/day** — EPUB ↔ PDF ↔ MOBI via Calibre
- **Telegram Stars payment**: Native in-app, no external gateways
- **UPI/PayPal support**: External payment option with INR pricing

### Admin & Library
- **Smart indexing**: Index files from channels with checkpoint/resume
- **Broadcast**: Message all users or groups
- **Duplicate detection**: Find duplicate files in the database
- **Multi-client support**: Load balance across multiple bot instances

### Security & Deployment
- Docker container runs as non-root user
- Koyeb/Heroku/Docker ready

---

## 🛠 Configuration

| File | Purpose |
|------|---------|
| `info.py` | API keys, DB URLs, channel IDs, pricing |
| `Script.py` | All user-facing text — edit for tone/language |

### Premium Pricing
```python
FREE_DAILY_LIMIT = 1          # Free downloads per day
PREMIUM_DAILY_LIMIT = 20      # Premium downloads per day
PREMIUM_DOWNLOAD_COOLDOWN = 30  # Seconds between downloads

PREMIUM_PRICES = {
    30: 100,   # 30 Days — 100 Stars (~$1.99)
    90: 250,   # 90 Days — 250 Stars (~$4.99)
}

PREMIUM_PRICES_INR = {
    30: 150,   # 30 Days — ₹150
    90: 350,   # 90 Days — ₹350
}
```

---

## 🐳 Deployment

```bash
# Build
docker build -t ebookguy-bot .

# Run
docker run -d -p 8080:8080 --env-file .env ebookguy-bot
```

---

## 🤖 Commands

### User
| Command | Description |
|---------|-------------|
| `/start` | Start the bot, choose format |
| `/premium` | View plans and subscribe |
| `/mystatus` | Check premium status and remaining downloads |
| `/id` | Get your Telegram ID |
| `/info` | Get user info |

### Admin
| Command | Description |
|---------|-------------|
| `/stats` | Live stats: users, library, downloads, DB size |
| `/broadcast` | Broadcast to all users |
| `/grp_broadcast` | Broadcast to all groups |
| `/ban` / `/unban` | Manage user access |
| `/addpremium <id> <days>` | Gift premium |
| `/removepremium <id>` | Remove premium |
| `/premiumusers` | List premium subscribers |
| `/stars` | Bot Star balance |
| `/starhistory [limit]` | Star transaction history |
| `/logs` | Recent error logs |

### Indexing
| Command | Description |
|---------|-------------|
| `/index` | Index files from a channel |
| `/delete` | Delete a specific file from DB |
| `/deleteall` | Delete all indexed files |
| `/deletebyquery` | Delete files matching a query |
| `/find_duplicates` | Find duplicate files |

---

## 💎 Premium Benefits

| Feature | Free | Premium |
|---------|------|---------|
| Daily downloads | 1/day | 20/day |
| Download cooldown | — | 30s between downloads |
| Format conversion | ❌ | ✅ 3/day (EPUB ↔ PDF ↔ MOBI) |
| File access | All files | All files |

---

## 📝 License

MIT License.
