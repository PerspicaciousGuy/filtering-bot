# HANDOFF

## Project Overview
EbookGuy is a Python Telegram bot for searching, downloading, indexing, and converting ebooks/audiobooks with premium access via Telegram Stars and external payment links. It uses Pyrogram/pyrofork, MongoDB/Motor, plugin-based handlers, and an aiohttp keepalive server.

## Current State
The split phase is complete and the first organization pass is complete. Thin Pyrogram plugin/decorator entrypoints remain in `plugins/`, because `bot.py` loads `plugins/*.py`. Extracted implementation code now lives in domain folders under `EbookGuy/features/`, shared utility code lives under `EbookGuy/shared/`, and the public compatibility barrels (`utils.py`, `plugins/pm_filter_search.py`, `plugins/pm_filter_filtering.py`, `plugins/commands_downloads.py`) preserve existing import surfaces.

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
Organized extracted implementation files out of `plugins/` into domain folders while preserving plugin loader behavior:
- Moved search/filter/download/premium/indexing/admin/request implementation modules into `EbookGuy/features/*`.
- Moved root `utils_*` implementation modules into `EbookGuy/shared/`.
- Added `__init__.py` files for the new packages.
- Updated imports in plugin entrypoints, compatibility barrels, and moved implementation modules.
- Kept thin plugin-facing files in `plugins/` so `bot.py` can continue loading `plugins/*.py`.

Verification completed with `python -m compileall -q .`. Stale imports to moved plugin implementation modules were searched and none were found.

## In Progress
No active file edit is in progress.

## Pending
- Run a final manual review of known preserved issues before making behavior changes.
- Add characterization tests or lightweight smoke checks before fixing behavior-sensitive bugs.
- Consider later internal function-level cleanup for modules that are under 300 lines but still have large functions, such as `EbookGuy/features/search/results.py`, `EbookGuy/features/downloads/start.py`, and `EbookGuy/features/indexing/worker.py`.

## Known Issues
- No test suite or CI workflow was found, so refactors are currently verified only by compile/static checks.
- `EbookGuy/features/filters/premium_callbacks.py` preserves callback references to premium functions that do not appear to exist in `plugins/premium.py`.
- `EbookGuy/features/search/results.py` preserves the pre-existing missing `save_group_settings` import path from the original search module.
- `EbookGuy/features/downloads/start.py` preserves the pre-existing `base64` reference without a local import from the original download command module.
- `EbookGuy/features/filters/manual.py` and `EbookGuy/features/filters/global_filters.py` still contain the pre-existing `eval(btn)` pattern from the original filtering code.
- `EbookGuy/features/filters/manual.py` and `EbookGuy/features/filters/global_filters.py` preserve pre-existing references to `asyncio` and `save_group_settings` without local imports.
- `EbookGuy/features/indexing/worker.py` preserves the original large `index_files_to_db` function, including broad exception handling and recursive resume behavior during FloodWait handling.
- `EbookGuy/features/indexing/requests.py` preserves the original non-admin public-username link path that reads `message.forward_from_chat.username` even when the request came from typed text.
- Several modules still use broad `except` blocks and `print()` logging.
- `info.py` uses `bool(environ.get(...))`, which treats string values like `False` as true.
- Some async database functions still call synchronous PyMongo operations directly.
- Compile verification generated ignored `__pycache__/` files.

## Files Status
- Created: `EbookGuy/features/__init__.py`, `EbookGuy/features/search/`, `EbookGuy/features/filters/`, `EbookGuy/features/downloads/`, `EbookGuy/features/premium/`, `EbookGuy/features/indexing/`, `EbookGuy/features/admin/`, `EbookGuy/features/requests/`, `EbookGuy/shared/`, and package `__init__.py` files inside each new folder.
- Moved: plugin implementation modules from `plugins/` into their matching `EbookGuy/features/*` folders; root `utils_*` modules into `EbookGuy/shared/`.
- Modified: `plugins/commands.py`, `plugins/commands_downloads.py`, `plugins/index.py`, `plugins/pm_filter_callbacks.py`, `plugins/pm_filter_filtering.py`, `plugins/pm_filter_search.py`, `plugins/premium.py`, `utils.py`, moved implementation modules with updated import paths, and `HANDOFF.md`.
- Currently Being Edited: none.
- Planned to Edit: none until the next approved phase.
- Untouched: `bot.py`, `database/ia_filterdb.py`, `database/users_chats_db.py`, `info.py`, `requirements.txt`, `Dockerfile`, `README.md`.
