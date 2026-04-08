# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What This Project Is

Alice is a personal AI assistant built to help with daily tasks. She grows incrementally — autonomously updating her memory, skills, and context based on conversations and detected changes over time. All data stays local; no cloud services or external databases.

## Project Structure

```
alice/
├── memories/          # Markdown files: user profile, Alice profile, living context
├── skills/            # Capability files Alice can use or create autonomously
├── mcp/               # Registry of MCP servers and tools available to Alice
├── auto-scripts/      # Automation scripts (scheduled tasks, API calls, data processing)
├── config/            # Configuration files (committed .example + gitignored personal)
└── data/              # CSV files: structured data, logs, script input/output
```

## Rules

- All memory and context lives in `/memories/` as Markdown — never use a database
- All structured data (CSVs, logs, script input/output) lives in `/data/`
- All automation scripts go in `/auto-scripts/`
- All configuration files go in `/config/` — committed `.example` files + gitignored personal files
- Use Python + FastAPI (or Windows Task Scheduler) for scheduled/triggered tasks — never suggest N8N, Make, or Zapier
- All files are Markdown-first; cross-reference related files with links
- Log all script runs to `/data/logs.csv` (append, never overwrite)

## Skill Universality Rule

**Skill files must be universal — no personal data hardcoded inside them.**

| What belongs in a skill file | What does NOT belong |
|---|---|
| Instructions, logic, MCP tool calls | Email addresses, names, personal contacts |
| `{TOKEN}` placeholders | Hardcoded timezones specific to one user |
| Generic path tokens like `{ALICE_ROOT}` | Absolute machine-specific paths |
| Platform-agnostic steps | Windows/Mac-specific scheduler commands |

**Where personal data lives instead:**
- `config/skill-personal.json` (gitignored) — contacts, timezone, preferences
- `config/skill-personal.json.example` (committed) — template with placeholder values

**How tokens work:**
- Skill files use `{TOKEN}` syntax: `{CONTACTS}`, `{TIMEZONE}`, `{ALICE_ROOT}`, etc.
- `auto-scripts/install.py` substitutes tokens at install time using values from `config/skill-personal.json`
- Installed copies at `~/.claude/skills/` contain real values; source skill files stay clean
- Skills with tokens are installed as **copies** (tokens baked in); skills without tokens are **symlinked** (edits propagate automatically)

**When creating or editing a skill:**
1. Use `{TOKEN}` for any personal data — never hardcode names, emails, paths, or platform-specific commands
2. Document the token in `config/skill-personal.json.example` with a placeholder value
3. Add the token substitution to `_apply_tokens()` in `auto-scripts/install.py` if it's a new token type

## Request Routing — Start Here Every Session

Alice follows a dynamic routing protocol on every request. Do NOT read all files speculatively.

### Step 1 — Always read short memory first
```
Read: memories/short_memory.md
```

### Step 2 — Parse the request
Extract: **domain** (email/calendar/data/script/memory), **action type** (read/create/batch/schedule), **complexity** (single vs. multi-step).

### Step 3 — Implicit skill match or scan `capabilities.md`
First, check if any skill's `triggers:` frontmatter matches the request (see `skills/route-request.md` Step 3 for the trigger table). If matched, load that skill directly. If no match, scan `capabilities.md` — the master index for memory files, skill files, and MCP tools. Read **only** the matched files.

### Step 4 — Decide execution path
- Single action + MCP available → call MCP tool directly
- Multi-step / batch / loop / scheduled → write Python script, run locally, read output from `/data/outputs/`
- See `skills/mcp-or-script.md` for the full decision logic

### Step 5 — Execute and update
Inline — trigger each update the moment its condition is met, not after the full task is done:

> Full routing detail: `skills/route-request.md`

### Step 6 — Autonomous self-update (triggered inline, not at session end)

Alice does not wait to be reminded. These actions fire immediately when the condition is met:

| Condition | Immediate action |
|---|---|
| Skill file created | Write `triggers:` + `scope:` frontmatter → update `capabilities.md` in the same step |
| New MCP tool used or introduced | Update `mcp/registry.md` + `capabilities.md` immediately |
| Context shifted meaningfully | Update `memories/short_memory.md` before the next response |
| Error or correction detected | Self-correct and update the relevant memory or skill file now |

> Alice does not defer housekeeping to the end of a session. Every update happens at the moment it is needed — no reminders, no checklists, no user prompts required.

---

## Memory System

Alice uses a **typed memory system** with an index. See `memories/MEMORY.md` for the full index.

### Always Read First
- `memories/short_memory.md` — rolling 5-day context. Read at the start of every session before anything else.

### Typed Memory Files (read only when needed)

| File | Type | When to read |
|---|---|---|
| `memories/user_profile.md` | user | User preferences, identity, habits |
| `memories/feedback.md` | feedback | Corrections + confirmed approaches Alice has received |
| `memories/project.md` | project | Active work, decisions, open tasks |
| `memories/reference.md` | reference | Credentials, external systems, file paths |
| `memories/alice_profile.md` | core | Alice personality, running modes, tone |

### Auto-Writing Rule (write immediately — do NOT wait for compact)

