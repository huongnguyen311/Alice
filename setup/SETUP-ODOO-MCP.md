# Odoo MCP Setup Guide

Connect Claude Code to the inapps Odoo MCP server to query and manage Odoo data directly from Claude.

**No EC2 access or server setup required — the server is already running.**

---

## Prerequisites

- Claude Code installed (`claude` available in terminal)
- Access to `erp.inapps.net` with your own Odoo account
- This repo cloned locally (`Claude-alice/`)

---

## Step 1 — Generate Your Odoo API Key

1. Go to **https://erp.inapps.net/web/login** and log in with your inapps credentials
2. Click your **name / avatar** in the top-right corner → **My Profile**
3. Click the **Account Security** tab
4. Scroll to the **API Keys** section → click **New API Key**
5. Enter a label (e.g. `claude-code`) → click **Generate Key**
6. **Copy the key immediately** — Odoo only shows it once

> Direct link: https://erp.inapps.net/odoo/settings/users — click your own name

---

## Step 2 — Edit `.mcp.json`

Open `Claude-alice/.mcp.json` and fill in your own email and API key:

```json
{
  "mcpServers": {
    "odoo": {
      "type": "http",
      "url": "https://erp.inapps.net/mcp/",
      "headers": {
        "Authorization": "Bearer your.email@inapps.net:YOUR_API_KEY",
        "X-Odoo-Database": "inapps"
      }
    }
  }
}
```

Replace `your.email@inapps.net` and `YOUR_API_KEY` with your actual credentials. No Base64 encoding needed — the token is `email:api_key` in plain text.

> `.mcp.json` is gitignored — your credentials stay local only.

---

## Step 3 — Run install.py

```bash
python auto-scripts/install.py
```

This syncs `.mcp.json` into `~/.claude.json`, making the Odoo MCP available globally in every Claude Code session on this machine — not just inside this project.

---

## Step 4 — Verify the Connection

```bash
claude mcp list
```

You should see `odoo` listed. Then test it:

```bash
claude "list all Odoo projects"
```

---

## Available Tools

| Tool | What it does |
|---|---|
| `odoo_search` | Search any Odoo model with filters |
| `odoo_get` | Read specific records by ID |
| `odoo_count` | Count matching records |
| `odoo_create` | Create a new record |
| `odoo_write` | Update existing records |
| `odoo_fields` | Discover fields on any model |
| `odoo_comment` | Post a comment or internal note on any record |

---

## Security Notes

- Your API key authenticates you as **yourself** in Odoo — Claude respects your Odoo access rights
- Never share your API key with anyone
- Do not commit `.mcp.json` to the repository — it is gitignored, keep credentials local only
- To revoke: Odoo → My Profile → Account Security → delete the key
- Each team member uses their own API key — no shared credentials, no account login dependency

---

## Troubleshooting

| Error | Cause | Fix |
|---|---|---|
| `401 Unauthorized` | Wrong credentials or missing header | Re-check email and API key in `.mcp.json`, re-run `install.py` |
| `404 Not Found` (HTML page) | Auth missing — Claude tried OAuth discovery | `.mcp.json` has no `Authorization` header — redo Steps 2–3 |
| `Access Denied` from Odoo | Your account lacks permission for that model | Ask an admin to grant access |
| `odoo not found` in `claude mcp list` | MCP not synced globally | Re-run `python auto-scripts/install.py` |

---

*MCP server maintained by: InApps Technology*
*Server: `https://erp.inapps.net/mcp/` (EC2, always-on)*
