---
name: alice-connection-check
description: Check connectivity status of Alice's integrated services and MCP tools — Gmail, Google Calendar, Odoo, and internet access. Use when verifying Alice's connections in Alice's project.
scope: core
triggers:
  - "connection check"
  - "check connection"
  - "check connections"
  - "are services connected"
  - "is alice connected"
  - "connection status"
  - "service status"
  - "check integrations"
  - "verify connections"
  - "ping services"
---

# Skill: Connection Check

## What This Does

Checks the connectivity and reachability of Alice's integrated services. Reports which services are online, which are unavailable, and surfaces any auth or config issues.

---

## Services to Check

| Service | Check Method | Healthy Signal |
|---|---|---|
| **Internet** | Fetch a known reliable URL (e.g. `https://www.google.com`) | HTTP 200 |
| **Gmail (MCP)** | ToolSearch schema → call `mcp__claude_ai_Gmail__gmail_get_profile` | Returns email address |
| **Google Calendar (MCP)** | ToolSearch schema → call `mcp__claude_ai_Google_Calendar__authenticate` | No error |
| **Odoo (MCP)** | ToolSearch schema → call `mcp__odoo__odoo_count` with model `project.project` | Returns a number |
| **Google API (Python/local)** | Check file exists: `{ALICE_ROOT}/credentials/google_token.json` | File present |

---

## Execution Steps

### 1. Internet connectivity

Use the `WebFetch` tool to fetch `https://www.google.com`.

- Success → report `Internet: OK`
- Failure → report `Internet: OFFLINE` — flag this, as it will cause all MCP and API calls to fail

### 2. Gmail MCP

Use `ToolSearch` (query: `"select:mcp__claude_ai_Gmail__gmail_get_profile"`) to fetch the schema, then call `mcp__claude_ai_Gmail__gmail_get_profile`.

> **Why:** Gmail MCP tools are deferred — ToolSearch must be called first or the tool will falsely appear unconfigured.

- Returns a profile with an email → `Gmail MCP: OK (connected as <email>)`
- ToolSearch returns no results → `Gmail MCP: NOT CONFIGURED`
- Call errors after schema loaded → `Gmail MCP: UNAVAILABLE`

### 3. Google Calendar MCP

Use `ToolSearch` (query: `"select:mcp__claude_ai_Google_Calendar__authenticate"`) to fetch the schema, then call `mcp__claude_ai_Google_Calendar__authenticate`.

> **Why:** Same deferred-tool pattern as Gmail.

- Succeeds → `Google Calendar MCP: OK`
- ToolSearch returns no results → `Google Calendar MCP: NOT CONFIGURED`
- Call errors after schema loaded → `Google Calendar MCP: UNAVAILABLE`

### 4. Odoo MCP

First use `ToolSearch` to fetch the `mcp__odoo__odoo_count` schema (query: `"select:mcp__odoo__odoo_count"`), then call it with `{"model": "project.project", "domain": []}`.

> **Why:** Odoo MCP tools are deferred — they must be fetched via ToolSearch before they can be called. Skipping this step causes a false "not found" error even when Odoo is correctly set up.

- Tool found + call returns a number → `Odoo MCP: ✅ OK (<N> projects found)`
- ToolSearch returns no results AND running from outside Alice project → `Odoo MCP: ✅ OK (project-scoped — only active inside the Alice project directory)`
- ToolSearch returns no results AND running from inside Alice project → `Odoo MCP: ❌ NOT CONFIGURED — check the \`odoo\` entry in \`.claude.json\``
- Call errors after schema loaded → `Odoo MCP: ❌ UNAVAILABLE` — server reachable but call failed. Check the bearer token in `.claude.json`.

### 5. Local Google API credentials

Check if `{ALICE_ROOT}/credentials/google_token.json` exists.

- File present → `Local Google API token: PRESENT`
- Missing → `Local Google API token: MISSING — Python scripts that call Gmail/Calendar directly will fail`

---

## Output Format

Report results in a single summary block:

```
## Alice — Connection Status [YYYY-MM-DD HH:MM]

| Service                  | Status  | Detail                         |
|--------------------------|---------|--------------------------------|
| Internet                 | ✅ OK   |                                |
| Gmail MCP                | ✅ OK   | Connected as user@example.com  |
| Google Calendar MCP      | ✅ OK   |                                |
| Odoo MCP                 | ✅ OK   | 5 projects found               |
| Local Google API token   | ✅ OK   | File present                   |
```

Use `✅ OK`, `❌ UNAVAILABLE`, or `⚠️ WARNING` in the Status column.

If any service fails, append a **Diagnosis** section with:
- What likely caused the failure
- The fix steps (e.g. re-run auth, check MCP config, verify network)

---

## Notes

- MCP tools (Gmail, Calendar, Odoo) are only available in the `claude.ai` web app by default. In Claude Code CLI, you need local MCP servers configured.
- A failing internet check means ALL network-dependent checks will also fail — report this first before interpreting other failures.
- The local Google API token check is independent of MCP availability.
