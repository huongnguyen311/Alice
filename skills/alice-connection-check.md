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
| **Gmail (MCP)** | Call `mcp__claude_ai_Gmail__gmail_get_profile` | Returns email address |
| **Google Calendar (MCP)** | Call `mcp__claude_ai_Google_Calendar__authenticate` | No error |
| **Odoo (MCP)** | Call `mcp__odoo__odoo_count` with model `project.project` | Returns a number |
| **Google API (Python/local)** | Check file exists: `{ALICE_ROOT}/credentials/google_token.json` | File present |

---

## Execution Steps

### 1. Internet connectivity

Use the `WebFetch` tool to fetch `https://www.google.com`.

- Success → report `Internet: OK`
- Failure → report `Internet: OFFLINE` — flag this, as it will cause all MCP and API calls to fail

### 2. Gmail MCP

Call `mcp__claude_ai_Gmail__gmail_get_profile`.

- Returns a profile with an email → `Gmail MCP: OK (connected as <email>)`
- Error or no response → `Gmail MCP: UNAVAILABLE`

### 3. Google Calendar MCP

Call `mcp__claude_ai_Google_Calendar__authenticate`.

- Succeeds → `Google Calendar MCP: OK`
- Error → `Google Calendar MCP: UNAVAILABLE`

### 4. Odoo MCP

Call `mcp__odoo__odoo_count` with `{"model": "project.project", "domain": []}`.

- Returns a number → `Odoo MCP: OK (<N> projects found)`
- Error or no response → `Odoo MCP: UNAVAILABLE`

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
