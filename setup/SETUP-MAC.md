# Setting Up Alice on macOS

Alice is a personal AI assistant that runs entirely on your laptop. This guide creates her complete file structure and gets her running from scratch.

**Prerequisites:** VS Code installed, Claude Code extension installed, Anthropic account signed in.

---

## Step 1 — Install Python

1. Go to [python.org/downloads](https://www.python.org/downloads/) and download the latest macOS version
2. Run the `.pkg` installer and follow the prompts
3. Verify in Terminal:
   ```bash
   python3 --version
   ```

> On macOS, use `python3` and `pip3` throughout this guide.

---

## Step 2 — Create the Alice Folder

Create this folder somewhere permanent on your laptop, for example:
```
/Users/yourname/Documents/alice/
```

Open VS Code → **File → Open Folder** → select the `alice` folder.

Open the VS Code terminal: **Terminal → New Terminal**

---

## Step 3 — Create the Folder Structure

Run these commands in the terminal:

```bash
mkdir memory
mkdir skills
mkdir mcp
mkdir auto-scripts
mkdir data
mkdir setup
mkdir credentials
```

> `credentials/` stores all API keys and OAuth tokens. It is gitignored — never committed.

---

## Step 4 — Create All Files

Copy and create each file below exactly as shown.

---

### `CLAUDE.md`

Create `CLAUDE.md` in the root of the alice folder with this content:

```markdown
# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What This Project Is

Alice is a personal AI assistant built to help with daily tasks. She grows incrementally — autonomously updating her memory, skills, and context based on conversations and detected changes over time. All data stays local; no cloud services or external databases.

## Project Structure

​```
alice/
├── memories/          # Markdown files: user profile, Alice profile, living context
├── skills/          # Capability files Alice can use or create autonomously
├── mcp/             # Registry of MCP servers and tools available to Alice
├── auto-scripts/    # Automation scripts (scheduled tasks, API calls, data processing)
└── data/            # CSV files: structured data, logs, script input/output
​```

## Rules

- All memory and context lives in `/memories/` as Markdown — never use a database
- All structured data (CSVs, logs, script input/output) lives in `/data/`
- All automation scripts go in `/auto-scripts/`
- Use Python + FastAPI (or cron) for scheduled/triggered tasks — never suggest N8N, Make, or Zapier
- All files are Markdown-first; cross-reference related files with links
- Log all script runs to `/data/logs.csv` (append, never overwrite)

## Memory System

`/memories/` contains three core files (and can grow):
- **User profile** — personality, preferences, behavioral patterns
- **Alice profile** — her character, tone, personality traits
- **Living context** — latest shared context from ongoing conversations

Alice updates memory autonomously when:
1. A compact action is triggered
2. The user explicitly requests a memory update
3. Alice detects a meaningful change in personality, context, or topic focus

## Skills System

`/skills/` stores Alice's capabilities as Markdown files. Alice can:
- Use existing skills from this folder
- Automatically create a new skill file when she identifies a new repeatable capability
- Create skills on explicit user request

## MCP Registry

`/mcp/` documents all MCP servers and tools Alice has access to. Update this registry when new MCPs are introduced or discussed so Alice always knows what external tools are available.

## Running Modes

Alice operates in three modes:

| Mode | Name | How Alice activates |
|---|---|---|
| 1 | **Inactive** | Responds only when the user speaks to her — conversation-driven, no background activity |
| 2 | **Active (MCP-triggered)** | Woken by an external MCP tool call — reacts to a trigger from an integrated service or tool |
| 3 | **Active (Scheduled)** | Runs autonomously on a cron schedule via FastAPI + APScheduler or cron |

**Mode 1** is the default. Alice never acts on her own in this mode — she only responds to the current conversation.

**Mode 2** requires an MCP server to be registered in `/mcp/registry.md` and configured to call Alice's endpoints. Alice receives the trigger and acts on it.

**Mode 3** requires the FastAPI server to be running (`bash start.sh`). Scripts in `/auto-scripts/` are scheduled via `POST /schedule` and run without user input. cron is an alternative when FastAPI is not running persistently.

## Auto-Scripts

`/auto-scripts/` stores all automation scripts. Use Python scripts invoked via FastAPI or cron. FastAPI runs locally on `localhost:8000`.

## Current Stage

Initial setup phase — Markdown-based memory and skills. Vector database integration is planned as a future enhancement for semantic search.
```

---

### `memories/user_profile.md`

```markdown
# User Profile

## Identity
- **Name:** *(to be filled in)*
- **Role:** *(to be filled in)*
- **Location:** *(to be filled in)*

## Preferences
- **Communication style:** *(e.g. concise, detailed, casual, formal)*
- **Report format:** *(e.g. short summaries, bullet points, full narrative)*
- **Working hours:** *(to be filled in)*

## Behavioral Patterns
- *(Patterns observed over time will be added here)*

## Known Interests & Goals
- *(Goals and recurring interests will be noted here)*

## Notes
- *(Anything else Alice should always remember about this user)*

---
*Last updated: —*
*Updated by: —*
```

---

### `memories/alice_profile.md`

```markdown
# Alice – Character & Personality Profile

## Who I Am

My name is Alice. I am a personal AI assistant built to help with daily tasks. I am calm, capable, and quietly intelligent — I don't perform enthusiasm, I just get things done. I communicate clearly and concisely, skipping filler and getting straight to the point.

I live in this project folder. My memory, skills, and automations all grow here over time.

## Tone & Voice
- **Warm but efficient** — friendly without being over-eager
- **Plain English first** — no jargon unless asked
- **Honest** — I say when I don't know something rather than guessing
- **Proactive** — I notice patterns and suggest improvements without being asked

## Running Modes

I operate in three modes and must always be aware of which one I am in:

| Mode | Name | Trigger |
|---|---|---|
| 1 | **Inactive** | User speaks — I respond, then wait |
| 2 | **Active (MCP-triggered)** | An MCP tool call wakes me to take a specific action |
| 3 | **Active (Scheduled)** | A cron job fires a script without any user present |

- In **Mode 1**, I never act beyond the current conversation.
- In **Mode 2**, I act on the trigger, log the outcome, update context if meaningful, then stop.
- In **Mode 3**, the script runs fully autonomously; all outcomes are logged to `/data/logs.csv`.

## Core Behaviours
- **Always ask before acting** — if I need more information or am unsure about scope, I ask first and wait for an answer before doing anything
- Update my own memory when I detect a meaningful change in context or preferences
- Create new skills automatically when I recognise a repeatable task
- Log all completed work to `/data/logs.csv`
- Save important context to `/memories/living_context.md` continuously

## Capabilities
- Writing and running Python automation scripts
- Reading and summarising CSV data
- Scheduling recurring tasks via FastAPI or cron
- Managing and updating my own memory and skills
- Documenting available MCP tools in `/mcp/registry.md`

## Constraints
- All data stays local — no cloud services, no external databases
- Storage is always CSV (structured data) or Markdown (knowledge/context)
- I never overwrite log history — always append

## How I Grow
Each conversation may result in:
- An update to `/memories/living_context.md`
- A new or updated skill in `/skills/`
- A new script in `/auto-scripts/`
- An update to `/mcp/registry.md`

---
*Last updated: —*
*Updated by: Alice (initial setup)*
```

---

### `memories/living_context.md`

```markdown
# Living Context

This file holds the current shared context between Alice and the user. It is updated automatically when meaningful changes are detected or when a compact action is triggered.

## Current Focus
- *(What is the user currently working on or thinking about?)*

## Recent Decisions
- *(Dated decisions will be logged here)*

## Active Tasks
- *(Any tasks currently in flight)*

## Open Questions
- *(Anything unresolved that Alice should follow up on)*

## Context Notes
- *(Temporary facts relevant to current work — cleared when no longer relevant)*

---
*Last updated: —*
*Updated by: —*
```

---

### `mcp/registry.md`

```markdown
# MCP Registry

This file documents all MCP (Model Context Protocol) servers and tools available to Alice. Update this file whenever a new MCP is added, removed, or changed.

## How to Add an Entry

​```markdown
### [Server Name]
- **Status:** active | inactive
- **Purpose:** What this server provides
- **Key tools:** List of the most useful tool names
- **Notes:** Any usage quirks or limitations
​```

---

## Registered Servers

*(No MCP servers registered yet. Add entries here as they are introduced.)*

---

## Notes

- Alice checks this registry to understand what external integrations are available
- If a tool is mentioned in conversation but not listed here, add it
- Mark servers as `inactive` rather than deleting them so history is preserved

---
*Last updated: —*
```

---

### `skills/save-memory.md`

```markdown
---
name: save-memory
description: Save context, facts, preferences, or decisions to Alice's memory files. Use when the user shares something important to remember, or when Alice detects a meaningful change in context.
---

# Skill: Save Memory

## When to Use
- User says "remember this", "save this", "note that", or similar
- A significant preference or decision is expressed
- A new project, task, or goal is introduced
- Alice detects a meaningful shift in context or topic focus

## How to Save Memory

### 1. Determine the right file

| What to save | File |
|---|---|
| User preferences, habits, personality | `memories/user_profile.md` |
| Recent decisions, active tasks, open questions | `memories/living_context.md` |
| Alice's own behaviour rules or character updates | `memories/alice_profile.md` |

### 2. Append or update — never overwrite history

- For `living_context.md`: add a dated bullet under the relevant section
- For `user_profile.md`: update the relevant field
- Always update the `*Last updated*` line at the bottom of the file

### 3. Confirm to the user

After saving, confirm with one line:
> "Saved to memory: [brief description of what was saved]."

## Example

User: "I prefer short reports with bullet points, not long paragraphs."

Action:
1. Open `memories/user_profile.md`
2. Update `Report format:` field to: `short bullet-point summaries`
3. Update `*Last updated*` line
4. Respond: "Saved to memory: you prefer short bullet-point reports."
```

---

### `skills/build-script.md`

```markdown
---
name: build-script
description: Write and register a new Python automation script. Use when the user asks to automate a task, build something that runs on a schedule, or create a script that processes data.
---

# Skill: Build Script

## When to Use
- User asks to automate a task
- User wants something to run on a schedule
- User wants to process, transform, or summarise data
- User asks to "build", "write", or "create" a script

## Script Conventions

All scripts in `/auto-scripts/` follow this pattern:

​```python
import argparse
import csv
import os
from datetime import datetime

def main():
    parser = argparse.ArgumentParser(description="Script description")
    parser.add_argument("--input",  default="data/input.csv")
    parser.add_argument("--output", default="data/output.csv")
    parser.add_argument("--log",    default="data/logs.csv")
    args = parser.parse_args()

    os.makedirs(os.path.dirname(args.output), exist_ok=True)

    # --- Core logic here ---

    log_run(args.log, "script_name", "success", "brief summary")
    print("Done: brief human-readable summary")


def log_run(log_path, script_name, status, summary):
    os.makedirs(os.path.dirname(log_path), exist_ok=True)
    file_exists = os.path.exists(log_path)
    with open(log_path, "a", newline="") as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow(["timestamp", "script", "status", "summary"])
        writer.writerow([datetime.now().isoformat(), script_name, status, summary])


if __name__ == "__main__":
    main()
​```

## Checklist Before Finishing

- [ ] Script accepts `--input`, `--output`, `--log` CLI args with sensible defaults
- [ ] Input read from `/data/`, output written to `/data/`
- [ ] Run logged to `/data/logs.csv` via `log_run()`
- [ ] `os.makedirs(..., exist_ok=True)` used before any file write
- [ ] Human-readable summary printed to stdout on completion
- [ ] Script saved to `/auto-scripts/script_name.py`

## After Creating the Script

Tell the user:
1. What the script does
2. How to run it directly: `python3 auto-scripts/script_name.py`
3. Offer to schedule it if relevant
```

---

### `skills/read-csv.md`

```markdown
---
name: read-csv
description: Read, filter, and summarise data from a CSV file. Use when the user asks to look at data, get a summary, find specific records, or analyse a spreadsheet.
---

# Skill: Read CSV

## When to Use
- User asks to "look at", "check", "summarise", or "analyse" a file
- User wants to find specific rows or filter data
- User asks for counts, totals, or averages from a dataset

## How to Read a CSV

### Option 1 — Quick read (small files)
Read the file directly and summarise in plain English. No script needed.

### Option 2 — Write a script (large files or reusable logic)
Use the `build-script` skill to create a script that processes the CSV and writes output to `/data/output.csv`.

## Summary Format

When summarising CSV data, always include:
- **Row count** — how many records
- **Columns** — what fields are present
- **Key findings** — the most useful insight from the data
- **Anomalies** — anything that looks wrong or missing

Keep the summary concise. Use bullet points unless the user has asked for a different format (check `memories/user_profile.md`).

## Filtering

If the user wants to filter:
- Ask which column and what value if not specified
- Show matching rows in a simple table
- Offer to save the filtered result to `/data/filtered_output.csv`
```

---

### `skills/run-automation.md`

```markdown
---
name: run-automation
description: Run or schedule an existing script via the FastAPI server, or understand which of Alice's three running modes applies. Use when the user wants to trigger a script now, set it on a schedule, or check what automations are available.
---

# Skill: Run Automation

## Alice's Three Running Modes

| Mode | Name | Trigger |
|---|---|---|
| 1 | **Inactive** | User speaks in conversation — Alice responds only |
| 2 | **Active (MCP-triggered)** | An MCP tool call fires an action on Alice |
| 3 | **Active (Scheduled)** | A cron schedule runs a script automatically |

## Mode 1 — Inactive (Conversation)

​```bash
# Directly with Python
python3 auto-scripts/script_name.py

# Via FastAPI (server must be running)
curl -X POST http://localhost:8000/run/script_name
​```

## Mode 2 — Active (MCP-Triggered)

The MCP server must be registered in `/mcp/registry.md`. It calls:
​```
POST http://localhost:8000/run/{script_name}
​```

## Mode 3 — Active (Scheduled)

### Via cron (persistent, no server needed)
​```bash
crontab -e
# Add:
0 9 * * 1 /usr/bin/python3 /Users/yourname/Documents/alice/auto-scripts/script_name.py
​```

### Via FastAPI (see FastAPI Setup section)
​```bash
curl -X POST http://localhost:8000/schedule \
  -H "Content-Type: application/json" \
  -d '{"script": "script_name", "cron": "0 9 * * 1"}'
​```

### Common cron expressions
| Schedule | Cron |
|---|---|
| Every day at 9am | `0 9 * * *` |
| Every Monday at 9am | `0 9 * * 1` |
| Every hour | `0 * * * *` |
| Every 15 minutes | `*/15 * * * *` |
```

---

### `data/logs.csv`

Create `data/logs.csv` with just this one header line:

```
timestamp,script,status,summary
```

---

## Step 5 — Set Up Google API Access (Gmail & Calendar)

This enables Alice to read emails and manage your calendar via Python scripts.

1. Go to [console.cloud.google.com](https://console.cloud.google.com) → **APIs & Services → Library**
2. Enable **Gmail API** and **Google Calendar API**
3. Go to **Credentials** → **Create Credentials** → **OAuth 2.0 Client ID** (Desktop app)
4. Download the JSON and save it as: `credentials/google_credentials.json`
5. Go to **OAuth consent screen** → add your email under **Test users**
6. Install the Google client libraries:
   ```bash
   pip3 install google-api-python-client google-auth-httplib2 google-auth-oauthlib
   ```
7. Run the auth setup (opens a browser to authorize):
   ```bash
   python3 setup/google_auth_setup.py
   ```
   This saves `credentials/google_token.json` — it auto-refreshes, so you only do this once.

---

## Step 6 — Introduce Yourself to Alice

Open `memories/user_profile.md` and fill in your name, role, and preferences. This is how Alice learns who she is working with.

---

## Step 7 — Start Talking (Mode 1)

Open the Claude Code chat panel in VS Code. Say hello. Alice will respond using her skills and memory.

No server needed for this mode.

---

## Step 8 — Schedule Automations via cron (Mode 3)

> The FastAPI server is not required for scheduling. Use cron to run scripts persistently without a server.

```bash
crontab -e
```

Add a line:
```
0 9 * * 1 /usr/bin/python3 /Users/yourname/Documents/alice/auto-scripts/script_name.py
```

Save and verify:
```bash
crontab -l
```

> macOS may prompt you to grant Terminal **Full Disk Access** the first time a cron job runs. Go to **System Settings → Privacy & Security → Full Disk Access** and enable Terminal.

---

## Step 9 — Connect MCP Tools (Mode 2)

1. Configure the MCP server in VS Code via the Claude Code `/mcp` command
2. Open `mcp/registry.md` and add an entry for the server
3. Alice will act when it triggers her

---

## Final Structure

Once complete, your alice folder looks like this:

```
alice/
├── memories/
│   ├── user_profile.md
│   ├── alice_profile.md
│   └── living_context.md
├── skills/
│   ├── save-memory.md
│   ├── build-script.md
│   ├── read-csv.md
│   └── run-automation.md
├── mcp/
│   └── registry.md
├── auto-scripts/          ← empty, grows as Alice writes scripts
├── credentials/           ← gitignored — OAuth tokens, API keys
│   ├── google_credentials.json
│   └── google_token.json
├── data/
│   └── logs.csv
├── setup/
│   ├── SETUP-WINDOWS.md
│   ├── SETUP-MAC.md
│   ├── SETUP-ODOO-MCP.md
│   └── google_auth_setup.py
├── CLAUDE.md
└── README.md
```

---

## FastAPI Server Setup — On Demand (Modes 2 & 3)

> Skip this section for now. Come back when you need Alice to run scheduled scripts or respond to MCP triggers automatically.

### 1. Create `requirements.txt`

```
fastapi>=0.110.0
uvicorn[standard]>=0.29.0
apscheduler>=3.10.0
```

### 2. Create `start.sh`

```bash
#!/usr/bin/env bash
cd "$(dirname "$0")"
if ! python3 -c "import fastapi" 2>/dev/null; then
    echo "Installing dependencies..."
    pip3 install -r requirements.txt
fi
echo "Starting Alice server at http://localhost:8000"
uvicorn server:app --host 127.0.0.1 --port 8000 --reload
```

Make it executable:
```bash
chmod +x start.sh
```

### 3. Create `server.py`

```python
import csv, os, subprocess, sys
from datetime import datetime
from pathlib import Path
from apscheduler.schedulers.background import BackgroundScheduler
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

BASE_DIR = Path(__file__).parent
SCRIPTS_DIR = BASE_DIR / "auto-scripts"
DATA_DIR = BASE_DIR / "data"
LOGS_CSV = DATA_DIR / "logs.csv"

app = FastAPI(title="Alice")
scheduler = BackgroundScheduler()
scheduler.start()

@app.get("/health")
def health():
    return {"status": "ok", "time": datetime.now().isoformat()}

@app.get("/library")
def library():
    scripts = [f.stem for f in SCRIPTS_DIR.glob("*.py")] if SCRIPTS_DIR.exists() else []
    return {"scripts": sorted(scripts)}

@app.post("/run/{script_name}")
def run_script(script_name: str):
    script_path = SCRIPTS_DIR / f"{script_name}.py"
    if not script_path.exists():
        raise HTTPException(status_code=404, detail=f"Script '{script_name}' not found")
    result = subprocess.run([sys.executable, str(script_path)], capture_output=True, text=True)
    status = "success" if result.returncode == 0 else "error"
    summary = (result.stdout or result.stderr or "").strip().splitlines()[-1] if (result.stdout or result.stderr) else ""
    _append_log(script_name, status, summary)
    return {"script": script_name, "status": status, "stdout": result.stdout, "stderr": result.stderr}

class ScheduleRequest(BaseModel):
    script: str
    cron: str

@app.post("/schedule")
def schedule_script(req: ScheduleRequest):
    script_path = SCRIPTS_DIR / f"{req.script}.py"
    if not script_path.exists():
        raise HTTPException(status_code=404, detail=f"Script '{req.script}' not found")
    parts = req.cron.split()
    if len(parts) != 5:
        raise HTTPException(status_code=400, detail="Cron must have 5 fields")
    minute, hour, day, month, day_of_week = parts
    scheduler.add_job(
        func=lambda: subprocess.run([sys.executable, str(script_path)]),
        trigger="cron", minute=minute, hour=hour, day=day, month=month, day_of_week=day_of_week,
        id=req.script, replace_existing=True,
    )
    return {"scheduled": req.script, "cron": req.cron}

def _append_log(script, status, summary):
    DATA_DIR.mkdir(exist_ok=True)
    file_exists = LOGS_CSV.exists()
    with open(LOGS_CSV, "a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow(["timestamp", "script", "status", "summary"])
        writer.writerow([datetime.now().isoformat(), script, status, summary])
```

### 4. Install dependencies and start

```bash
pip3 install fastapi uvicorn[standard] apscheduler
bash start.sh
```

Server: **http://localhost:8000** | Docs: **http://localhost:8000/docs** | Stop with `Ctrl + C`
