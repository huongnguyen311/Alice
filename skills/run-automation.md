---
name: run-automation
description: Run or schedule an existing script via the FastAPI server, or understand which of Alice's three running modes applies. Use when the user wants to trigger a script now, set it on a schedule, or check what automations are available.
scope: automation
triggers:
  - "run"
  - "schedule"
  - "cron"
  - "trigger"
  - "execute script"
  - "set up recurring"
  - "every day"
  - "every week"
  - "automatically"
  - "recurring"
---

# Skill: Run Automation

## Alice's Three Running Modes

| Mode | Name | Trigger |
|---|---|---|
| 1 | **Inactive** | User speaks in conversation — Alice responds only |
| 2 | **Active (MCP-triggered)** | An MCP tool call fires an action on Alice |
| 3 | **Active (Scheduled)** | A cron schedule runs a script automatically |

---

## Mode 1 — Inactive (Conversation)

Alice responds when the user asks. To run a script manually:

```bash
# Via FastAPI (server must be running)
curl -X POST http://localhost:8000/run/script_name

# Directly with Python (always use local venv)
.venv/bin/python auto-scripts/script_name.py
.venv/bin/python auto-scripts/script_name.py --input data/myfile.csv
```

---

## Mode 2 — Active (MCP-Triggered)

An MCP server calls Alice's FastAPI endpoint when a trigger event occurs (e.g. a new email, a file change, an incoming webhook).

The MCP server must be registered in `/mcp/registry.md`. It calls:
```
POST http://localhost:8000/run/{script_name}
```

Alice receives the trigger, runs the relevant script, logs the result, and updates `/memories/living_context.md` if meaningful.

---

## Mode 3 — Active (Scheduled)

### Schedule via FastAPI (server must be running)

```bash
curl -X POST http://localhost:8000/schedule \
  -H "Content-Type: application/json" \
  -d '{"script": "script_name", "cron": "0 9 * * 1"}'
```

### Schedule via Windows Task Scheduler (server not required)

1. Open Task Scheduler → Create Basic Task
2. Set trigger (daily, weekly, on login, etc.)
3. Action: **Start a program**
   - Program: `python`
   - Arguments: `C:\path\to\alice\auto-scripts\script_name.py`
   - Start in: `C:\path\to\alice`

### Common cron expressions

| Schedule | Cron |
|---|---|
| Every day at 9am | `0 9 * * *` |
| Every Monday at 9am | `0 9 * * 1` |
| Every hour | `0 * * * *` |
| Every 15 minutes | `*/15 * * * *` |

---

## Listing Available Scripts

```bash
curl http://localhost:8000/library
```

Or list `/auto-scripts/` directly.

---

## Starting the Server

Required for Mode 2 and Mode 3 (FastAPI scheduling):
```bash
bash start.sh
```

---

## After Scheduling

Confirm to the user which mode is active:
> "Scheduled `script_name` to run [human-readable schedule] — Mode 3 (scheduled). The FastAPI server must be running, or use Windows Task Scheduler for a server-independent alternative."
