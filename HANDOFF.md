# HANDOFF

## Project Overview
EbookGuy is a Python Telegram bot for searching, downloading, indexing, and converting ebooks/audiobooks with premium access via Telegram Stars and external payment links. It uses Pyrogram/pyrofork, MongoDB/Motor, plugin-based handlers, and an aiohttp keepalive server.

## Current State
The planned split, modernization, duplication cleanup, dead-code audit, organization, watermark audit, and validation phases are complete. Thin Pyrogram plugin/decorator entrypoints remain in `plugins/`, because `bot.py` loads `plugins/*.py`. Extracted implementation code now lives in domain folders under `EbookGuy/features/`, shared utility code lives under `EbookGuy/shared/`, and public compatibility barrels preserve existing import surfaces.

An admin-only `/settings` command opens a global settings dashboard with Usage Limits, Access & Welcome, Channels, Search, Delivery, Requests, Premium, and Bot Operation categories. All 54 settings are editable and enforced at runtime. Each setting opens a detail page with its description, current/default values, and Back navigation. Boolean settings use Enable/Disable; numeric, text, template, channel-ID, channel-list, and HTTPS URL settings use validated Edit Value/Reset Default flows. Invalid input keeps the prompt active, while successful input refreshes the detail page and removes the temporary prompt messages.

The Channels category controls file indexing channels, file deletion channels, the request channel, the index-request channel, the operational log channel, and the support fallback chat. Telegram access and bot-administrator status are validated before saving. File indexing and deletion source handlers use settings-backed dynamic filters, so channel-list changes apply without a restart; the same channel cannot be assigned to both source lists.

Access & Welcome settings now control force subscription, up to 10 required public/private channels, and the `/start` welcome template. Configured channels are validated live before saving, and restricted searches, inline queries, requests, downloads, conversions, and deep links enforce every required subscription concurrently. Legacy `AUTH_CHANNEL` behavior remains supported when the new channel list is empty.

Regular users can open `/trending_now` when trending searches are enabled. Search events are recorded without blocking handlers, and the configurable period and result count drive the public ranking. The settings dashboard also includes an Analytics page with Today, 7 Days, 30 Days, and All Time views for users, searches, downloads, requests, conversions, Premium activations, and Telegram Stars payments.

Book requests support an optional required-author format (`/request Book title | Author name`), stable persisted request IDs, and the restored Processing, Uploaded, Already Available, and Unavailable statuses. Each status sends its own configurable message template to the requester. Uploaded and Already Available notifications include an Open Bot & Search button. Current three-state callbacks, records, and saved templates are compatibility-mapped to the restored flow. Usage Limits includes a preview and second confirmation before resetting all nonzero download counters for the current UTC day.

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
Restored the previous four-state request workflow with the original 2x2 administrator menu: Unavailable, Uploaded, Already Available, and Processing. Replaced the Accepted/Rejected/Completed template settings with four status-specific templates, added search buttons for available-book outcomes, and retained compatibility for current callbacks, historical database statuses, and any legacy template overrides.

Verification passed for all 54 settings, four status buttons, callback payload limits, all notification templates, available-book search buttons, legacy callbacks/templates, historical analytics mapping, MongoDB defaults, full-project compilation, whitespace, and the 50-line/three-parameter structural gates. The bot launcher is PID `14196`, the server process is PID `7368`, and `http://127.0.0.1:8080/` returns HTTP 200 with the updated code.

## In Progress
None. Implementation and local/runtime verification are complete; the restored request statuses still need a live Telegram smoke test by the user.

