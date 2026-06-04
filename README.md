# Alice

Alice is a personal AI assistant that lives entirely on your laptop. She helps with daily tasks, builds automations on request, and grows smarter over time — updating her own memory, skills, and context as she learns more about you.

All data stays local. No cloud. No external databases.

---

## How Alice Works

You talk to Alice in VS Code via Claude Code. Depending on what's needed, she operates in one of three modes:

| Mode | Name | How it activates |
|---|---|---|
| 1 | **Inactive** | You speak — Alice responds, then waits |
| 2 | **Active (MCP-triggered)** | An external tool or service wakes Alice via MCP |
| 3 | **Active (Scheduled)** | A cron job runs a script automatically, no input needed |

---

## Structure

```
alice/
├── memories/          # Who Alice is, who you are, what's happening now
├── skills/            # Things Alice knows how to do
├── mcp/               # External tools and integrations Alice has access to
├── auto-scripts/      # Python scripts Alice writes and runs
├── credentials/       # OAuth tokens and API keys — gitignored, never committed
├── data/              # CSV files — structured data, logs, script output
├── setup/             # One-time setup scripts (Google auth, etc.)
├── server.py          # FastAPI server (run, schedule, memory, data endpoints)
└── start.sh           # Start the server: bash start.sh
```

---

## Memory

Alice keeps three core memory files:

| File | Purpose |
|---|---|
| [memories/user_profile.md](memories/user_profile.md) | Your preferences, personality, patterns |
| [memories/alice_profile.md](memories/alice_profile.md) | Alice's character, tone, running modes |
| [memories/living_context.md](memories/living_context.md) | Current focus, recent decisions, open questions |

Alice updates memory when she detects a meaningful change, when you ask her to, or when a compact action is triggered.

---

## Skills

Skills in `/skills/` are Markdown instruction files Alice reads to know how to handle certain tasks. They grow over time.

| Skill | When it's used |
|---|---|
| [save-memory](skills/save-memory.md) | Remembering something important |
| [build-script](skills/build-script.md) | Writing a new automation |
| [read-csv](skills/read-csv.md) | Reading and summarising data |
| [run-automation](skills/run-automation.md) | Running or scheduling a script |

---

## Starting Alice's Server

Required for MCP-triggered and scheduled modes:

```bash
bash start.sh
```

Server runs at `http://localhost:8000`. API docs at `http://localhost:8000/docs`.

---

## Design Principles

- **Incremental** — Alice grows smarter with every conversation
- **Autonomous** — she updates herself without always being asked
- **Local-first** — everything stays on your machine
- **Markdown + CSV only** — no databases, no setup, human-readable files

---

## Setup (first time)

Personal files are gitignored — you need to copy the example files and fill in your own values.

**1. Personal config** (identity, contacts, timezone):
```bash
cp config/skill-personal.json.example config/skill-personal.json
cp config/install-config.json.example config/install-config.json
```
Edit `config/skill-personal.json` — fill in your name, email, timezone, etc. in the `_user` section.

**2. Personal memory files** (Alice reads these to know who you are):
```bash
cp memories/user_profile.md.example memories/user_profile.md
cp memories/reference.md.example    memories/reference.md
cp memories/short_memory.md.example memories/short_memory.md
cp memories/project.md.example      memories/project.md
```
Edit `memories/user_profile.md` — fill in your name, role, location, and preferences.

**3. Install skills globally:**
```bash
python auto-scripts/install.py
```
This bakes your personal config into the installed skill copies at `~/.claude/skills/`.

**4. (Optional) Google API access**

- **Gmail & Calendar** Python scripts (desktop OAuth):
  ```bash
  python setup/google_auth_setup.py
  ```
- **Google Sheets** (easy-auth gateway — no local Google `client_secret`):
  ```bash
  cp credentials/gateway-config.json.example credentials/gateway-config.json   # fill in gate creds
  ```
  Then just tell Alice **"connect my google"** — a one-click consent (no copy-paste) via
  the project-scoped `google-auth` MCP. Manual fallback: `python setup/google_gateway_auth.py`.
  See `setup/google-sheets-setup.md`.

> Full platform-specific guide: `setup/SETUP-MAC.md` or `setup/SETUP-WINDOWS.md`
