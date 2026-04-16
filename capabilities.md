# Alice — Capability Index

This is Alice's **master routing index**. Scan this file first to identify which memory, skill, or MCP is relevant to a request. Do NOT read all files — read only what this index points to.

---

## How to Use This Index

1. Extract keywords and intent from the user's request
2. Find the matching row(s) below
3. Read only the files listed in that row
4. If action is multi-step or batch → also load `skills/mcp-or-script.md`

---

## Memory Index

> **Primary index:** `memories/MEMORY.md` — scan this for full memory routing detail.

| Topic | Type | Keywords | File to read |
|---|---|---|---|
| Recent context, active tasks, last 5 days | context | anything — read this first always | `memories/short_memory.md` |
| User identity, preferences, communication style | user | "how does user prefer", "report format", "user habits", "I prefer" | `memories/user_profile.md` |
| Alice personality, tone, running modes | core | "how should I respond", "Alice behaviour", "which mode" | `memories/alice_profile.md` |
| Corrections and confirmed approaches | feedback | "don't do that", "stop", "yes exactly", "keep doing that" | `memories/feedback.md` |
| Ongoing decisions, active work, open questions | project | "what were we working on", "current status", "open tasks" | `memories/project.md` |
| Credentials, APIs, external systems, file paths | reference | "api key", "token", "credential", "where is", "which endpoint" | `memories/reference.md` |

> **Rule:** Always read `short_memory.md` first. Read typed memory files only when the short memory does not have enough context.

---

## Skills Index

| Task type | Keywords | Skill file |
|---|---|---|
| Save something to memory | "remember", "save", "note", "update profile" | `skills/save-memory.md` |
| Write a new automation script | "write a script", "automate", "python script" | `skills/build-script.md` |
| Run or schedule a script | "run", "schedule", "trigger", "cron" | `skills/run-automation.md` |
| Read, summarise, or analyse a CSV | "data", "csv", "log", "analyse", "report" | `skills/read-csv.md` |
| Daily email digest | "email recap", "inbox summary", "daily digest" | `skills/alice-daily-email-recap.md` |
| Book, cancel, or reschedule a meeting | "book a meeting", "schedule", "cancel meeting", "reschedule", "move meeting" | `skills/alice-book-meeting.md` |
| Decide MCP vs Python script | multi-step, batch, loop, conditional, scheduled | `skills/mcp-or-script.md` |
| Create, find, update, or change stage of Odoo tasks | "odoo task", "task in project", "create task", "add a task", "move task", "mark task", "show tasks", "find the task" | `skills/alice-odoo-tasks.md` |
| Save structured notes or content to an Odoo task | "task notes", "save notes to task", "log to task", "add content to task", "update task description" | `skills/alice-odoo-task-notes.md` |
| Check connectivity of Alice's services and MCP tools | "connection check", "check connection", "service status", "are services connected", "is alice connected" | `skills/alice-connection-check.md` |
| Suggest what to eat — Vietnamese-focused meal suggestions | "what to eat", "suggest food", "ăn gì", "gợi ý món ăn", "suggest a meal", "hôm nay ăn gì" | `skills/alice-suggest-meal.md` |
| Read, write, update, delete, search, open Google Sheets | "google sheet", "spreadsheet", "sheet", "đọc sheet", "ghi sheet", "cập nhật sheet", "thêm vào sheet", "xóa dòng", "tìm trong sheet", "mở sheet", "open sheet" | `skills/Google-Sheet/skill.md` |
| Install Alice skills globally | "install alice", "install alice skills", "make alice skills global" | `skills/alice-install.md` |
| Uninstall Alice global skills | "uninstall alice", "uninstall alice skills", "remove alice skills" | `skills/alice-uninstall.md` |
| Global wrapper: read/analyse CSV from any project (`/alice-read-csv`) | (same as read-csv) | `skills/alice-read-csv.md` |
| Global wrapper: build Alice automation script from any project (`/alice-build-script`) | (same as build-script) | `skills/alice-build-script.md` |
| Global wrapper: run/schedule Alice automation from any project (`/alice-run-automation`) | (same as run-automation) | `skills/alice-run-automation.md` |

> **Rule:** Skills with matching `triggers:` frontmatter are loaded implicitly (see `skills/route-request.md` Step 3). This table is the fallback when no trigger match is found. Do not preload all skills.

---

## MCP + Tool Index

| Domain | Keywords | MCP tool prefix | Python alternative | Use MCP when | Use Python when |
|---|---|---|---|---|---|
| Email / Gmail | "email", "inbox", "message", "gmail", "draft", "thread" | `mcp__claude_ai_Gmail__` | `google-api-python-client` + `credentials/google_token.json` | Single read/search/draft | Batch, loop, summarise many |
| Calendar | "calendar", "meeting", "event", "schedule", "availability", "slot" | `mcp__claude_ai_Google_Calendar__` | `google-api-python-client` + `credentials/google_token.json` | Single event create/read | Multi-event, availability scan |
| Design / Canva | "design", "canva", "poster", "visual", "banner", "image" | `mcp__claude_ai_Canva__` | Canva REST API + `credentials/canva_api_key.txt` | Interactive design work | Batch design operations |
| Google Sheets | "sheet", "google sheet", "spreadsheet" | — | `google-api-python-client` + `credentials/google_token.json` | Never — use Python skill | Always — see `skills/Google-Sheet/skill.md` |
| Local data | "csv", "log", "output", "data file" | — | `pathlib`, `csv`, `json` (built-in) | Never — no MCP for local files | Always |
| Python scripts | "run", "execute", "auto-script" | — | `subprocess` or FastAPI `/run/` | Never | Always |
| Odoo ERP | "task", "project", "odoo", "erp", "stage", "crm" | `mcp__odoo__` | No Python equivalent — use MCP directly | Single record operations | Batch exports via Odoo REST API |

> **Rule:** See `skills/mcp-or-script.md` for the full decision logic. In short: single action → MCP. Batch/loop/scheduled → Python script.

---

## Action Complexity Guide

| Signal in request | Complexity | Approach |
|---|---|---|
| "read", "check", "what is", "show me" + single subject | Simple | MCP direct |
| "summarise", "recap", "all", "this week", "multiple" | Multi | Python script |
| "every day", "schedule", "automatically", "recurring" | Scheduled | Python script (Mode 3) |
| "if ... then", "filter", "find all that", "for each" | Conditional | Python script |
| Mixed services ("email and calendar") | Cross-service | Python script |

---

## Growing This Index

When Alice creates a new skill, memory file, or uses a new MCP:
- Add a row to the relevant section above
- Keep descriptions short — this file must stay scannable

---
*Last updated: 2026-04-16 (Google Sheets CRUD skill added)*
