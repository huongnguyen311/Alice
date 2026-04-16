---
name: alice-connection-check
description: Check whether Alice's integrated services are reachable — Gmail, Google Calendar, Odoo MCP, Google Sheets, and internet. Use when diagnosing Alice service connectivity or verifying MCP health.
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
  - "check google sheet connection"
---

# Skill: Connection Check

## What This Does

Checks the connectivity and reachability of Alice's integrated services. Reports which services are online, which are unavailable, and surfaces any auth or config issues.

---

## Services to Check

| Service | Check Method | Healthy Signal |
|---|---|---|
| **Internet** | WebFetch `https://www.google.com` | HTTP 200 |
| **Gmail (MCP)** | Call `mcp__claude_ai_Gmail__list_labels` | Returns label list |
| **Google Calendar (MCP)** | Call `mcp__claude_ai_Google_Calendar__authenticate` | No error |
| **Odoo (MCP)** | Call `mcp__odoo__odoo_count` with model `project.project` | Returns a number |
| **Google Sheets / Local Token** | File exists: `{ALICE_ROOT}/credentials/google_token.json` | File present |

---

## Execution Steps

### Step 1 — Load all deferred schemas in ONE ToolSearch call

All MCP tools and WebFetch are deferred — they must be fetched before calling. Do this in a single call:

```
ToolSearch query: "select:WebFetch,mcp__claude_ai_Gmail__list_labels,mcp__claude_ai_Google_Calendar__authenticate,mcp__odoo__odoo_count"
```

If any tool is missing from the result → mark that service as `❌ NOT CONFIGURED` (do not attempt the call).

### Step 2 — Fire ALL checks in parallel (single message)

Send one message with all tool calls at once:

- `WebFetch` → `https://www.google.com` (prompt: "Return only: OK")
- `mcp__claude_ai_Gmail__list_labels`
- `mcp__claude_ai_Google_Calendar__authenticate`
- `mcp__odoo__odoo_count` → `{"model": "project.project", "domain": []}`
- `Bash` → `ls {ALICE_ROOT}/credentials/google_token.json 2>/dev/null && echo PRESENT || echo MISSING`

### Step 3 — Report results

Compile results into the output table below.

---

## Output Format

```
## Alice — Connection Status [YYYY-MM-DD HH:MM]

| Service                      | Status               | Detail                                          |
|------------------------------|----------------------|-------------------------------------------------|
| Internet                     | ✅ OK                |                                                 |
| Gmail MCP                    | ✅ OK                |                                                 |
| Google Calendar MCP          | ❌ NOT CONFIGURED    | Run /mcp → select "claude.ai Google Calendar"   |
| Odoo MCP                     | ✅ OK                | 14 projects found                               |
| Google Sheets / Local Token  | ❌ MISSING           | Run: setup/google_auth_setup.py                 |
```

**Allowed status values — use exactly these:**

| Status | When to use |
|---|---|
| `✅ OK` | Service reachable and working |
| `❌ NOT CONFIGURED` | Tool/file genuinely missing or not authenticated |
| `❌ MISSING` | Local file not found |
| `❌ UNAVAILABLE` | Tool found but call failed (auth/network error) |

**Never use `⚠️ WARNING`.** Reserve `❌` for failures that need user action.

If any `❌` is present, append a **Diagnosis** section listing what caused it and how to fix it.

---

## Notes

- **Gmail & Calendar MCPs** — account-bound, loaded from claude.ai session. NOT CONFIGURED = not authenticated with claude.ai.
- **Odoo MCP** — machine-global, registered in `~/.claude.json` by `install.py`. NOT CONFIGURED = `install.py` hasn't been run.
- **Google Sheets / Local Token** — Python scripts for Sheets, Gmail, and Calendar all use `credentials/google_token.json`. Missing = run `setup/google_auth_setup.py`. See `setup/google-sheets-setup.md` for full setup guide.
- **Internet offline** → all network checks will fail — flag this first.
