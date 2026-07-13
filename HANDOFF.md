# HANDOFF

## Project Overview
EbookGuy is a Python Telegram bot for searching, downloading, indexing, and converting ebooks/audiobooks with premium access via Telegram Stars and external payment links. It uses Pyrogram/pyrofork, MongoDB/Motor, plugin-based handlers, and an aiohttp keepalive server.

## Current State
The planned split, modernization, duplication cleanup, dead-code audit, organization, watermark audit, and validation phases are complete. Thin Pyrogram plugin/decorator entrypoints remain in `plugins/`, because `bot.py` loads `plugins/*.py`. Extracted implementation code now lives in domain folders under `EbookGuy/features/`, shared utility code lives under `EbookGuy/shared/`, and public compatibility barrels preserve existing import surfaces.

Current domain layout:
- `EbookGuy/features/search/` - search state, format selection, and result rendering.
- `EbookGuy/features/filters/` - manual/global filters and callback families.
- `EbookGuy/features/downloads/` - start flow, download limits, download callbacks, and conversion.
- `EbookGuy/features/premium/` - premium views, payments, and admin commands.
- `EbookGuy/features/indexing/` - indexing worker, moderation, request intake, and admin resume/delete flows.
- `EbookGuy/features/admin/` - admin command implementations.
- `EbookGuy/features/requests/` - request command implementation.
- `EbookGuy/shared/` - state, subscriptions, broadcast, settings, formatting, message helpers, filter parser, and delivery helpers.

The local repository is on branch `main`, tracks `origin/main`, and local-only `AGENTS.md` / `agents-guidelines/` should remain ignored and untracked.

## Last Action
Audited `/settings` command availability. No Pyrogram command handler, alias, dynamic bot-command registration, or runtime log entry exists for `/settings`, so the bot does not currently respond to it. Settings persistence and helper modules are used internally by filtering, delivery, search pagination, secure-file behavior, and auto-delete behavior, but there is no user-facing settings command.

## In Progress
Callback latency measurement and safe early-acknowledgment optimization.

## Pending
- Commit the completed refactor when the user is ready.
- Move safe callback acknowledgments earlier based on measured handlers.
- Exercise core Telegram commands against the optimized bot.
- Run a live Telegram smoke test in the deployed environment before release.
## Known Issues
- `/settings` has no registered command handler, so it currently produces no bot response.
- No repository test suite or CI workflow was found; verification uses compile/static gates and isolated behavior smoke tests.
- Docker is unavailable; local execution uses the isolated temporary Python 3.10 environment.
- Retained dormant, unreferenced compatibility code: `database/connections_mdb.py:add_connection`, `EbookGuy/util/custom_dl.py:ByteStreamer`, and `EbookGuy/util/render_template.py:render_page`.
- Watermark/attribution identifiers retained for compatibility or branding: `EbookGuy`, `EbookGuyXBot`, `EbookGuyBot`, `MELCOW_NEW_USERS`, and `MELCOW`. The dormant `req.html` template also contains `Tech_VJ`, `VJ_Bots`, and `KingVJ01`; `custom_dl.py` credits `Eyaadh` in documentation. No generated filename watermark remains.
- Compile verification generated ignored `__pycache__/` files.

## Files Status
- Created: focused search, download, indexing, admin, shared, and database modules, including `inline_queries.py`, `models.py`, `pagination.py`, `rendering.py`, `start_views.py`, `start_delivery.py`, `force_subscription.py`, `progress.py`, `user_info.py`, `file_cleanup.py`, `file_collections.py`, `filter_stats.py`, and `indexing_checkpoints.py`.
- Moved: plugin implementation modules from `plugins/` into their matching `EbookGuy/features/*` folders; root `utils_*` modules into `EbookGuy/shared/`.
- Modified: `plugins/commands.py`, `plugins/commands_downloads.py`, `plugins/index.py`, `plugins/pm_filter_callbacks.py`, `plugins/pm_filter_filtering.py`, `plugins/pm_filter_search.py`, `plugins/premium.py`, `plugins/banned.py`, `utils.py`, moved implementation modules with updated import paths, `EbookGuy/features/search/results.py`, `EbookGuy/features/downloads/start.py`, `EbookGuy/features/filters/manual.py`, `EbookGuy/features/filters/global_filters.py`, `EbookGuy/features/filters/premium_callbacks.py`, `EbookGuy/features/indexing/moderation.py`, `EbookGuy/features/indexing/requests.py`, `EbookGuy/shared/filter_parser.py`, `info.py`, and `HANDOFF.md`.
- Currently Being Edited: callback instrumentation and optimization modules.
- Planned to Edit: measured slow callback handlers and `HANDOFF.md`.
- Untouched dependencies/deployment: `requirements.txt` and `Dockerfile`.
