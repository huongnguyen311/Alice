---
name: alice-odoo-timesheet
description: Log, view, edit, or delete Odoo timesheet entries via Alice. Asks clarifying questions for missing project/task/hours/description.
scope: odoo
triggers:
  - "log hours"
  - "log time"
  - "log work"
  - "timesheet"
  - "add timesheet"
  - "record hours"
  - "track hours"
  - "log my work"
  - "show my timesheet"
  - "what did I log"
  - "edit timesheet"
  - "delete timesheet entry"
mcp_required: odoo
mcp_scope: global
---

# Skill: Odoo Timesheet

## Execution Strategy

Use `odoo_search`, `odoo_create`, `odoo_write`, `odoo_get`, `odoo_fields` directly. The Odoo MCP is configured globally and available in every session.

**Model:** `account.analytic.line` — timesheet entries are analytic lines with `project_id` set.

**MCP parameter rules** — the tool schema is source of truth; do NOT use Odoo XML-RPC conventions in MCP calls:
- `odoo_get` takes `ids=[<int>, ...]` (array), never `id=<int>` (singular)
- `odoo_execute` takes `ids=[...]` and optional `kwargs={}` — there is no `args` parameter. To delete records, use `method="unlink"` with `ids=[...]`
- `odoo_fields` takes only `model` — no `fields=` filter
- All `domain`, `fields`, `ids` values must be native JSON arrays, never stringified

### How to delegate to alice-odoo-cache

Whenever this skill says "delegate to the alice-odoo-cache skill" (projects, employees, users, field schemas), **invoke it via the Skill tool** — do NOT read the cache skill file with the Read tool.

```
Skill(skill="alice-odoo-cache", args="resolve project name '<q>'")
Skill(skill="alice-odoo-cache", args="find employee for '{USER_EMAIL}'")
Skill(skill="alice-odoo-cache", args="check fields for model 'account.analytic.line'")
```

Reading the cache file inline bypasses the skill's runtime, skips cache file I/O, and leaves the manifest unwritten — the next session will then re-query Odoo for data already on disk. Always go through the Skill tool.

**MCP parameter types — always pass native JSON, never strings:**
- `fields`: array of strings → `["id", "name"]`, not `"[\"id\", \"name\"]"`
- `domain`: array of triplets → `[["name", "ilike", "foo"]]`, not a stringified version
- `ids`: array of integers → `[42]`, not `"[42]"`
- Passing a serialized string where an array is expected causes: `'[...]' is not of type 'array'`

---

## When to Use

Use this skill when the user wants to **log, view, edit, or delete work hours** in Odoo. Triggers: "log 2 hours on…", "track time on…", "show my timesheet", "edit the entry from yesterday", etc.

- For changing a **task's** fields (stage, deadline, assignee) → use `skills/alice-odoo/alice-odoo-tasks.md`
- For writing **prose notes** to a task description → use `skills/alice-odoo/alice-odoo-task-notes.md`

This skill is the foundation for a future report skill (planned separately). Two habits keep the data report-ready:
1. **Description is required** — never create an entry with an empty `name`. If missing, ask.
2. **Task is strongly preferred** — if the user gives only a project, ask once: *"Which task on that project? (or say 'no task' to log against the project directly)"*. Project-only entries are allowed but call them out in the confirmation so the user knows they'll show up as "Unassigned" in future reports.

---

## Clarifying Questions Protocol

Ask **all** missing required fields in **one message** — never one at a time.

| Action | Required | Optional | Ask if required missing |
|---|---|---|---|
| Log entry | Hours, description, project (or task) | Date (defaults to today), task (asked once if only project given) | "How many hours, on which task/project, and what's the description?" |
| Batch log | Same per entry | Same | If any entry is missing fields, list them in one message and ask for all gaps at once |
| View entries | Date range | — | Defaults to today if not specified |
| Edit entry | Entry identity, new value | — | "Which entry — by ID, or by date + project + hours?" |
| Delete entry | Entry identity | — | Always confirm: "Delete entry [N] hours on [task] from [date]?" |

**Rule:** Batch all missing-field questions into a single message. Never ask field by field.

> **Project name is auto-resolved from `.alice/project.md` if present.** See **Auto-resolve Project from Binding** below — when a repo binding exists, don't ask "which project?"; use the binding silently.

