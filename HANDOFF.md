# HANDOFF

## Project Overview
EbookGuy is a Python Telegram bot for searching, downloading, indexing, and converting ebooks/audiobooks with premium access via Telegram Stars and external payment links. It uses Pyrogram/pyrofork, MongoDB/Motor, plugin-based handlers, and an aiohttp keepalive server.

## Current State
The planned split, modernization, duplication cleanup, dead-code audit, organization, watermark audit, and validation phases are complete. Thin Pyrogram plugin/decorator entrypoints remain in `plugins/`, because `bot.py` loads `plugins/*.py`. Extracted implementation code now lives in domain folders under `EbookGuy/features/`, shared utility code lives under `EbookGuy/shared/`, and public compatibility barrels preserve existing import surfaces.

An admin-only `/settings` command opens a global settings dashboard with Usage Limits, Search, Delivery, Requests, Premium, and Bot Operation categories. Every category now lists compact setting buttons that open a dedicated detail page with a description, current value, default value, and Back navigation. Editable boolean settings use explicit Enable and Disable actions; editable numeric settings use Edit Value and Reset Default. Usage Limits and Search are editable and enforced immediately; the other category detail pages remain read-only until their behavior is wired in their planned slices.

Current domain layout:
- `EbookGuy/features/search/` - search state, format selection, and result rendering.
- `EbookGuy/features/filters/` - manual/global filters and callback families.
- `EbookGuy/features/downloads/` - start flow, download limits, download callbacks, and conversion.
- `EbookGuy/features/premium/` - premium views, payments, and admin commands.
- `EbookGuy/features/indexing/` - indexing worker, moderation, request intake, and admin resume/delete flows.
- `EbookGuy/features/admin/` - admin command implementations.
- `EbookGuy/features/requests/` - request command implementation.
- `EbookGuy/shared/` - state, subscriptions, broadcast, settings, formatting, message helpers, filter parser, and delivery helpers.
- `database/search_repository.py` - user-facing MongoDB search filters, result caps, and cross-collection pagination; `ia_filterdb.py` keeps compatibility re-exports.

The local repository is on branch `main`, tracks `origin/main`, and local-only `AGENTS.md` / `agents-guidelines/` should remain ignored and untracked.

## Last Action
Fixed private search results remaining on the `Searching For...` message after a successful database query. Initial result rendering still expected the removed group-era `file_secure` key even though `SearchOutcome.settings` now contains global settings. The resulting `KeyError` occurred after matches were loaded and before result buttons could be rendered.

Initial and paginated search rendering now use the global `protect_content` delivery setting consistently to choose `file` or `filep` callback prefixes. The obsolete private-chat settings lookup was also removed from page navigation; unrelated legacy group-filter delivery paths were left unchanged.

Compile and project-wide function/parameter limits pass across 104 Python files. Isolated initial/paginated rendering checks pass without a `file_secure` key. A live read-only `atomic habits` query returned 7 results in about 3.0 seconds. The bot launcher is PID `3392`, the server process is PID `3152`, and the health endpoint returns HTTP 200.

## In Progress
Live Telegram verification of the fixed private-search result rendering.

## Pending
- Commit the completed refactor when the user is ready.
- Live-test boolean Enable/Disable, numeric Edit Value/Reset Default, and Back navigation.
- Live-test all Search settings and private/inline search behavior.
- Split `EbookGuy/features/downloads/conversion.py` by workflow responsibility before activating Delivery settings that affect conversion.
- Implement editable Delivery, Requests, Premium, and Bot Operation categories in order.
- Move safe callback acknowledgments earlier based on measured handlers.
- Exercise core Telegram commands against the optimized bot.
- Run a live Telegram smoke test in the deployed environment before release.
## Known Issues
- Restart notification to chat `-1002181641962` fails with `CHAT_ADMIN_REQUIRED`; bot startup and the web server continue normally.
- A transient MongoDB SRV DNS timeout can prevent local startup before application import; retrying restored the bot without code changes.
- Local bot startup modifies tracked runtime file `EbookGuyBot.session`; exclude it from settings commits unless the session is intentionally being rotated.
- Legacy direct-download payloads do not expose file size until Telegram sends the file, so configured maximum file size is enforced before delivery only for indexed and bulk-download records.
- `EbookGuy/features/downloads/conversion.py` is 293 lines; split by conversion workflow responsibility before adding more conversion behavior.
- `database/search_repository.py:_compile_search_regex` and `database/ia_filterdb.py:get_bad_files` compile raw search text as regular expressions. This preserves existing behavior but allows regex metacharacters and potentially expensive patterns; decide whether search should be literal before changing it.
- No repository test suite or CI workflow was found; verification uses compile/static gates and isolated behavior smoke tests.
- Docker is unavailable; local execution uses the isolated temporary Python 3.10 environment.
- Retained dormant, unreferenced compatibility code: `database/connections_mdb.py:add_connection`, `EbookGuy/util/custom_dl.py:ByteStreamer`, and `EbookGuy/util/render_template.py:render_page`.
- Watermark/attribution identifiers retained for compatibility or branding: `EbookGuy`, `EbookGuyXBot`, `EbookGuyBot`, `MELCOW_NEW_USERS`, and `MELCOW`. The dormant `req.html` template also contains `Tech_VJ`, `VJ_Bots`, and `KingVJ01`; `custom_dl.py` credits `Eyaadh` in documentation. No generated filename watermark remains.
- Compile verification generated ignored `__pycache__/` files.

## Files Status
- Created: focused search, download, indexing, admin, shared, and database modules, including `inline_queries.py`, `models.py`, `pagination.py`, `rendering.py`, `expiry.py`, `start_views.py`, `start_delivery.py`, `force_subscription.py`, `progress.py`, `user_info.py`, `file_cleanup.py`, `file_collections.py`, `filter_stats.py`, `indexing_checkpoints.py`, `search_repository.py`, `settings_catalog.py`, `settings_schema.py`, `global_settings.py`, `global_settings_db.py`, `settings_commands.py`, `settings_callbacks.py`, and `settings_input.py`.
- Moved: plugin implementation modules from `plugins/` into their matching `EbookGuy/features/*` folders; root `utils_*` modules into `EbookGuy/shared/`.
- Modified: settings views, callbacks, input, schema, persistence, and audit infrastructure; `database/ia_filterdb.py`; private and inline search result, format, rendering, pagination, navigation, model, and formatting modules; Usage enforcement and premium messaging modules; runtime-generated `EbookGuyBot.session`; and `HANDOFF.md`.
- Currently Being Edited: none; the search repository split is complete.
- Planned to Edit: conversion workflow modules, remaining settings category modules, and `HANDOFF.md`.
- Untouched dependencies/deployment: `requirements.txt` and `Dockerfile`.