## Pending
- Submit a test request and live-test Processing, Uploaded, Already Available, and Unavailable notifications.
- Live-test each Channels setting with chats where the bot is an administrator.
- Live-test the new Access & Welcome, `/trending_now`, request-status, reset-confirmation, and analytics flows in Telegram.
- Commit the completed settings and analytics implementation when the user is ready.
- Validate conversion callback target formats before creating output paths.
- Split `EbookGuy/features/downloads/conversion.py` when file splitting resumes.
- Move safe callback acknowledgments earlier based on measured handlers.
- Exercise core Telegram commands against the optimized bot.
- Run a live Telegram smoke test in the deployed environment before release.
## Known Issues
- Restart notification to chat `-1002181641962` fails with `CHAT_ADMIN_REQUIRED`; bot startup and the web server continue normally.
- A transient MongoDB SRV DNS timeout can prevent local startup before application import; retrying restored the bot without code changes.
- Local bot startup modifies tracked runtime file `EbookGuyBot.session`; exclude it from settings commits unless the session is intentionally being rotated.
- Legacy direct-download payloads do not expose file size until Telegram sends the file, so configured maximum file size is enforced before delivery only for indexed and bulk-download records.
- `EbookGuy/features/downloads/conversion.py` is 353 lines and `EbookGuy/shared/settings_validation.py` is 431 lines. Both exceed the 300-line soft limit but remain below the 500-line hard limit; each currently owns one responsibility.
- Conversion callback target formats are not independently allowlisted in `handle_do_convert_callback`; forged callback data could produce an invalid output path. Address this as the next security fix outside the settings scope.
- Successful Telegram payment handling is not idempotent against a duplicate successful-payment update; the existing flow could extend premium twice if Telegram redelivers the same charge.
- `database/search_repository.py:_compile_search_regex` and `database/ia_filterdb.py:get_bad_files` compile raw search text as regular expressions. This preserves existing behavior but allows regex metacharacters and potentially expensive patterns; decide whether search should be literal before changing it.
- No repository test suite or CI workflow was found, and Ruff is not installed in the isolated environment; verification uses compile/static gates and isolated behavior smoke tests.
- Docker is unavailable; local execution uses the isolated temporary Python 3.10 environment.
- Retained dormant, unreferenced compatibility code: `database/connections_mdb.py:add_connection`, `EbookGuy/util/custom_dl.py:ByteStreamer`, and `EbookGuy/util/render_template.py:render_page`.
- Watermark/attribution identifiers retained for compatibility or branding: `EbookGuy`, `EbookGuyXBot`, `EbookGuyBot`, `MELCOW_NEW_USERS`, and `MELCOW`. The dormant `req.html` template also contains `Tech_VJ`, `VJ_Bots`, and `KingVJ01`; `custom_dl.py` credits `Eyaadh` in documentation. No generated filename watermark remains.
- Compile verification generated ignored `__pycache__/` files.

## Files Status
- Created: focused search, download, indexing, admin, shared, and database modules, including `inline_queries.py`, `models.py`, `pagination.py`, `rendering.py`, `expiry.py`, `start_views.py`, `start_delivery.py`, `force_subscription.py`, `progress.py`, `user_info.py`, `file_cleanup.py`, `file_collections.py`, `filter_stats.py`, `indexing_checkpoints.py`, `search_repository.py`, `settings_catalog.py`, `settings_schema.py`, `settings_defaults.py`, `settings_descriptions.py`, `settings_validation.py`, `configured_channels.py`, `global_settings.py`, `global_settings_db.py`, `settings_commands.py`, `settings_callbacks.py`, `settings_input.py`, `settings_actions.py`, `settings_runtime_validation.py`, `analytics.py`, `analytics_db.py`, `trending.py`, `notifications.py`, `request_records_db.py`, `premium/plans.py`, `premium/expiry_notifications.py`, `operations/maintenance.py`, and the thin `plugins/maintenance.py` entrypoint.
- Moved: plugin implementation modules from `plugins/` into their matching `EbookGuy/features/*` folders; root `utils_*` modules into `EbookGuy/shared/`.
- Modified: all settings views, input, schema, persistence, and runtime consumers across Search, Delivery, Requests, Premium, startup, subscriptions, downloads, conversions, payments, indexing requests, request notifications, channel indexing/deletion plugins, database mixins, `plugins/commands.py`, `README.md`, runtime-generated `EbookGuyBot.session`, and `HANDOFF.md`.
- Currently Being Edited: none; all 54 settings and the restored request flow are locally verified and running.
- Planned to Edit: conversion workflow/security modules after user approval.
- Untouched dependencies/deployment: `requirements.txt` and `Dockerfile`.
