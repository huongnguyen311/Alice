---
type: reference
description: Pointers to external systems, credentials, API endpoints, and resource locations Alice needs to access
---

# Reference Memory

## Credentials & Auth

| Resource | Location | Notes |
|---|---|---|
| Google OAuth token (Gmail + Calendar) | `credentials/google_token.json` | Generate once with `python setup/google_auth_setup.py`. Auto-refreshes. Same Google account as MCP (vinh.nguyen@inapps.net). |
| Google OAuth client credentials | `credentials/google_credentials.json` | Prerequisite for `google_auth_setup.py`. Must be placed by user before running setup. Not committed to git. |
| Canva API key | `credentials/canva_api_key.txt` | Not yet set up. Needed for Python batch Canva scripts. Not committed to git. |

---

## External Services

| Service | Account | MCP access | Python access | Notes |
|---|---|---|---|---|
| Gmail | vinh.nguyen@inapps.net | `mcp__claude_ai_Gmail__*` | `google-api-python-client` + `credentials/google_token.json` | MCP for single actions; Python for batch |
| Google Calendar | vinh.nguyen@inapps.net | `mcp__claude_ai_Google_Calendar__*` | `google-api-python-client` + `credentials/google_token.json` | Same token as Gmail |
| Canva | (session account) | `mcp__claude_ai_Canva__*` | Canva REST API + `credentials/canva_api_key.txt` | Python access requires separate API key setup |

---

## Local File Conventions

| Purpose | Path |
|---|---|
| Script outputs | `data/outputs/[script_name]_[YYYYMMDD_HHMMSS].json` |
| Script run log | `data/logs.csv` |
| Email recap log | `data/email_recap_log.csv` |
| Automation scripts | `auto-scripts/[script_name].py` |
| FastAPI server | `localhost:8000` |

---

## Setup Scripts

| Script | Purpose | Run when |
|---|---|---|
| `setup/google_auth_setup.py` | Generate `credentials/google_token.json` | Once before any Python Gmail/Calendar script |

---
*Last updated: 2026-03-25*
*Updated by: Alice*
