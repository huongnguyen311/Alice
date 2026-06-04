---
name: alice-google-connect
description: "Connect or reconnect Alice to Google (Sheets/Docs) via the easy-auth gateway — one-click consent. Only invoke when the user explicitly addresses Alice, e.g. 'alice connect google' / 'alice reconnect google'. Do NOT auto-load on generic mentions of connecting or authorizing Google."
scope: core
triggers:
  - "alice connect google"
  - "alice reconnect google"
  - "alice connect my google"
  - "alice link google"
  - "alice authorize google"
  - "alice kết nối google"
  - "alice đăng nhập google"
---

# Skill: Connect Google (gateway)

One-command Google (Sheets/Docs) connect for Alice, powered by the **project-scoped
`google-auth` MCP** (`mcp__google-auth__*`). The MCP does **auth only** — it mints the
token via the easy-auth gateway and writes `credentials/google_token.json`. The actual
Sheets work stays in `skills/Google-Sheet/skill.md`.

> **Project-scoped:** this skill + the `google-auth` MCP only work **inside the Alice
> project**. They are not installed globally.

---

## When to use

- User asks to connect / reconnect / authorize Google.
- A Sheets action failed because the token is missing or revoked
  (`google_auth_status` → `reauthorize` / `no_token`).

---

## Steps

### 1. Load the MCP tool schemas (they are deferred)

```
ToolSearch query: "select:mcp__google-auth__google_auth_status,mcp__google-auth__connect_google,mcp__google-auth__finish_google_connect"
```

If `mcp__google-auth__*` tools are **not** found → the MCP isn't loaded. Tell the user:
> "The Google auth MCP isn't loaded. Make sure you're in the Alice project and that
> `credentials/gateway-config.json` exists (copy from `.example`), then restart Claude Code."

### 2. Check status first

Call `mcp__google-auth__google_auth_status`.

| Result | Action |
|---|---|
| `connected: true` | Tell the user Google is already connected (show scopes + expiry). Stop unless they want to reconnect. |
| `reason: no_token` / `reauthorize` | Proceed to connect (step 3). |
| `reason: config` | Gateway config missing — tell user to create `credentials/gateway-config.json` from the `.example`. |

### 3. Connect (one-click)

Call `mcp__google-auth__connect_google`.

- It opens the Google consent page in the browser. Tell the user: **"Click Allow in the
  browser tab that just opened."**
- On `ok: true` → confirm connected, show the granted scopes.
- On `error: timeout` → the gateway may not support localhost redirect yet. Fall back to
  step 4 with the JSON shown on the callback page.
- On `error: config` → gateway config missing/placeholder.

### 4. Paste fallback (only if step 3 times out)

If the gateway can't redirect to localhost, the callback page shows a JSON blob. Ask the
user to paste it, then call:

```
mcp__google-auth__finish_google_connect(callback_json="<the pasted JSON>")
```

---

## Notes

- **No Sheets/Docs calls here** — this skill is auth only. After connecting, route Sheets
  requests to `skills/Google-Sheet/skill.md` as usual (its pre-flight refresh keeps the
  token fresh via the gateway).
- Connecting **overwrites** `credentials/google_token.json` with Sheets scopes
  (`spreadsheets` + `drive.readonly`). Gmail/Calendar Python scripts that share that file
  must re-auth via `setup/google_auth_setup.py` if needed.
- Full gateway protocol: `setup/google-gateway-INTEGRATION.md`. Setup guide:
  `setup/google-sheets-setup.md`.
