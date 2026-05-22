---
name: alice-odoo-task-notes
description: Format and save structured notes, meeting summaries, or decisions to an Odoo task description via Alice using a grep-friendly markdown template.
scope: odoo
triggers:
  - "save notes to task"
  - "add notes to the task"
  - "update task description"
  - "log this to the task"
  - "save meeting notes"
  - "write to the task"
  - "add content to task"
  - "task notes"
mcp_required: odoo
mcp_scope: global
---

# Skill: Odoo Task Notes

## When to Use This Skill

Use this skill (not `alice-odoo-tasks.md`) when the user wants to **log prose content** to a task:
- Meeting notes or call summaries
- Decisions made
- Blockers or issues discovered
- Progress updates or handovers
- Any content longer than a one-line status update

For field changes (stage, deadline, assignee) → use `skills/alice-odoo/alice-odoo-tasks.md` instead.

---

## The Grep-Friendly Template

The `description` field in Odoo is **HTML** — always write HTML, not raw markdown.

```html
<h2>[YYYY-MM-DD] [TYPE]: [One-line title]</h2>
<p><strong>Status:</strong> [active | resolved | pending | info]<br/>
<strong>Ref:</strong> [optional: related task ID, email subject, or external reference]</p>

<h3>Summary</h3>
<p>[2–4 sentences max. What happened or was decided.]</p>

<h3>Key Points</h3>
<ul>
  <li>[Point 1]</li>
  <li>[Point 2]</li>
</ul>

<h3>Action Items</h3>
<ul>
  <li>[ ] [Owner]: [What needs to happen] — due [date if known]</li>
</ul>

<h3>Keywords</h3>
<p>`keyword1` `keyword2` `project-name` `person-name`</p>
```

**Grep still works** — TYPE tags and backtick keywords are plain text inside the HTML, so `grep "DECISION"` and `` grep "`keyword`" `` match correctly on retrieved description text.

---

## TYPE Tags

Use in the heading — enables grep-based retrieval:

| TYPE | When to use |
|---|---|
| `MEETING` | Call, standup, or in-person meeting summary |
| `DECISION` | A conclusion or choice that was made |
| `BLOCKER` | Something preventing progress |
| `UPDATE` | Progress report or status change note |
| `HANDOVER` | Context passed to another person or team |
| `REVIEW` | Feedback, code review, or sign-off notes |

---

## Append vs. Overwrite Rule

| User says | Action |
|---|---|
| "add notes", "log this", "append" | **Append** — add new dated block above previous blocks (newest first) |
| "update description", "replace", "rewrite" | **Overwrite** — confirm first if existing content is > 2 lines |

**Never silently overwrite a non-empty description.** If the task already has content, show the user the existing content and confirm before replacing.

---

## MCP Parameter Types — Always Pass Native JSON

- `fields`: array of strings → `["id", "name"]`, not `"[\"id\", \"name\"]"`
- `ids`: array of integers → `[42]`, not `"[42]"`
- `domain`: array of triplets → `[["name", "ilike", "foo"]]`, not a stringified version
- Passing a serialized string where an array is expected causes: `'[...]' is not of type 'array'`

---

## Auto-resolve Project from Binding

Before searching for a task by name, check for a per-repo binding written by the **alice-project-bind** skill:

```bash
test -f .alice/project.md && cat .alice/project.md
```

If the file exists, parse the project from the two-fact schema:

```bash
ID=$(grep -E '^- Odoo Project ID:' .alice/project.md | sed -E 's/^- Odoo Project ID:[[:space:]]*//')
NAME=$(grep -E '^- Odoo Project Name:' .alice/project.md | sed -E 's/^- Odoo Project Name:[[:space:]]*//')
```

Use the binding's `ID` as a `project_id` filter when searching for the task — this narrows the task lookup from "all projects" to "this project" and avoids matching the same task name in unrelated projects. Append `(via repo binding)` to the resolution confirmation.

**User input always wins.** If the user explicitly names a project in their request, use that project instead and ignore the binding.

If `.alice/project.md` doesn't exist or the user already gave a task ID, skip this step.

---

## Execution Steps

1. Find the task — `odoo_search` by name (filtered by `project_id` from the binding above, if present), or use known task ID
2. Read current description:
   ```
   odoo_get(model="project.task", id=<task_id>, fields=["name", "description"])
   ```
3. Decide: append or overwrite (see rule above)
4. Format new content using the template
5. Build final description:
   - **Append:** new block + `\n\n---\n\n` + existing content
   - **Overwrite:** new block only
6. Write:
   ```
   odoo_write(model="project.task", ids=[<task_id>], values={"description": "<formatted html or markdown>"})
   ```
7. Confirm: "Saved [TYPE] note to '[task name]' on [YYYY-MM-DD]."

---

## Grep Patterns for Future Retrieval

When Alice retrieves a task description and needs to scan for relevance, use these patterns on the description text before parsing full prose. This avoids reading the entire content when only a subset is needed.

| Intent | Pattern to match |
|---|---|
| Find all decisions | `DECISION` in heading |
| Find open action items | `- [ ]` |
| Find blockers | `BLOCKER` in heading |
| Find entries from a specific date | `2026-04-07` in heading |
| Find by topic keyword | `` `keyword` `` in Keywords line |
| Find unresolved entries | `Status: active` |
| Find entries about a person | `` `person-name` `` in Keywords line |

**Token-saving rule:** When asked "what decisions were made about X?", scan the Keywords and heading lines only first. Only read the full body if the heading/keywords match. This collapses a 300-word note to a single grep-able line on first pass.
