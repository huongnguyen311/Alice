---
name: alice-connection-check
description: Check whether Alice's integrated services are reachable — Gmail, Google Calendar, Odoo MCP, and internet. Use when diagnosing Alice service connectivity or verifying MCP health.
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
| **Gmail (MCP)** | ToolSearch schema → call `mcp__claude_ai_Gmail__list_labels` | Returns label list |
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

Use `ToolSearch` (query: `"select:mcp__claude_ai_Gmail__list_labels"`) to fetch the schema, then call `mcp__claude_ai_Gmail__list_labels`.

> **Why:** Gmail MCP tools are deferred — ToolSearch must be called first or the tool will falsely appear unconfigured.

- Returns a list of labels → `Gmail MCP: ✅ OK`
- ToolSearch returns no results → `Gmail MCP: ❌ NOT CONFIGURED — session not authenticated with claude.ai`
- Call errors after schema loaded → `Gmail MCP: ❌ UNAVAILABLE`

### 3. Google Calendar MCP

Use `ToolSearch` (query: `"select:mcp__claude_ai_Google_Calendar__authenticate"`) to fetch the schema, then call `mcp__claude_ai_Google_Calendar__authenticate`.

> **Why:** Same deferred-tool pattern as Gmail.

- Succeeds → `Google Calendar MCP: ✅ OK`
- ToolSearch returns no results → `Google Calendar MCP: ❌ NOT CONFIGURED — session not authenticated with claude.ai`
- Call errors after schema loaded → `Google Calendar MCP: ❌ UNAVAILABLE`

### 4. Odoo MCP

First use `ToolSearch` to fetch the `mcp__odoo__odoo_count` schema (query: `"select:mcp__odoo__odoo_count"`), then call it with `{"model": "project.project", "domain": []}`.

> **Why:** Odoo MCP tools are deferred — they must be fetched via ToolSearch before they can be called. Skipping this step causes a false "not found" error even when Odoo is correctly set up.

- Tool found + call returns a number → `Odoo MCP: ✅ OK (<N> projects found)`
- ToolSearch returns no results → `Odoo MCP: ❌ NOT CONFIGURED — run \`python auto-scripts/install.py\` inside the Alice project to sync Odoo MCP globally`
- Call errors after schema loaded → `Odoo MCP: ❌ UNAVAILABLE` — server reachable but call failed. Check the bearer token in `~/.claude/settings.json` or re-run `install.py`.

### 5. Local Google API credentials

Check if `{ALICE_ROOT}/credentials/google_token.json` exists.

- File present → `Local Google API token: PRESENT`
- Missing → `Local Google API token: MISSING — Python scripts that call Gmail/Calendar directly will fail`

---

## Output Format

Report results in a single summary block:

```
## Alice — Connection Status [YYYY-MM-DD HH:MM]

| Service                  | Status                  | Detail                                            |
|--------------------------|-------------------------|---------------------------------------------------|
| Internet                 | ✅ OK                   |                                                   |
| Gmail MCP                | ✅ OK                   | Connected as user@example.com                     |
| Google Calendar MCP      | ❌ NOT CONFIGURED        | Not authenticated                                 |
| Odoo MCP                 | ✅ OK                   | 14 projects found                                 |
| Local Google API token   | ❌ MISSING              | Re-run auth script to regenerate                  |
```

**Allowed status values — use exactly these, no others:**

| Status | When to use |
|---|---|
| `✅ OK` | Service reachable and working |
| `❌ NOT CONFIGURED` | Tool/file genuinely missing or not authenticated |
| `❌ MISSING` | Local file not found |
| `❌ UNAVAILABLE` | Tool found but call failed (auth/network error) |

**Never use `⚠️ WARNING`.** Reserve `❌` for actual failures that need user action.

If any `❌` status is present, append a **Diagnosis** section with:
- What likely caused the failure
- The fix steps

---

## Notes

- Gmail and Calendar MCPs are **account-bound** — loaded automatically from your claude.ai session. No local config needed. NOT CONFIGURED means the session is not authenticated with claude.ai.
- Odoo MCP is **machine-global** — registered in `~/.claude.json` by `install.py`. NOT CONFIGURED means `install.py` hasn't been run yet.
- A failing internet check means ALL network-dependent checks will also fail — report this first before interpreting other failures.
- The local Google API token check is independent of MCP availability.