---

## Field Discovery

Some Odoo installs customize the timesheet model. **Invoke `Skill(skill="alice-odoo-cache", args="check fields for model 'account.analytic.line'")`** — the cache persists the schema across sessions so this only runs against Odoo once per instance.

Verify these fields are present: `name`, `date`, `unit_amount`, `project_id`, `task_id`, `employee_id`, `user_id`. If any are missing or renamed, ask the user before proceeding.

---

## Resolve Employee Identity

Timesheet entries belong to an `hr.employee`, not directly to `res.users`.

**Invoke `Skill(skill="alice-odoo-cache", args="find employee for '{USER_EMAIL}'")`** (exact match on `work_email`) with fuzzy fallback on `{USER_NAME}` (`Skill(skill="alice-odoo-cache", args="find employee matching '{USER_NAME}'")`). If the cache returns no match after the full escalation ladder, ask: "What's your Odoo employee name?"

> **Never call `odoo_search` for `hr.employee` or `res.users` directly, and never Read the cache skill file** — always invoke alice-odoo-cache via the Skill tool so the lookup result is persisted to `employees.json` / `users.json` for next session.

Pass `employee_id` explicitly when creating entries even though most Odoo configs auto-fill it from the logged-in user.

---

## Auto-resolve Project from Binding

This is **Step A of Resolve Project Name** — it runs first, before any cache delegation. Check for a per-repo binding written by the **alice-project-bind** skill:

```bash
test -f .alice/project.md && cat .alice/project.md
```

If the file exists, parse the two-fact schema:

```bash
ID=$(grep -E '^- Odoo Project ID:' .alice/project.md | sed -E 's/^- Odoo Project ID:[[:space:]]*//')
NAME=$(grep -E '^- Odoo Project Name:' .alice/project.md | sed -E 's/^- Odoo Project Name:[[:space:]]*//')
```

Use `(ID, NAME)` as the resolved project — **skip the cache delegation entirely** for this lookup. Append `(via repo binding)` to the confirmation line so the user knows.

**User input always wins.** If the user explicitly names a project in their request (e.g. *"log 2 hours on [Project] TRS bug fix"*), use the explicit name and ignore the binding — run the normal cache delegation below.

If `.alice/project.md` doesn't exist, fall through to **Resolve Project Name** below.

---

## Resolve Project Name

**This is the single entry point for project resolution.** Every action below (Log / Batch Log / View / Edit / Delete) MUST go through these steps in order — do NOT skip straight to the cache.

**Step A — Binding check (always first).** Run the **Auto-resolve Project from Binding** section above. If `.alice/project.md` exists AND the user did not explicitly name a different project in their request, use the binding's `(ID, NAME)` and **stop** — do not invoke the cache for this lookup. Append `(via repo binding)` to the confirmation.

**Step B — Cache delegation (only if Step A did not resolve).** Invoke `Skill(skill="alice-odoo-cache", args="resolve project name '<q>'")` — the cache runs the full Lookup Escalation Ladder. See the same delegation in [`alice-odoo-tasks.md`](alice-odoo-tasks.md) under **Resolve Project Name** for the rationale; do NOT read the cache skill file with the Read tool.

**Within a single conversation:** once a project is resolved, reuse `(id, name)` — do not re-invoke the binding check or the cache.

---

## Resolve Task Name

Same algorithm as Resolve Project Name, but scoped to `project.task` with the project_id filter:

```
odoo_search(model="project.task",
  domain=[["project_id", "=", <project_id>], ["name", "ilike", "<token>"]],
  fields=["id", "name", "stage_id"], limit=10)
```

Cache the chosen `(id, name)` for the session.

---

## Log Hours (single entry)

1. Validate **description is non-empty**. If empty, ask: "What did you work on? (description required)"
2. Parse hours — accept `"2h"`, `"2"`, `"1.5"`, `"90m"` (convert minutes → hours float).
3. Default date to **today** (local timezone) if not given.
4. Resolve `project_id` (and `task_id` if given) using the algorithms above.
5. If only a project is given, ask once: "Which task on [project]? (or 'no task' to log against the project)"
6. Resolve `employee_id` (cached).
7. Create the entry:
   ```
   odoo_create(model="account.analytic.line", values={
     "name": "<description>",
     "date": "YYYY-MM-DD",
     "unit_amount": <hours float>,
     "project_id": <project_id>,
     "task_id": <task_id>,        # omit key entirely if no task
     "employee_id": <employee_id>
   })
   ```
