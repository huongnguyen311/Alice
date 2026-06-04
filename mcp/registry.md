# MCP Registry

This file documents all MCP (Model Context Protocol) servers and tools available to Alice. Update this file whenever a new MCP is added, removed, or changed.

## How to Add an Entry

```markdown
### [Server Name]
- **Status:** active | inactive
- **Purpose:** What this server provides
- **Key tools:** List of the most useful tool names
- **Notes:** Any usage quirks or limitations
```

---

## Registered Servers

### claude.ai Gmail
- **Status:** active
- **MCP type:** Remote — hosted by Anthropic, authenticated via Claude.ai session
- **Purpose:** Read and search Gmail inbox for the configured account
- **Key tools:** `gmail_search_messages`, `gmail_read_message`, `gmail_get_profile`, `gmail_list_labels`, `gmail_list_drafts`, `gmail_create_draft`, `gmail_read_thread`
- **Use for:** Single actions in conversation (read one email, search, draft)
- **Python equivalent:** `google-api-python-client` with `credentials/google_token.json` — use for batch/multi-step scripts
- **Python setup:** Run `python setup/google_auth_setup.py` once to generate `credentials/google_token.json`
- **Notes:** Used by the `daily-email-recap` skill. Session-bound — available while Claude Code is running with this MCP connected. Python scripts cannot connect to this MCP directly.

### claude.ai Google Calendar
- **Status:** active
- **MCP type:** Remote — hosted by Anthropic, authenticated via Claude.ai session
- **Purpose:** Read and manage Google Calendar events
- **Key tools:** `gcal_list_events`, `gcal_get_event`, `gcal_create_event`, `gcal_update_event`, `gcal_delete_event`, `gcal_list_calendars`, `gcal_find_meeting_times`, `gcal_find_my_free_time`, `gcal_respond_to_event`
- **Use for:** Single actions in conversation (create one event, check schedule)
- **Python equivalent:** `google-api-python-client` with `credentials/google_token.json` — same credential as Gmail
- **Notes:** Same Google account as Gmail. Python scripts cannot connect to this MCP directly.

### claude.ai Canva
- **Status:** active
- **MCP type:** Remote — hosted by Anthropic, authenticated via Claude.ai session
- **Purpose:** Search, generate, and edit Canva designs
- **Key tools:** `search-designs-claude`, `generate-designs-claude`, `generate-designs-structured`, `outline-review-claude`
- **Use for:** Interactive design tasks in conversation
- **Python equivalent:** Canva REST API via `requests` with API key stored in `credentials/canva_api_key.txt`
- **Notes:** Not yet used by any Alice skill. Python scripts cannot connect to this MCP directly — requires separate Canva API key setup.

### Google Workspace (Sheets / Docs)
- **Status:** active — **no MCP server** (Python-only)
- **MCP type:** None. The former `mcp-google-sheets` MCP has been **removed**; all Sheets/Docs work runs through the Python skill.
- **Purpose:** Read/write/append/update/delete/search Google Sheets
- **Auth:** **Easy-auth gateway** (token broker) — the gateway holds Google's `client_secret` server-side; Alice holds a gate credential (`clientId`/`clientSecret`) + a per-user `refresh_token`. Tokens cannot self-refresh against Google; refresh routes through the gateway.
- **Skill:** `skills/Google-Sheet/skill.md` (google-api-python-client, with a pre-flight gateway refresh)
- **Setup:** `setup/google_gateway_auth.py` (one-time consent) → writes `credentials/google_token.json`. Gate creds in `credentials/gateway-config.json`. Refresh helper: `setup/gateway_tokens.py`.
- **Setup guide:** `setup/google-sheets-setup.md` · **Protocol:** `setup/google-gateway-INTEGRATION.md`
- **Notes:** Gateway grants `spreadsheets` + `drive.readonly` only (no Gmail/Calendar). Gmail/Calendar Python still use the separate desktop-OAuth flow (`setup/google_auth_setup.py`).

### Google Auth (gateway) — auth-only
- **Status:** active
- **MCP type:** Local **stdio**, **project-scoped** — declared in `.mcp.json`, loaded by Claude Code **only inside the Alice project**. NOT synced to `~/.claude.json` (excluded by `PROJECT_LOCAL_MCPS` in `install.py`).
- **Server:** `mcp/google_auth_mcp.py` (Python, `mcp[cli]` / FastMCP), launched via the project venv.
- **Purpose:** One-click connect/reconnect to Google (Sheets/Docs) via the easy-auth gateway — **auth only, no API calls**. Removes the copy-paste from the setup flow.
- **Key tools:** `mcp__google-auth__connect_google` (one-click localhost auto-capture), `mcp__google-auth__google_auth_status` (read-only health), `mcp__google-auth__finish_google_connect` (paste fallback).
- **Writes:** `credentials/google_token.json` (then consumed by `skills/Google-Sheet/skill.md`). Reuses `setup/gateway_tokens.py` for token I/O.
- **Needs:** `credentials/gateway-config.json` (gate credential). One-click capture also needs the gateway to honor a `localhost` redirect_uri (see `setup/google-gateway-INTEGRATION.md`).
- **Skill:** `skills/alice-google-connect.md` (Alice-local). **Notes:** auth-only by design — never calls Sheets/Docs APIs.

### Odoo ERP (Self-Hosted)
- **Status:** active
- **MCP type:** Remote SSE — self-hosted at `https://erp.inapps.net/mcp/`
- **Purpose:** Interact with the inapps Odoo ERP instance (CRM, projects, invoicing, contacts, etc.)
- **Key tools:** `odoo_get`, `odoo_search`, `odoo_count`, `odoo_fields`, `odoo_create`, `odoo_write`, `odoo_comment`
- **Use for:** Single actions in conversation (query records, create/update CRM entries, check invoices)
- **Config:** Registered in `.mcp.json` as `"odoo"` with `type: sse`
- **Setup guide:** `setup/SETUP-ODOO-MCP.md`
- **Notes:** Self-hosted Odoo instance. No Python equivalent needed — use this MCP for all Odoo interactions.

---

## Notes

- Alice checks this registry to understand what external integrations are available
- If a tool is mentioned in conversation but not listed here, add it
- Mark servers as `inactive` rather than deleting them so history is preserved
- **All `claude.ai` MCP servers are remote and session-bound.** Python scripts cannot connect to them. For automation, use the Python equivalent listed per server.
- See `skills/mcp-or-script.md` for the full decision framework on when to use MCP vs. Python script.

---
*Last updated: 2026-06-04 (Google Sheets migrated to easy-auth gateway; mcp-google-sheets removed; added project-scoped auth-only `google-auth` MCP for one-click connect)*
