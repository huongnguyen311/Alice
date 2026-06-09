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

For logging notes, meeting summaries, or structured content to a task → use `skills/alice-odoo-task-notes.md` instead.

---

## Clarifying Questions Protocol

Ask **all** missing required fields in **one message** — never one at a time.

| Action | Required | Optional | Ask if required missing |
|---|---|---|---|
| Create task | Task title, project name | Assignee, deadline, description, star/priority | "What should I name the task, and which project does it belong to?" |
| Create task | — | Assignee | "Who should I assign it to? (skip if unassigned is fine)" |
| Create task | — | Deadline | "Any deadline for this task?" |
| Create task | — | Description | "Any description for this task?" |
| Create task | — | Star (priority) | "Should this task be starred/high priority? (yes/no, default: no)" |
| Change stage | Target stage, project name | — | "Which stage should I move it to? I'll check what stages are available in that project." |
| Update description | Task identity | — | "Which task — by name, or tell me which project it's in?" |
| Find tasks | Project name | — | "Which project should I search in?" |

**Rule:** Batch all missing-field questions into a single message. Never ask field by field.

**Create task — always ask for these optional fields** if not already provided by the user:
- Description: "Any description for this task? (or skip)"
- Star: "Should this task be starred (high priority)? (yes / no)"
- Assign for: "Who should this task be assigned to? (or skip to leave unassigned)"

Ask all three in a single follow-up message if none were mentioned.

---

## Self-Assignment

If the user says "assign to me", "assign it to myself", or similar, resolve the user's Odoo account using known identity — no need to ask:

1. Search by name first:
   ```
   odoo_search(model="res.users", domain=[["name", "ilike", "{USER_NAME}"]], fields=["id", "name"])
   ```
2. Fallback by email if no name match:
   ```
   odoo_search(model="res.users", domain=[["login", "=", "{USER_EMAIL}"]], fields=["id", "name"])
   ```
3. Use the first match. If neither returns a result, ask: "What's your Odoo username?"

---

## Resolve Project Name

Use this algorithm every time a project name is needed. Ask the user **at most once**.

**Session cache rule:** If a project was already resolved this conversation, reuse `(id, name)` — do not re-query.

**Step 1 — Normalize**
Lowercase, strip punctuation, split into tokens.
- `"inapps website"` → `["inapps", "website"]`
- `"HR"` → `["hr"]`

**Step 2 — AND search** (all tokens must appear in name)
```
odoo_search(model="project.project",
  domain=[["name", "ilike", "<token1>"], ["name", "ilike", "<token2>"], ...],
  fields=["id", "name"], limit=10)
```
- 1 result → **resolved**
- 2–5 results → go to Step 5
- >5 results → go to Step 6
- 0 results → go to Step 3

**Step 3 — OR search** (any token matches)

Build OR domain with Odoo prefix `"|"` operator — use N-1 `"|"` for N conditions:
```
# 2 tokens:
odoo_search(model="project.project",
  domain=["|", ["name", "ilike", "<token1>"], ["name", "ilike", "<token2>"]],
  fields=["id", "name"], limit=10)

# 3 tokens:
domain=["|", "|", ["name", "ilike", "<t1>"], ["name", "ilike", "<t2>"], ["name", "ilike", "<t3>"]]
```
- 1 result → **resolved**
- 2–5 results → go to Step 5
- >5 results → go to Step 6
- 0 results → go to Step 4

**Step 4 — Full list fallback**
```
odoo_search(model="project.project",
  domain=[["active", "=", true]],
  fields=["id", "name"], limit=50)
```
In your own reasoning (no extra Odoo call), keep entries where any token is a substring of the name (case-insensitive).
- 0 matches → show all project names, ask user to identify theirs
- 1 match → **resolved**
- 2–5 → go to Step 5
- >5 → go to Step 6

**Step 5 — Disambiguation** (ask once, numbered list)
```
I found a few projects matching "[input]":
1. inapps.net Website Redesign 2025
2. inapps Internal Portal

Which one? Reply with the number or the exact name.
```
Cache the chosen `(id, name)` for the rest of the session.

**Step 6 — Too many results**
```
I found [N] projects matching "[input]". Could you add a few more words from the project name?
```
Re-run from Step 1 with the refined input.

**After resolution — always show the full Odoo project name in confirmations** so the user can verify the match.

---

## Create a Task

1. Validate required fields (task title + project name). Ask if missing.
2. If description, star (priority), or assignee were **not** provided, ask for all three in one message:
   > "A few quick questions before I create the task:
   > - Any description? (or skip)
   > - Should it be starred / high priority? (yes / no)
   > - Who should it be assigned to? (or skip to leave unassigned)"
3. Resolve project using the **Resolve Project Name** algorithm above to get `project_id`.
4. If assignee given, resolve user ID:
   ```
   odoo_search(model="res.users", domain=[["name", "ilike", "<assignee name>"]], fields=["id", "name"])
   ```
5. Create the task:
   ```
   odoo_create(model="project.task", values={
     "name": "<task title>",
     "project_id": <project_id>,
     "description": "<description>",   # optional — plain text or HTML
     "user_ids": [[6, 0, [<user_id>]]],  # optional — use ORM many2many syntax
     "date_deadline": "YYYY-MM-DD",    # optional
     "priority": "1"                   # "0" = normal, "1" = high/starred
   })
   ```
6. Confirm: "Task '[name]' created in [project] (ID: [id])."
   Include a summary line for each field that was set (description snippet, assignee name, star status).

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

Stages are **project-specific** in Odoo — always discover before writing.

1. Resolve `project_id` using the **Resolve Project Name** algorithm.
2. Discover available stages for the project:
   ```
   odoo_search(model="project.task.type", domain=[("project_ids", "in", [<project_id>])], fields=["id", "name"])
   ```
3. Present list if user intent is ambiguous: "Available stages: New, In Progress, Done, Cancelled"
4. Fuzzy-match user's word to stage name (case-insensitive, partial match):
   - "done" → "Done", "in progress" / "inprogress" / "wip" → "In Progress", "todo" / "new" → "New"
5. If still ambiguous, ask once: "Did you mean [Stage A] or [Stage B]?"
6. Write the stage:
   ```
   odoo_write(model="project.task", ids=[<task_id>], values={"stage_id": <matched_stage_id>})
   ```
7. Confirm: "Task '[name]' moved to [Stage Name]."

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
