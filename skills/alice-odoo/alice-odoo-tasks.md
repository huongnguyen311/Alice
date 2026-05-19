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

---

## Self-Assignment

If the user says "assign to me", "assign it to myself", or similar, resolve the user's Odoo account via the cache:

- Find user matching `{USER_NAME}` (or `{USER_EMAIL}` as a fallback) via `skills/alice-odoo/alice-odoo-cache.md` (`users` table)
- If the cache returns no match after the full escalation ladder, ask: "What's your Odoo username?"

---

## Resolve Project Name

**Delegate to `skills/alice-odoo/alice-odoo-cache.md`.** Ask the cache skill to resolve project `<q>` via the **Lookup Escalation Ladder** (cache → fuzzy match → silent force-refresh on miss → live `odoo_search` → ask user). The cache handles fuzzy matching (typos, word swaps, abbreviations) and disambiguation locally.

**Within a single conversation:** once a project is resolved, reuse `(id, name)` — do not re-invoke the cache. The cache layer covers cross-session persistence; the in-conversation reuse rule covers redundant calls within a turn.

**After resolution — always show the full Odoo project name in confirmations** so the user can verify the match. If the cache had to force-refresh to find the project, surface that as `(via force-refresh)` in the confirmation.

---

## Create a Task

1. Validate required fields (task title + project name). Ask if missing.
2. Resolve project using the **Resolve Project Name** algorithm above to get `project_id`.
3. If assignee given, resolve user ID via `skills/alice-odoo/alice-odoo-cache.md` (`users` table — fuzzy match on name, exact match on email).
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
2. Resolve the target stage via `skills/alice-odoo/alice-odoo-cache.md` (`stages` table, scoped to `<project_id>`). The cache handles fuzzy matching like `"wip"` → `"In Progress"` and disambiguation locally.
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
| `stage_id` | many2one | Link to `project.task.type` (project-specific) |
| `user_ids` | many2many | Assignees — use `[[6, 0, [id1, id2]]]` syntax to replace |
| `date_deadline` | date | Format: `YYYY-MM-DD` |
| `description` | html | Full description — use `alice-odoo-task-notes.md` for structured content |
| `priority` | selection | `"0"` = Normal, `"1"` = High |
| `tag_ids` | many2many | Task tags |
| `kanban_state` | selection | `normal`, `done`, `blocked` |

---

## Common Stage Names (Odoo defaults — verify per project)

| User says | Likely stage name |
|---|---|
| "todo", "new", "backlog" | New / To Do |
| "in progress", "wip", "doing" | In Progress |
| "review", "testing" | In Review / Testing |
| "done", "finished", "complete" | Done |
| "cancelled", "dropped" | Cancelled |

Always confirm via `project.task.type` search — stages vary by project.
