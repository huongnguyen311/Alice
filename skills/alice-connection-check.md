---
name: alice-connection-check
description: "Slash-only: run /alice-connection-check to check whether Alice's integrated services are reachable (Gmail, Google Calendar, Odoo MCP, Google Sheets, internet). Do NOT auto-load on phrases about connections or status — only invoke when the user explicitly runs the slash command."
scope: core
triggers: []
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
| **Google (Sheets/gateway)** | Call `mcp__google-auth__google_auth_status` if present; else file check `{ALICE_ROOT}/credentials/google_token.json` | `connected: true` (or file present) |

---

## Execution Steps

### Step 1 — Load all deferred schemas in ONE ToolSearch call

All MCP tools and WebFetch are deferred — they must be fetched before calling. Do this in a single call:

```
ToolSearch query: "select:WebFetch,mcp__claude_ai_Gmail__list_labels,mcp__claude_ai_Google_Calendar__authenticate,mcp__odoo__odoo_count,mcp__google-auth__google_auth_status"
```

If any tool is missing from the result → mark that service as `❌ NOT CONFIGURED` (do not attempt the call). `mcp__google-auth__*` is project-scoped — only present inside the Alice project; if missing, fall back to the file check for Google.

### Step 2 — Fire ALL checks in parallel (single message)

Send one message with all tool calls at once:

- `WebFetch` → `https://www.google.com` (prompt: "Return only: OK")
- `mcp__claude_ai_Gmail__list_labels`
- `mcp__claude_ai_Google_Calendar__authenticate`
- `mcp__odoo__odoo_count` → `{"model": "project.project", "domain": []}`
- `mcp__google-auth__google_auth_status` (if present) — else `Bash` → `ls {ALICE_ROOT}/credentials/google_token.json 2>/dev/null && echo PRESENT || echo MISSING`

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
| Google (Sheets/gateway)      | ❌ NOT CONNECTED     | Say "connect my google" (or run setup/google_gateway_auth.py) |
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
- **Google (Sheets/gateway)** — best signal is `mcp__google-auth__google_auth_status` (project-scoped, auth-only MCP): reports `connected`/`reauthorize`/`no_token`. If that MCP isn't loaded, fall back to checking `credentials/google_token.json` exists. Not connected = say **"connect my google"** (runs `skills/alice-google-connect.md`) or run `setup/google_gateway_auth.py`. Needs `credentials/gateway-config.json`. (Gmail/Calendar Python share the same token file but via the older `setup/google_auth_setup.py` desktop flow.)
- **Internet offline** → all network checks will fail — flag this first.
