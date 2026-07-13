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
Completed the modernization and organization phases. Extracted inline search, user-info, delete-channel, duplicate-maintenance, start, indexing, search presentation, database connection, filter-stat, and checkpoint responsibilities into focused modules. Plugins now contain handler registration or explicit compatibility exports. Consolidated duplicate implementations, removed wildcard and unused imports, restored corrupted search regexes and user-facing replacement characters, and preserved legacy positional APIs through request-object adapters.

Verification: all 98 Python files compile under Python 3.13; no file is 300 lines or larger; no function exceeds 50 lines or three parameters; no wildcard or unused imports, duplicate function bodies, broad exceptions, production prints, control characters, or suspect source encodings remain. Targeted smoke tests cover search/pagination, start routing, indexing state, iterator batching, compatibility adapters, search regexes, checkpoint exports, and callback payloads.

## In Progress
None.

## Pending
- Commit the completed refactor when the user is ready.
- Run a live Telegram smoke test in the deployed environment before release.
## Known Issues
- No repository test suite or CI workflow was found; verification uses compile/static gates and isolated behavior smoke tests.
- Retained dormant, unreferenced compatibility code: `database/connections_mdb.py:add_connection`, `EbookGuy/util/custom_dl.py:ByteStreamer`, and `EbookGuy/util/render_template.py:render_page`.
- Watermark/attribution identifiers retained for compatibility or branding: `EbookGuy`, `EbookGuyXBot`, `EbookGuyBot`, `MELCOW_NEW_USERS`, and `MELCOW`. The dormant `req.html` template also contains `Tech_VJ`, `VJ_Bots`, and `KingVJ01`; `custom_dl.py` credits `Eyaadh` in documentation. No generated filename watermark remains.
- Compile verification generated ignored `__pycache__/` files.

## Files Status
- Created: focused search, download, indexing, admin, shared, and database modules, including `inline_queries.py`, `models.py`, `pagination.py`, `rendering.py`, `start_views.py`, `start_delivery.py`, `force_subscription.py`, `progress.py`, `user_info.py`, `file_cleanup.py`, `file_collections.py`, `filter_stats.py`, and `indexing_checkpoints.py`.
- Moved: plugin implementation modules from `plugins/` into their matching `EbookGuy/features/*` folders; root `utils_*` modules into `EbookGuy/shared/`.
- Modified: `plugins/commands.py`, `plugins/commands_downloads.py`, `plugins/index.py`, `plugins/pm_filter_callbacks.py`, `plugins/pm_filter_filtering.py`, `plugins/pm_filter_search.py`, `plugins/premium.py`, `plugins/banned.py`, `utils.py`, moved implementation modules with updated import paths, `EbookGuy/features/search/results.py`, `EbookGuy/features/downloads/start.py`, `EbookGuy/features/filters/manual.py`, `EbookGuy/features/filters/global_filters.py`, `EbookGuy/features/filters/premium_callbacks.py`, `EbookGuy/features/indexing/moderation.py`, `EbookGuy/features/indexing/requests.py`, `EbookGuy/shared/filter_parser.py`, `info.py`, and `HANDOFF.md`.
- Currently Being Edited: none.
- Planned to Edit: none.
- Untouched dependencies/deployment: `requirements.txt` and `Dockerfile`.