8. Confirm:
   - With task: `"Logged 2.0h on '[task name]' ([project name]) for 2026-05-19 — '[description]'."`
   - Project only: `"Logged 2.0h on '[project name]' (no task — will show as Unassigned in reports) for 2026-05-19 — '[description]'."`

---

## Batch Log

Input form: *"Log 2h on Task A and 1.5h on Task B today"* or a list.

1. Parse into a list of entries. For each entry validate: hours, description, project/task.
2. If ANY entry is missing required fields, gather all gaps into **one** clarifying message before any writes.
3. Resolve project_id / task_id once per unique name (reuse session cache).
4. Loop: call `odoo_create` per entry.
5. Summarize: `"Logged 3 entries totalling 5.0h for 2026-05-19: 2.0h on Task A, 1.5h on Task B, 1.5h on Task C."`

If a single create fails, report which entry failed and stop — do not silently skip.

---

## View Entries

Filter by `user_id` and date range. Default range: today.

```
odoo_search(model="account.analytic.line",
  domain=[
    ["user_id", "=", <user_id>],
    ["date", ">=", "YYYY-MM-DD"],
    ["date", "<=", "YYYY-MM-DD"]
  ],
  fields=["id", "date", "name", "unit_amount", "project_id", "task_id"],
  limit=50)
```

Date-range shortcuts:
- "today" → today only
- "yesterday" → yesterday only
- "this week" → Monday of current week → today
- "last week" → Monday–Sunday of previous week
- "this month" → 1st of current month → today

Output: a table with date, hours, project, task, description. End with the **total hours** for the range.

---

## Edit Entry

1. Find the entry. Preferred: the user gives an ID. Otherwise filter by date + project + (optionally) hours and disambiguate:
   ```
   odoo_search(model="account.analytic.line",
     domain=[["user_id", "=", <user_id>], ["date", "=", "YYYY-MM-DD"], ["project_id", "=", <project_id>]],
     fields=["id", "date", "name", "unit_amount", "task_id"])
   ```
   If multiple results, list them numbered and ask which one.
2. Apply the update:
   ```
   odoo_write(model="account.analytic.line", ids=[<id>], values={
     "unit_amount": <new hours>,    # any subset of fields
     "name": "<new description>",
     "date": "YYYY-MM-DD",
     "task_id": <new_task_id>
   })
   ```
3. Confirm with the updated entry's full state.

---

## Delete Entry

1. Find the entry (same as Edit, step 1).
2. **Always confirm before deleting:**
   `"Delete this entry? — 2.0h on '[task]' from [date], description: '[description]'."`
3. After explicit confirmation:
   ```
   odoo_execute(model="account.analytic.line", method="unlink", ids=[<id>])
   ```
4. Confirm: `"Deleted timesheet entry (ID [id])."`

---

## Field Reference

| Field | Type | Notes |
|---|---|---|
| `name` | char | Description of work — **required, never empty** |
| `date` | date | Format `YYYY-MM-DD`. Default: today (local timezone) |
| `unit_amount` | float | Hours (e.g. `1.5` = 1h 30m). Convert minutes if needed |
| `project_id` | many2one → `project.project` | Required for timesheet entries |
| `task_id` | many2one → `project.task` | Strongly preferred. Omit key (not `false`) if no task |
| `employee_id` | many2one → `hr.employee` | Pass explicitly. Resolved via `work_email` then name |
| `user_id` | many2one → `res.users` | Usually auto-set from employee. Use it as filter when viewing |

---

## Notes on Future Report Skill

This skill produces the raw data; a future report skill will aggregate it. To keep that easy:
- Always write a non-empty `name`
- Prefer task-level over project-only entries
- Use a consistent local timezone (the user's `{USER_TIMEZONE}`) when defaulting dates

No tag taxonomy or structured-description template is enforced here — those choices belong to the report skill so it can match how the user actually wants to slice the data.
