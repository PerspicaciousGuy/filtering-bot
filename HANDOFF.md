# HANDOFF

## Project Overview
EbookGuy is a Python Telegram bot for searching, downloading, indexing, and converting ebooks/audiobooks with premium access via Telegram Stars and external payment links. It uses Pyrogram/pyrofork, MongoDB/Motor, plugin-based handlers, and an aiohttp keepalive server.

## Current State
The bot remains plugin-driven. Large plugin files are being split one at a time while keeping `plugins/` as the current flat plugin-loading surface. `plugins/pm_filter.py` and `plugins/commands.py` now act as small Pyrogram handler registration/delegation modules. Their extracted behavior currently remains under `plugins/` and has not yet been reorganized into domain folders.

The local repository is on branch `main`, tracks `origin/main`, and has been pushed to `https://github.com/PerspicaciousGuy/filtering-bot.git`. `AGENTS.md` and `agents-guidelines/` are local-only project guidance files and should not be tracked in Git.

## Last Action
Rewrote Git history to remove `AGENTS.md` and `agents-guidelines/` from the repository history. The local files remain available and ignored by Git.

Commands used for the history rewrite:
- Create a clean orphan branch from the current working tree.
- Commit the current non-ignored project snapshot.
- Rename the clean branch to `main`.
- Force-push `main` to `origin/main` with lease.

## In Progress
No active file edit is in progress. History rewrite cleanup is the active Git operation until the clean commit is force-pushed and verified.

## Pending
- Continue one-file-at-a-time splitting before folder reorganization.
- Next likely split target: `plugins/premium.py` or `plugins/index.py`, both currently above the soft limit.
- After splitting the large files, reorganize implementation modules into domain folders such as `EbookGuy/features/search`, `EbookGuy/features/downloads`, `EbookGuy/features/premium`, and `EbookGuy/features/indexing`, while leaving thin decorator entrypoints in `plugins/`.
- Add characterization tests or lightweight smoke checks before behavior changes.
- Consider later splitting `database/users_chats_db.py` and `utils.py`.

## Known Issues
- No test suite or CI workflow was found, so refactors are currently verified only by compile/static checks.
- `plugins/pm_filter.py` previously contained callback references to premium functions that do not appear to exist in `plugins/premium.py`; the split preserved those references.
- `plugins/pm_filter_filtering.py` still contains the pre-existing `eval(btn)` pattern from the original code.
- Several modules still use broad `except` blocks and `print()` logging.
- `info.py` uses `bool(environ.get(...))`, which treats string values like `False` as true.
- Some async database functions still call synchronous PyMongo operations directly.
- Compile verification generated `plugins/__pycache__/pm_filter*.pyc` and `plugins/__pycache__/commands*.pyc` files, but they are ignored by Git.

## Files Status
- Created: `plugins/pm_filter_search.py`, `plugins/pm_filter_callbacks.py`, `plugins/pm_filter_premium_callbacks.py`, `plugins/pm_filter_filtering.py`, `plugins/commands_downloads.py`, `plugins/commands_conversion.py`, `plugins/commands_admin.py`, `plugins/commands_requests.py`, `HANDOFF.md`, `.git/`.
- Modified: `plugins/pm_filter.py` — reduced from a large mixed-responsibility module to delegated handlers; `plugins/commands.py` — reduced from a large mixed-responsibility module to delegated handlers; `.gitignore` — excludes `AGENTS.md` and `agents-guidelines/`; `HANDOFF.md` — records the history rewrite cleanup.
- Currently Being Edited: none.
- Planned to Edit: `plugins/premium.py` or `plugins/index.py` if the next approved split continues with large plugin files.
- Untouched: `plugins/premium.py`, `plugins/index.py`, `database/users_chats_db.py`, `database/ia_filterdb.py`, `utils.py`, `info.py`, `requirements.txt`, `Dockerfile`, `README.md`.
