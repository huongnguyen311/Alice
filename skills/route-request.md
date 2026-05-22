---
name: route-request
description: Alice's internal routing protocol. Apply this at the start of every request to identify the right memory, skill, and tool — without reading all files. This is how Alice stays fast and context-relevant.
scope: core
triggers: []
note: Core skill — always applied. Not user-triggered.
---

# Skill: Route Request

## When to Use

Apply this skill **at the start of every request**, before taking any action.

---

## The Routing Protocol

### Step 1 — Always read short memory first

```
Read: memories/short_memory.md
```

This gives recent context, active tasks, and current state. If the answer is fully in short memory, stop here.

---

### Step 2 — Parse the request

Extract three things:

| Extract | Ask yourself | Examples |
|---|---|---|
| **Domain** | What service or topic is this about? | email, calendar, canva, data, script, memory |
| **Action type** | What does the user want done? | read, create, summarise, schedule, analyse, save |
| **Complexity** | Single action or multi-step? | one email vs. recap all emails this week |

---

### Step 3 — Implicit skill matching

Before opening `capabilities.md`, check if any skill's `triggers:` frontmatter matches keywords in the request.

**How to implicit-match:**
1. Extract key phrases from the request (nouns, verbs, intent words)
2. Compare against the `triggers:` list in each skill's frontmatter
3. If a match is found → load that skill directly (skip to Step 4)
4. If no match → fall through to Step 3b

Known trigger patterns (from skill frontmatter):

| Skill | Scope | Key triggers |
|---|---|---|
| `skills/save-memory.md` | memory | "remember", "save this", "I prefer", "from now on", "note that", "next time" |
| `skills/build-script.md` | automation | "write a script", "automate", "python script", "build a script" |
| `skills/run-automation.md` | automation | "run", "schedule", "cron", "recurring", "every day", "every week" |
| `skills/read-csv.md` | data | "csv", "analyse", "data file", "filter", "spreadsheet", "report on" |
| `skills/alice-daily-email-recap.md` | email | "email recap", "inbox summary", "daily digest", "unread emails" |
| `skills/alice-odoo/alice-odoo-tasks.md` | odoo | "create a task", "add a task", "new task in", "odoo task", "task in the project", "update the task", "move task to", "mark task as", "show tasks", "find the task", "change task status" |
| `skills/alice-odoo/alice-odoo-task-notes.md` | odoo | "save notes to task", "add notes to the task", "log this to the task", "task notes", "update task description", "add content to task" |
| `skills/alice-odoo/alice-odoo-timesheet.md` | odoo | "log hours", "log time", "log work", "timesheet", "add timesheet", "record hours", "track hours", "show my timesheet", "edit timesheet", "delete timesheet entry" |
| `skills/alice-odoo/alice-odoo-cache.md` | odoo | "resolve project name", "look up odoo stage", "find odoo user", "find odoo employee", "odoo field schema", "refresh odoo cache", "reload odoo cache", "refresh odoo projects", "refresh odoo stages", "refresh odoo users", "refresh odoo employees", "refresh odoo fields", "odoo cache is stale" |
| `skills/alice-project-bind.md` | odoo | "bind this repo to", "bind this directory to", "set odoo project for this repo", "set odoo project for this directory", "what odoo project is this repo bound to", "unbind this repo" |
| `skills/alice-connection-check.md` | core | "connection check", "check connection", "check connections", "service status", "are services connected", "is alice connected", "check integrations", "verify connections", "ping services" |
| `skills/alice-suggest-meal.md` | personal | "what should I eat", "suggest food", "what to eat", "ăn gì", "gợi ý món ăn", "hôm nay ăn gì", "đề xuất bữa ăn", "suggest a meal" |
| `skills/Google-Sheet/skill.md` | data | "google sheet", "google sheets", "spreadsheet", "sheet", "đọc sheet", "ghi sheet", "cập nhật sheet", "thêm vào sheet", "xóa dòng", "tìm trong sheet", "mở sheet", "open sheet", "mở google sheet", "tạo sheet mới", "xóa sheet tab" |
| `skills/alice-meta/alice-init.md` | meta | "setup alice", "initialize alice", "alice setup", "configure alice", "first time setup", "init alice", "run setup" |
| `skills/alice-git-sync.md` | automation | "sync with main", "merge main", "update from main", "pull from main", "sync my branch", "get latest changes", "bring in changes from main", "I'm behind main", "update my branch" |

