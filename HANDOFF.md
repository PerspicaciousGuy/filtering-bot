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
Completed the second exception-cleanup batch across the codebase:
- Removed raw exception text from user-facing Telegram replies in admin, request, conversion, indexing, premium, duplicate-cleanup, and misc info flows.
- Replaced weak exception logging patterns such as `logger.exception(e)`, `logger.error(f"...{e}")`, and exception `print()` calls with contextual `logger.exception(...)` calls.
- Removed unused `as e` bindings from several broad handlers where the exception object was not used.

Verification completed with a targeted `rg` scan for raw `{e}` replies, weak logger calls, and exception prints; `python -m py_compile` across all modified Python files; and `git diff --check`.

## In Progress
No active file edit is in progress.

## Pending
- Review remaining broad `except Exception` handlers that intentionally preserve control flow and decide which can be narrowed safely.
- Add characterization tests or lightweight smoke checks before fixing behavior-sensitive bugs.
- Consider later internal function-level cleanup for modules that are under 300 lines but still have large functions, such as `EbookGuy/features/search/results.py`, `EbookGuy/features/downloads/start.py`, and `EbookGuy/features/indexing/worker.py`.

## Known Issues
- No test suite or CI workflow was found, so refactors are currently verified only by compile/static checks.
- Broader watermark-like identifiers remain and were not renamed in this local-variable pass: `EbookGuy` package paths, `EbookGuyXBot`, `EbookGuyBot`, `MELCOW_NEW_USERS`, `MELCOW`, and `MELCOW_ENG`.
- `EbookGuy/features/indexing/worker.py` preserves the original large `index_files_to_db` function and recursive resume behavior during FloodWait handling.
- Bare `except:` handlers have been removed, and the first pass of raw exception exposure / weak exception logging has been cleaned. Some broad `except Exception` handlers remain where narrowing them would require behavior-sensitive review.
- Some async database functions still call synchronous PyMongo operations directly.
- Compile verification generated ignored `__pycache__/` files.

## Files Status
- Created: `EbookGuy/features/__init__.py`, `EbookGuy/features/search/`, `EbookGuy/features/filters/`, `EbookGuy/features/downloads/`, `EbookGuy/features/premium/`, `EbookGuy/features/indexing/`, `EbookGuy/features/admin/`, `EbookGuy/features/requests/`, `EbookGuy/shared/`, and package `__init__.py` files inside each new folder.
- Moved: plugin implementation modules from `plugins/` into their matching `EbookGuy/features/*` folders; root `utils_*` modules into `EbookGuy/shared/`.
- Modified: `plugins/commands.py`, `plugins/commands_downloads.py`, `plugins/index.py`, `plugins/pm_filter_callbacks.py`, `plugins/pm_filter_filtering.py`, `plugins/pm_filter_search.py`, `plugins/premium.py`, `plugins/banned.py`, `utils.py`, moved implementation modules with updated import paths, `EbookGuy/features/search/results.py`, `EbookGuy/features/downloads/start.py`, `EbookGuy/features/filters/manual.py`, `EbookGuy/features/filters/global_filters.py`, `EbookGuy/features/filters/premium_callbacks.py`, `EbookGuy/features/indexing/moderation.py`, `EbookGuy/features/indexing/requests.py`, `EbookGuy/shared/filter_parser.py`, `info.py`, and `HANDOFF.md`.
- Currently Being Edited: none.
- Planned to Edit: next pass should review behavior-sensitive broad `except Exception` handlers and async DB blocking patterns.
- Untouched: `bot.py`, `database/ia_filterdb.py`, `database/users_chats_db.py`, `requirements.txt`, `Dockerfile`, `README.md`.
