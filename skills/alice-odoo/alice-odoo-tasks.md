---
name: alice-odoo-tasks
description: Create, read, update, and change the stage of Odoo project tasks via Alice. Asks clarifying questions before acting when info is missing.
scope: odoo
triggers:
  - "create a task"
  - "add a task"
  - "new task in"
  - "odoo task"
  - "task in the project"
  - "update the task"
  - "change task status"
  - "move task to"
  - "mark task as"
  - "task deadline"
  - "assign the task"
  - "what tasks"
  - "show tasks"
  - "find the task"
mcp_required: odoo
mcp_scope: global
---

# Skill: Odoo Tasks

## Execution Strategy

Use `odoo_search`, `odoo_create`, `odoo_write`, `odoo_get` directly. The Odoo MCP is configured globally and available in every session.

**MCP parameter rules** — the tool schema is source of truth; do NOT use Odoo XML-RPC conventions in MCP calls:
- `odoo_get` takes `ids=[<int>, ...]` (array), never `id=<int>` (singular)
- `odoo_execute` takes `ids=[...]` and optional `kwargs={}` — there is no `args` parameter; method positional args do not pass through
- `odoo_fields` takes only `model` — no `fields=` filter
- All `domain`, `fields`, `ids` values must be native JSON arrays, never stringified

### How to delegate to alice-odoo-cache

Whenever this skill says "delegate to the alice-odoo-cache skill" (projects, stages, users, employees, field schemas), **invoke it via the Skill tool** — do NOT read the cache skill file with the Read tool.

```
Skill(skill="alice-odoo-cache", args="resolve project name '<q>'")
Skill(skill="alice-odoo-cache", args="look up stage '<q>' in project <project_id>")
Skill(skill="alice-odoo-cache", args="find user matching '<name-or-email>'")
```

Reading the cache file inline bypasses the skill's runtime, skips cache file I/O, and leaves the manifest unwritten — the next session will then re-query Odoo for data already on disk. Always go through the Skill tool.

**MCP parameter types — always pass native JSON, never strings:**
- `fields`: array of strings → `["id", "name"]`, not `"[\"id\", \"name\"]"`
- `domain`: array of triplets → `[["name", "ilike", "foo"]]`, not a stringified version
- `ids`: array of integers → `[42]`, not `"[42]"`
- Passing a serialized string where an array is expected causes: `'[...]' is not of type 'array'`

---

## When to Use

Use this skill when the user wants to **act on a task** in Odoo: create, find, update fields, or move to a different stage.

For logging notes, meeting summaries, or structured content to a task → use `skills/alice-odoo/alice-odoo-task-notes.md` instead.

---

## Clarifying Questions Protocol

Ask **all** missing required fields in **one message** — never one at a time.

| Action | Required | Optional | Ask if required missing |
|---|---|---|---|
| Create task | Task title, project name | Assignee, deadline | "What should I name the task, and which project does it belong to?" |
| Create task | — | Assignee | "Who should I assign it to? (skip if unassigned is fine)" |
| Create task | — | Deadline | "Any deadline for this task?" |
| Change stage | Target stage, project name | — | "Which stage should I move it to? I'll check what stages are available in that project." |
| Update description | Task identity | — | "Which task — by name, or tell me which project it's in?" |
| Find tasks | Project name | — | "Which project should I search in?" |

**Rule:** Batch all missing-field questions into a single message. Never ask field by field.

> **Project name is auto-resolved from `.alice/project.md` if present.** See **Auto-resolve Project from Binding** below — when a repo binding exists, don't ask "which project?"; use the binding silently.

---

## Self-Assignment

If the user says "assign to me", "assign it to myself", or similar, resolve the user's Odoo account via the cache:

- Invoke `Skill(skill="alice-odoo-cache", args="find user matching '{USER_NAME}'")` (fall back to `{USER_EMAIL}` if the name lookup fails)
- If the cache returns no match after the full escalation ladder, ask: "What's your Odoo username?"

> **Never call `odoo_search` for `res.users` directly, and never Read the cache skill file** — always invoke alice-odoo-cache via the Skill tool so the lookup result is persisted to `users.json` for next session.

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

**User input always wins.** If the user explicitly names a project in their request (e.g. *"create task 'foo' in [Project] TRS"*), use the explicit name and ignore the binding — run the normal cache delegation below.

If `.alice/project.md` doesn't exist, fall through to **Resolve Project Name** below.

> If a user repeatedly works in this repo without a binding, suggest once: *"Want me to bind this directory to <project> so I stop asking? Say 'bind this repo to <project>'."*

---

## Resolve Project Name

**This is the single entry point for project resolution.** Every action below (Create / Find / Change Stage / Update) MUST go through these steps in order — do NOT skip straight to the cache.