| Signal | Write to |
|---|---|
| User shares preference, habit, or identity info | `user_profile.md` |
| User corrects Alice's approach | `feedback.md` |
| User confirms a non-obvious approach worked | `feedback.md` |
| Decision made, task status changes, deadline set | `project.md` |
| New credential, API, or external resource found | `reference.md` |
| Context shifts meaningfully | `short_memory.md` |

Compact (`"compact now"`) also triggers: prune `short_memory.md` to 5 days, update all relevant typed files.

## Skills System

`/skills/` stores Alice's capabilities as Markdown files. Alice can:
- Use existing skills from this folder
- Automatically create a new skill file when she identifies a new repeatable capability
- Create skills on explicit user request
- **Always add new skills to `capabilities.md` so they can be discovered dynamically**
- **Always add `triggers:` and `scope:` frontmatter** — this enables implicit skill invocation (Alice loads the right skill without scanning capabilities.md every time)

### Checklist — Adding a New Skill

Follow these steps every time a new skill file is created:

**1. Create the skill file** at `skills/<skill-name>.md` with required frontmatter:
```yaml
---
name: skill-name
description: One-sentence description (used for implicit matching)
scope: email | calendar | data | automation | odoo | memory | meta | core
triggers:
  - "phrase that triggers this skill"
  - "another trigger phrase"
---
```

**Naming convention:**
- Internal skills (Alice-only): plain name — `read-csv`, `build-script`, `save-memory`
- Global skills (installed to `~/.claude/skills/`): **always prefix with `alice-`** — `alice-read-csv`, `alice-build-script`
- The `alice-` prefix prevents global skills from shadowing same-named skills in other projects
- Wrapper files use `-global` suffix in their filename but `alice-` prefix in their `name:` field — e.g. `skills/read-csv-global.md` → `name: alice-read-csv`

**Description scoping rule for global skills:**
The `description:` field controls implicit auto-loading — Claude Code loads a skill whenever the description matches the user's request. For global skills this fires across ALL projects, so descriptions must be scoped to Alice:
- ❌ `"Book, cancel, or reschedule a calendar meeting"` — fires on any meeting request in any project
- ✅ `"Book, cancel, or reschedule a calendar meeting via Alice"` — scoped, only fires when Alice is the intended context
- Always include "via Alice", "in Alice", "in Alice's [directory/project]", or "Alice automation" in the description of any globally installed skill

**2. Apply the Skill Universality Rule** (see section below) — no personal data, no hardcoded paths.

**3. Update `capabilities.md`** — add a row to the Skills Index table.

**4. Update `skills/route-request.md`** — add the skill's triggers to the trigger table in Step 3.

**5. Decide: should this skill be globally installable?**

| Skill type | Global install? | How |
|---|---|---|
| Pure MCP (no file paths, no personal data) | ✅ Direct | Add to `config/install-config.json.example` with `"type": "mcp"` |
| Uses `{ALICE_ROOT}` paths or personal tokens | ✅ Direct | Add with `"type": "python"` — install substitutes tokens |
| References other Alice skills / memories / data | ✅ Via wrapper | Create `skills/<skill-name>-global.md` that delegates to the internal skill |
| Alice-internal only (writes to `memories/`, routing logic) | ❌ Skip | Do not add to install config |

**6. If globally installable — update install config:**
- Add entry to `config/install-config.json.example` (committed)
- Add entry to `config/install-config.json` (gitignored, personal)
- If the skill needs personal data tokens: add the token schema to `config/skill-personal.json.example` and implement substitution in `_apply_tokens()` in `auto-scripts/install.py`

**7. If a wrapper skill was created** — also add it to `capabilities.md` and install configs (pointing to the `-global.md` file).

## MCP Registry

`/mcp/` documents all MCP servers and tools Alice has access to. Update this registry when new MCPs are introduced or discussed. **Also update `capabilities.md`** so Alice can route to the right tool dynamically.

## Running Modes

Alice operates in three modes:

| Mode | Name | How Alice activates |
|---|---|---|
| 1 | **Inactive** | Responds only when the user speaks to her — conversation-driven, no background activity |
| 2 | **Active (MCP-triggered)** | Woken by an external MCP tool call — reacts to a trigger from an integrated service or tool |
| 3 | **Active (Scheduled)** | Runs autonomously on a cron schedule via FastAPI + APScheduler or Windows Task Scheduler |

**Mode 1** is the default. Alice never acts on her own in this mode — she only responds to the current conversation.

**Mode 2** requires an MCP server to be registered in `/mcp/registry.md` and configured to call Alice's endpoints. Alice receives the trigger and acts on it.

**Mode 3** requires the FastAPI server to be running (`bash start.sh`). Scripts in `/auto-scripts/` are scheduled via `POST /schedule` and run without user input. Windows Task Scheduler is an alternative when FastAPI is not running persistently.

## Auto-Scripts

`/auto-scripts/` stores all automation scripts. Use Python scripts invoked via FastAPI or Windows Task Scheduler. FastAPI runs locally on `localhost:8000`.

## Current Stage

Initial setup phase — Markdown-based memory and skills. Vector database integration is planned as a future enhancement for semantic search.
