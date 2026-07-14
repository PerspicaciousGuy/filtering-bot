# HANDOFF

## Project Overview
EbookGuy is a Python Telegram bot for searching, downloading, indexing, and converting ebooks/audiobooks with premium access via Telegram Stars and external payment links. It uses Pyrogram/pyrofork, MongoDB/Motor, plugin-based handlers, and an aiohttp keepalive server.

## Current State
The planned split, modernization, duplication cleanup, dead-code audit, organization, watermark audit, and validation phases are complete. Thin Pyrogram plugin/decorator entrypoints remain in `plugins/`, because `bot.py` loads `plugins/*.py`. Extracted implementation code now lives in domain folders under `EbookGuy/features/`, shared utility code lives under `EbookGuy/shared/`, and public compatibility barrels preserve existing import surfaces.

An admin-only `/settings` command opens a global settings dashboard with Usage Limits, Search, Delivery, Requests, Premium, and Bot Operation categories. All 38 settings are editable and enforced at runtime. Each setting opens a detail page with its description, current/default values, and Back navigation. Boolean settings use Enable/Disable; numeric, text, template, channel-ID, and HTTPS URL settings use validated Edit Value/Reset Default flows. Invalid input keeps the prompt active, while successful input refreshes the detail page and removes the temporary prompt messages.

Free users who exhaust their daily download allowance now receive a normal follow-up chat message explaining that all free downloads for the day have been used, with an Upgrade to Premium button that opens the existing premium flow. Download-button callbacks are acknowledged silently instead of displaying this denial as a popup.

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
Standardized the free download-limit message and upgrade button on the existing Premium product name. The text now says `Premium plan`, the button says `Upgrade to Premium`, and the existing `show_premium` callback and follow-up-message behavior remain unchanged.

The module compiles and an isolated behavior check confirms the Premium wording, callback payload, and follow-up message. The bot launcher is PID `13664`, the server process is PID `11492`, and `http://127.0.0.1:8080/` returns HTTP 200.

## In Progress
None. The user confirmed all `/settings` controls and the download-limit follow-up message work correctly in Telegram.

## Pending
- Commit the completed settings implementation when the user is ready.
- Validate conversion callback target formats before creating output paths.
- Split `EbookGuy/features/downloads/conversion.py` and settings validation by responsibility when file splitting resumes.
- Move safe callback acknowledgments earlier based on measured handlers.
- Exercise core Telegram commands against the optimized bot.
- Run a live Telegram smoke test in the deployed environment before release.
## Known Issues
- Restart notification to chat `-1002181641962` fails with `CHAT_ADMIN_REQUIRED`; bot startup and the web server continue normally.
- A transient MongoDB SRV DNS timeout can prevent local startup before application import; retrying restored the bot without code changes.
- Local bot startup modifies tracked runtime file `EbookGuyBot.session`; exclude it from settings commits unless the session is intentionally being rotated.
- Legacy direct-download payloads do not expose file size until Telegram sends the file, so configured maximum file size is enforced before delivery only for indexed and bulk-download records.
- `EbookGuy/features/downloads/conversion.py` is now 335 lines and `EbookGuy/shared/settings_schema.py` is 360 lines. Both exceed the 300-line soft limit but remain below the 500-line hard limit; splitting is paused by user direction.
- Conversion callback target formats are not independently allowlisted in `handle_do_convert_callback`; forged callback data could produce an invalid output path. Address this as the next security fix outside the settings scope.
- Successful Telegram payment handling is not idempotent against a duplicate successful-payment update; the existing flow could extend premium twice if Telegram redelivers the same charge.
- `database/search_repository.py:_compile_search_regex` and `database/ia_filterdb.py:get_bad_files` compile raw search text as regular expressions. This preserves existing behavior but allows regex metacharacters and potentially expensive patterns; decide whether search should be literal before changing it.
- No repository test suite or CI workflow was found; verification uses compile/static gates and isolated behavior smoke tests.
- Docker is unavailable; local execution uses the isolated temporary Python 3.10 environment.
- Retained dormant, unreferenced compatibility code: `database/connections_mdb.py:add_connection`, `EbookGuy/util/custom_dl.py:ByteStreamer`, and `EbookGuy/util/render_template.py:render_page`.
- Watermark/attribution identifiers retained for compatibility or branding: `EbookGuy`, `EbookGuyXBot`, `EbookGuyBot`, `MELCOW_NEW_USERS`, and `MELCOW`. The dormant `req.html` template also contains `Tech_VJ`, `VJ_Bots`, and `KingVJ01`; `custom_dl.py` credits `Eyaadh` in documentation. No generated filename watermark remains.
- Compile verification generated ignored `__pycache__/` files.

## Files Status
- Created: focused search, download, indexing, admin, shared, and database modules, including `inline_queries.py`, `models.py`, `pagination.py`, `rendering.py`, `expiry.py`, `start_views.py`, `start_delivery.py`, `force_subscription.py`, `progress.py`, `user_info.py`, `file_cleanup.py`, `file_collections.py`, `filter_stats.py`, `indexing_checkpoints.py`, `search_repository.py`, `settings_catalog.py`, `settings_schema.py`, `global_settings.py`, `global_settings_db.py`, `settings_commands.py`, `settings_callbacks.py`, `settings_input.py`, `request_records_db.py`, `premium/plans.py`, `premium/expiry_notifications.py`, `operations/maintenance.py`, and the thin `plugins/maintenance.py` entrypoint.
- Moved: plugin implementation modules from `plugins/` into their matching `EbookGuy/features/*` folders; root `utils_*` modules into `EbookGuy/shared/`.
- Modified: all settings views, input, schema, persistence, and runtime consumers across Delivery, Requests, Premium, indexing, broadcasts, maintenance, startup/logging, support rendering, `EbookGuy/features/downloads/limits.py`, `README.md`, runtime-generated `EbookGuyBot.session`, and `HANDOFF.md`.
- Currently Being Edited: none; settings and download-limit behavior are verified in Telegram.
- Planned to Edit: conversion workflow/security modules after user approval.
- Untouched dependencies/deployment: `requirements.txt` and `Dockerfile`.