**Step A — Binding check (always first).** Run the **Auto-resolve Project from Binding** section above. If `.alice/project.md` exists AND the user did not explicitly name a different project in their request, use the binding's `(ID, NAME)` and **stop** — do not invoke the cache for this lookup. Append `(via repo binding)` to the confirmation.

**Step B — Cache delegation (only if Step A did not resolve).** Invoke the alice-odoo-cache skill via the Skill tool: `Skill(skill="alice-odoo-cache", args="resolve project name '<q>'")`. The cache skill runs the **Lookup Escalation Ladder** (cache → fuzzy match → silent force-refresh on miss → live `odoo_search` → ask user) and handles fuzzy matching (typos, word swaps, abbreviations) and disambiguation locally.

> Do NOT read `alice-odoo-cache.md` with the Read tool to perform the lookup yourself — that bypasses the cache files and the manifest never gets updated.

**Within a single conversation:** once a project is resolved, reuse `(id, name)` — do not re-invoke the binding check or the cache. The cache layer covers cross-session persistence; the in-conversation reuse rule covers redundant calls within a turn.

**After resolution — always show the full Odoo project name in confirmations** so the user can verify the match. If the cache had to force-refresh to find the project, surface that as `(via force-refresh)` in the confirmation.

---

## Create a Task

1. Validate required fields (task title + project name). Ask if missing.
2. Resolve project using the **Resolve Project Name** algorithm above to get `project_id`.
3. If assignee given, resolve user ID by invoking `Skill(skill="alice-odoo-cache", args="find user matching '<name-or-email>'")` (fuzzy match on name, exact match on email).
4. Create the task:
   ```
   odoo_create(model="project.task", values={
     "name": "<task title>",
     "project_id": <project_id>,
     "user_ids": [<user_id>],          # optional
     "date_deadline": "YYYY-MM-DD",    # optional
     "priority": "0"                   # "0" = normal, "1" = high
   })
   ```
5. Confirm: "Task '[name]' created in [project] (ID: [id])."

---

## Find a Task

First resolve `project_id` using the **Resolve Project Name** algorithm. Then filter by integer ID — this is faster and more accurate than matching on the relational name field.

Single task by name:
```
odoo_search(model="project.task",
  domain=[["name", "ilike", "<name>"], ["project_id", "=", <project_id>]],
  fields=["id", "name", "stage_id", "date_deadline", "user_ids"])
```

List tasks in a project:
```
odoo_search(model="project.task",
  domain=[["project_id", "=", <project_id>]],
  fields=["id", "name", "stage_id", "date_deadline"], limit=20)
```

Return: name, stage, deadline, assignee.

---

## Update Task Fields

Get task ID first (via Find a Task above if not known), then:
```
odoo_write(model="project.task", ids=[<task_id>], values={
  "date_deadline": "YYYY-MM-DD",    # update deadline
  "user_ids": [[6, 0, [<user_id>]]],  # replace assignee list
  "priority": "1"                   # "0" normal / "1" high
})
```

---

## Change Task Stage

Stages are **project-specific** in Odoo — always resolve via cache before writing.

1. Resolve `project_id` using the **Resolve Project Name** section (cache-delegated).
2. Resolve the target stage by invoking `Skill(skill="alice-odoo-cache", args="look up stage '<q>' in project <project_id>")`. The cache handles fuzzy matching like `"wip"` → `"In Progress"` and disambiguation locally.
3. Write the stage:
   ```
   odoo_write(model="project.task", ids=[<task_id>], values={"stage_id": <matched_stage_id>})
   ```
4. Confirm: "Task '[name]' moved to [Stage Name]."

---

## Field Reference

| Field | Type | Notes |
|---|---|---|
| `name` | char | Task title |
| `project_id` | many2one | Link to `project.project` |
| `stage_id` | many2one | Link to `project.task.type`. M2M to projects — a stage record may be shared across many projects or scoped to one (empty `project_ids` = global). |
| `user_ids` | many2many | Assignees — use `[[6, 0, [id1, id2]]]` syntax to replace |
| `date_deadline` | date | Format: `YYYY-MM-DD` |
| `description` | html | Full description — use `alice-odoo-task-notes.md` for structured content |
| `priority` | selection | `"0"` = Normal, `"1"` = High |
| `tag_ids` | many2many | Task tags |
| `state` | selection (required) | Odoo 19 replaced `kanban_state`. Values: `01_in_progress`, `02_changes_requested`, `03_approved`, `1_done`, `1_canceled`. Use `is_closed` (bool) to check if a state counts as closed without hardcoding values. |

---

## Common Stage Names (Odoo defaults — verify per project)

| User says | Likely stage name |
|---|---|
| "todo", "new", "backlog" | New / To Do |
| "in progress", "wip", "doing" | In Progress |
| "review", "testing" | In Review / Testing |
| "done", "finished", "complete" | Done |
| "cancelled", "dropped" | Cancelled |

Always resolve via the alice-odoo-cache skill — stage records are M2M to projects and the same record may belong to many projects (or none).
