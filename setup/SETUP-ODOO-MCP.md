# Odoo MCP Setup Guide

Connect Claude Code to the inapps Odoo MCP server to query and manage Odoo data directly from Claude.

**No EC2 access or server setup required — the server is already running.**

---

## Prerequisites

- Claude Code installed (`claude` available in terminal)
- Access to `erp.inapps.net` with your own Odoo account

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

## Step 2 — Build Your Auth Token

Run this in your terminal (replace with your actual email and API key):

```bash
echo -n 'your.email@inapps.net:YOUR_API_KEY' | base64
```

Copy the output — this is your `BASE64_TOKEN`.

**Example:**
```bash
echo -n 'vinh.nguyen@inapps.net:abc123xyz' | base64
# Output: dmluaC5uZ3V5ZW5AaW5hcHBzLm5ldDphYmMxMjN4eXo=
```

---

## Step 3 — Register the MCP in Claude Code

Run this once in your terminal:

```bash
claude mcp add --transport http odoo https://erp.inapps.net/mcp/ --header "Authorization: Basic BASE64_TOKEN"
```

Replace `BASE64_TOKEN` with the output from Step 2.

This registers the MCP at **user scope** — it applies to all your Claude Code sessions.

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
- Never share your API key or Base64 token with anyone
- Do not commit `.mcp.json` to the repository — keep credentials local only
- To revoke: Odoo → My Profile → Account Security → delete the key

---

## Troubleshooting

| Error | Cause | Fix |
|---|---|---|
| `401 Unauthorized` | Wrong credentials or missing header | Re-run Steps 2–3 with correct key |
| `404 Not Found` (HTML page) | Auth missing — Claude tried OAuth discovery | `.mcp.json` has no `Authorization` header — redo Step 3 |
| `Access Denied` from Odoo | Your account lacks permission for that model | Ask an admin to grant access |
| `odoo not found` in `claude mcp list` | Registration didn't complete | Re-run the `claude mcp add` command |

---

*MCP server maintained by: Vinh Nguyen*
*Server: `https://erp.inapps.net/mcp/` (EC2, always-on)*