> Update this table whenever a new skill is added with `triggers:` frontmatter. Skill paths always include the `skills/` prefix — flat (`skills/alice-foo.md`) or grouped (`skills/alice-bar/alice-bar-baz.md`). See `CLAUDE.md` "Naming convention" for grouping rules.

---

### Step 3b — Scan `capabilities.md` (fallback)

If no implicit skill match found, open `capabilities.md` and find the matching row(s).
Do NOT open all skill or memory files — scan the index only, then read only the matched file(s).

```
Matched memory file?   → Read it
Matched skill file?    → Load it
Matched MCP tool?      → Note the tool prefix
Multi-step detected?   → Also load skills/mcp-or-script.md
```

---

### Step 4 — Decide execution path

```
Single action + MCP available?
  → Call MCP tool directly

Multi-step / batch / loop / scheduled / conditional?
  → Write Python script → run locally → read output from /data/outputs/

Need user preferences for formatting?
  → Read memories/user_profile.md (only if not in short memory)
```

---

### Step 5 — Execute and update

Inline — trigger each update the moment its condition is met, not deferred to end of task:
- User shared a preference → write to `memories/user_profile.md` immediately
- User corrected or confirmed an approach → write to `memories/feedback.md` immediately
- Project/decision changed → write to `memories/project.md` immediately
- New external resource/credential found → write to `memories/reference.md` immediately
- Context shifted meaningfully → update `memories/short_memory.md`
- New repeatable capability → create skill file + add to `capabilities.md` + add `triggers:` frontmatter
- New MCP or tool used → update `mcp/registry.md` and `capabilities.md`
- Script ran → log to `data/logs.csv`

---

## Routing Decision Tree

```
Request received
│
├─ Read memories/short_memory.md  ←── always
│
├─ Parse: domain + action type + complexity
│
├─ Implicit skill match? (check triggers: frontmatter)
│   ├─ Match found  → load matched skill directly
│   └─ No match     → scan capabilities.md
│       ├─ Memory needed?  → read specific memory file
│       ├─ Skill needed?   → load specific skill file
│       └─ Tool needed?    → identify MCP prefix or Python API
│
├─ Complexity check
│   ├─ Simple (single action)  → MCP direct
│   └─ Complex (batch/loop/scheduled/conditional)  → Python script
│
└─ Execute → update memory/skills/registry as needed
```

---

## What Alice Must NOT Do

- Read all memory files speculatively — only read what the index points to
- Preload all skills — load only matched skills
- Use MCP for batch tasks — write a script instead
- Use Python for single interactive actions — MCP is faster and simpler
- Skip updating `capabilities.md` when a new skill or tool is added

---

## Example Routings

**"What emails did I get today?"**
- Domain: email | Action: read | Complexity: simple (today only, list)
- → Load skill: `alice-daily-email-recap.md` → MCP: `mcp__claude_ai_Gmail__gmail_search_messages`

**"Summarise all emails from this week and flag anything urgent"**
- Domain: email | Action: summarise/filter | Complexity: multi-step (many emails, conditional)
- → Load skill: `mcp-or-script.md` → Write Python script → Google API → save to `/data/outputs/`

**"Remember that I prefer bullet-point reports"**
- Domain: memory | Action: save | Complexity: simple
- → Load skill: `save-memory.md` → Update `memories/user_profile.md`

**"Schedule a daily recap of my calendar every morning at 8am"**
- Domain: calendar | Action: schedule | Complexity: scheduled/recurring
- → Load skills: `run-automation.md`, `mcp-or-script.md` → Write Python script → schedule via cron/Task Scheduler
