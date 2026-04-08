---
name: mcp-or-script
description: Alice's decision framework for choosing between calling MCP tools directly vs. writing a Python script. Use this skill at the start of any task that involves external services (Gmail, Calendar, Canva).
scope: decision
triggers: []
note: This skill is loaded by route-request during Step 4 for multi-step tasks. Not triggered directly by user phrases.
---

# Skill: MCP Direct vs. Python Script

## Decision Rule

```
Single action, one result needed?
  → Call MCP directly in conversation

Multi-step, batch, loop, conditional, or scheduled?
  → Write Python script → run locally → read output from /data/outputs/
```

## Decision Table

| Task type | Example | Approach |
|---|---|---|
| Read one email | "What does this email say?" | MCP direct |
| Create one calendar event | "Book a meeting tomorrow at 3pm" | MCP direct |
| Search and return a list | "Find emails from John this week" | MCP direct (if just listing) |
| Summarise many emails | "Recap all emails from today" | Python script |
| Batch create events | "Add these 10 events to my calendar" | Python script |
| Conditional logic | "If email has invoice, extract amount" | Python script |
| Scheduled/automated task | Daily email recap, weekly report | Python script (Mode 3) |
| Multi-service task | "Check email + calendar + summarise" | Python script |

---

## How MCP Tools Work (and Why Python Cannot Use Them)

Alice's MCP servers (`mcp__claude_ai_Gmail__*`, `mcp__claude_ai_Google_Calendar__*`, `mcp__claude_ai_Canva__*`) are **hosted remotely by Anthropic**. They authenticate using Alice's Claude.ai session — not a local API key.

**Python scripts cannot connect to these MCP servers directly.**

For Python automation, Alice calls the underlying services directly using their own APIs:

| Service | Python library | Credential file |
|---|---|---|
| Gmail | `google-api-python-client` | `credentials/google_token.json` |
| Google Calendar | `google-api-python-client` | `credentials/google_token.json` |
| Canva | `requests` (REST API) | `credentials/canva_api_key.txt` or env var |

---

## Python Script Pattern

Every script that calls an external service follows this structure:

```python
# auto-scripts/[script_name].py
import json
from pathlib import Path
from datetime import datetime

OUTPUT = Path("data/outputs") / f"[name]_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"

# 1. Authenticate
creds = load_credentials("credentials/google_token.json")

# 2. Call the service API directly
service = build("gmail", "v1", credentials=creds)
results = service.users().messages().list(...).execute()

# 3. Process data locally (filter, aggregate, loop — no extra model round-trips)
output = process(results)

# 4. Save to /data/outputs/
OUTPUT.parent.mkdir(exist_ok=True)
OUTPUT.write_text(json.dumps(output, indent=2))
print(f"Done. Output: {OUTPUT}")
```

Alice then reads the output file and synthesises the answer.

---

## Credential Setup (One-Time)

Before any Python script can call Google services, run the setup once:

```bash
python setup/google_auth_setup.py
```

This generates `credentials/google_token.json` using the same Google account as the MCP.
Token auto-refreshes — only needs to be done once (or if revoked).

For Canva: store the API key in `credentials/canva_api_key.txt` (not committed to git).

---

## Output Convention

All script outputs go to:
```
data/outputs/[script_name]_[YYYYMMDD_HHMMSS].json
```

Alice reads the most recent file matching the script name to get the result.

---

## Summary

- **MCP direct** = fast, interactive, single action, no setup
- **Python script** = batch, logic, scheduled, multi-step — calls Google/Canva APIs directly, not through MCP
- Credentials for Python are **separate from MCP** but access the same account
