# HANDOFF

## Project Overview
EbookGuy is a Python Telegram bot for searching, downloading, indexing, and converting ebooks/audiobooks with premium access via Telegram Stars and external payment links. It uses Pyrogram/pyrofork, MongoDB/Motor, plugin-based handlers, and an aiohttp keepalive server.

## Current State
The bot remains plugin-driven. Large plugin files are being split one at a time while keeping `plugins/` as the current flat plugin-loading surface. `plugins/pm_filter.py`, `plugins/pm_filter_callbacks.py`, `plugins/pm_filter_search.py`, `plugins/pm_filter_filtering.py`, `plugins/commands.py`, `plugins/commands_downloads.py`, `plugins/premium.py`, and `plugins/index.py` now act as small Pyrogram handler registration/delegation modules. `utils.py` is now a compatibility utility barrel with focused implementation modules at the project root. `database/users_chats_db.py` is now a small public database module backed by focused user, settings, and premium mixins. Extracted plugin behavior currently remains under `plugins/` and has not yet been reorganized into domain folders.

The local repository is on branch `main`, tracks `origin/main`, and has been pushed to `https://github.com/PerspicaciousGuy/filtering-bot.git`. `AGENTS.md` and `agents-guidelines/` are local-only project guidance files and should not be tracked in Git.

## Last Action
Split `plugins/commands_downloads.py` into focused download/start modules while preserving the same import surface for `plugins/commands.py`:
- `plugins/commands_download_limits.py` owns download quota checks and auto-delete cleanup messages.
- `plugins/commands_start.py` owns `/start` handling, start buttons, force-subscribe handling, and deep-link preview responses.
- `plugins/commands_download_callbacks.py` owns the `download_book` callback delivery path.
- `plugins/commands_downloads.py` now re-exports the same public names used by `plugins/commands.py`.

Verification completed with `python -m py_compile plugins\commands_downloads.py plugins\commands_download_limits.py plugins\commands_start.py plugins\commands_download_callbacks.py plugins\commands.py`.

## In Progress
No active file edit is in progress.

## Pending
- Continue one-file-at-a-time splitting before folder reorganization.
- Run a final split audit; no file should remain above the 300-line soft limit.
- After splitting the large files, reorganize implementation modules into domain folders such as `EbookGuy/features/search`, `EbookGuy/features/downloads`, `EbookGuy/features/premium`, `EbookGuy/features/indexing`, and utility/domain support folders, while leaving thin decorator entrypoints in `plugins/`.
- Add characterization tests or lightweight smoke checks before behavior changes.
- Consider later splitting the oversized `index_files_to_db` loop into smaller internal helpers after the file-level split sequence is complete.

## Known Issues
- No test suite or CI workflow was found, so refactors are currently verified only by compile/static checks.
- `plugins/pm_filter.py` previously contained callback references to premium functions that do not appear to exist in `plugins/premium.py`; the split preserved those references.
- `plugins/pm_filter_callbacks.py` was split by callback family, but the extracted modules preserve the original broad exception handling and repeated request-status notification code.
- `plugins/pm_filter_search_results.py` preserves the pre-existing missing `save_group_settings` import path from the original search module.
- `plugins/commands_start.py` preserves the pre-existing `base64` reference without a local import from the original download command module.
- `plugins/pm_filter_manual_filters.py` and `plugins/pm_filter_global_filters.py` still contain the pre-existing `eval(btn)` pattern from the original filtering code.
- `plugins/pm_filter_manual_filters.py` and `plugins/pm_filter_global_filters.py` preserve pre-existing references to `asyncio` and `save_group_settings` without local imports.
- `plugins/index_worker.py` preserves the original large `index_files_to_db` function, including broad exception handling and recursive resume behavior during FloodWait handling.
- `plugins/index_requests.py` preserves the original non-admin public-username link path that reads `message.forward_from_chat.username` even when the request came from typed text.
- Several modules still use broad `except` blocks and `print()` logging.
- `info.py` uses `bool(environ.get(...))`, which treats string values like `False` as true.
- Some async database functions still call synchronous PyMongo operations directly.
- Compile verification generated ignored `__pycache__/` files under `plugins/`.

## Files Status
- Created: `plugins/pm_filter_search.py`, `plugins/pm_filter_callbacks.py`, `plugins/pm_filter_premium_callbacks.py`, `plugins/pm_filter_filtering.py`, `plugins/commands_downloads.py`, `plugins/commands_conversion.py`, `plugins/commands_admin.py`, `plugins/commands_requests.py`, `plugins/premium_views.py`, `plugins/premium_payments.py`, `plugins/premium_admin.py`, `plugins/index_worker.py`, `plugins/index_requests.py`, `plugins/index_moderation.py`, `plugins/index_admin.py`, `plugins/pm_filter_filter_management_callbacks.py`, `plugins/pm_filter_connection_callbacks.py`, `plugins/pm_filter_alert_callbacks.py`, `plugins/pm_filter_file_callbacks.py`, `plugins/pm_filter_request_status_callbacks.py`, `plugins/pm_filter_search_state.py`, `plugins/pm_filter_search_format.py`, `plugins/pm_filter_search_results.py`, `plugins/pm_filter_manual_filters.py`, `plugins/pm_filter_global_filters.py`, `utils_state.py`, `utils_subscriptions.py`, `utils_broadcast.py`, `utils_settings.py`, `utils_formatting.py`, `utils_message.py`, `utils_filter_parser.py`, `utils_delivery.py`, `database/users_chats_user_db.py`, `database/users_chats_settings_db.py`, `database/users_chats_premium_db.py`, `plugins/commands_download_limits.py`, `plugins/commands_start.py`, `plugins/commands_download_callbacks.py`, `HANDOFF.md`, `.git/`.
- Modified: `plugins/pm_filter.py` - reduced from a large mixed-responsibility module to delegated handlers; `plugins/pm_filter_callbacks.py` - reduced from a large callback dispatcher to callback-family delegation; `plugins/pm_filter_search.py` - reduced from a large search workflow module to a compatibility re-export surface; `plugins/pm_filter_filtering.py` - reduced from a large filtering workflow module to a compatibility re-export surface; `utils.py` - reduced from a mixed utility module to a compatibility re-export surface; `database/users_chats_db.py` - reduced from a mixed database repository class to a concrete database composition module; `plugins/commands.py` - reduced from a large mixed-responsibility module to delegated handlers; `plugins/commands_downloads.py` - reduced from a mixed start/download module to a compatibility re-export surface; `plugins/premium.py` - reduced from a large premium workflow module to delegated handlers; `plugins/index.py` - reduced from a large indexing workflow module to delegated handlers; `.gitignore` - excludes `AGENTS.md` and `agents-guidelines/`; `HANDOFF.md` - records the index split and current file status.
- Currently Being Edited: none.
- Planned to Edit: none until the final split audit identifies another responsibility-based split.
- Untouched: `database/users_chats_db.py`, `database/ia_filterdb.py`, `utils.py`, `info.py`, `requirements.txt`, `Dockerfile`, `README.md`.
