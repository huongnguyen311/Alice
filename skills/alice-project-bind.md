---
name: alice-project-bind
description: Bind the current working directory to an Odoo project in Alice — writes .alice/project.md so other Alice skills can skip 'which project?' prompts.
scope: odoo
triggers:
  - "bind this repo to"
  - "bind this directory to"
  - "set odoo project for this repo"
  - "set odoo project for this directory"
  - "what odoo project is this repo bound to"
  - "unbind this repo"
mcp_required: odoo
mcp_scope: global
---

# Skill: Project Bind

Bind the current working directory to an Odoo project. Once bound, other Alice skills (`alice-odoo-tasks`, `alice-odoo-timesheet`, `alice-odoo-task-notes`) skip "which project?" by reading `.alice/project.md` from the cwd.

The binding is per-repo (lives in the repo's `.alice/` directory) and gitignored — every developer binds their own working copy.

---

## When to Use

| User says | Action |
|---|---|
| "bind this repo to <project>" / "set odoo project for this directory" | **Bind** — resolve `<project>` and write `.alice/project.md` |
| "what odoo project is this repo bound to" | **Show** — read and report current binding |
| "unbind this repo" | **Unbind** — delete `.alice/project.md` |

If the user just says "bind this repo" with no project name, ask: *"Which Odoo project should I bind this directory to?"*

---

## Bind Action

### Step 1 — Resolve the Odoo project

**Delegate to the alice-odoo-cache skill** (`projects` table). Pass the user's project name as the query. The cache runs the full Lookup Escalation Ladder (cache → fuzzy match → silent force-refresh → live search → ask user). Result: a `(id, name)` pair, or the cache asks the user to disambiguate / declares not-found.

If the cache returns not-found, stop — do not write a binding file. Tell the user the project couldn't be resolved.

### Step 2 — Ensure `.alice/` is gitignored (before writing the file)

Always do gitignore first. If the next step fails, we still haven't leaked anything.

```bash
# Are we even in a git repo? (Skip gitignore step if not.)
git rev-parse --is-inside-work-tree 2>/dev/null
```

If inside a git repo:

```bash
# Check if .alice/ is already ignored — match `.alice` or `.alice/`, anchored to start of line.
grep -qE '^\.alice/?$' .gitignore 2>/dev/null && echo "already_ignored" || echo "not_ignored"
```

If `not_ignored`:

```bash
# Append the bare name on its own line.
printf '\n.alice/\n' >> .gitignore
```

Then **re-verify** — read the file back and confirm the last lines contain `.alice/` as a bare entry (no leading path like `/abs/path/.alice/` or `subdir/.alice/`). If a full path slipped in (e.g. shell expansion in an unusual environment), remove that line and re-run the `printf` command.

If not inside a git repo, skip the gitignore step and continue.

### Step 3 — Write `.alice/project.md`

```bash
mkdir -p .alice
```

Write `./.alice/project.md` with this exact two-fact schema:

```markdown
# Project Binding

- Odoo Project ID: <resolved_id>
- Odoo Project Name: <resolved_name>
```

Use the Write tool. If the file already exists, overwrite it (binding is idempotent — re-binding is how you change projects).

### Step 4 — Confirm

> "Bound this directory to Odoo project **<resolved_name>** (ID: <resolved_id>).
> Other Alice skills (tasks, timesheet, task-notes) will now use this project by default.
> To change: re-run `bind this repo to <other project>`. To remove: say `unbind this repo`."

---

## Show Action

```bash
test -f .alice/project.md && echo "exists" || echo "missing"
```

If missing:
> "This directory isn't bound to an Odoo project yet. To bind: `bind this repo to <project name>`."

If exists, read `.alice/project.md` and grep the two lines:

```bash
grep -E '^- Odoo Project (ID|Name):' .alice/project.md
```

Report:
> "This directory is bound to Odoo project **<name>** (ID: <id>)."

---

## Unbind Action

```bash
test -f .alice/project.md && rm .alice/project.md && echo "removed" || echo "not_bound"
```

Confirm:
> "Removed the Odoo project binding for this directory. Skills will go back to asking 'which project?'."

Leave `.alice/` and the `.gitignore` line untouched — they may be needed again, and the gitignore line is harmless when the directory is empty.

---

## Schema Reference

The `.alice/project.md` file uses a fixed two-fact schema so consumer skills can parse it with a single `grep`:

```markdown
# Project Binding

- Odoo Project ID: <integer>
- Odoo Project Name: <exact Odoo project name, including any [tags]>
```

**Parsing recipe for consumers** (use exactly this — no variants):

```bash
ID=$(grep -E '^- Odoo Project ID:' .alice/project.md | sed -E 's/^- Odoo Project ID:[[:space:]]*//')
NAME=$(grep -E '^- Odoo Project Name:' .alice/project.md | sed -E 's/^- Odoo Project Name:[[:space:]]*//')
```

Do not add other fields to this file. If you need to record something else about the project, use a sibling file (e.g. `.alice/team.md`) — keep `project.md` minimal.

---

## Notes

- **Per-repo, not per-Alice-install.** This skill operates on `pwd`, never on `{ALICE_ROOT}`. Each repo you work in gets its own binding.
- **User input always wins.** Consumer skills must treat the binding as a default only. If the user explicitly names a project in their request, the binding is ignored for that request.
- **No cache invalidation.** If a project is renamed in Odoo, the cached name in `.alice/project.md` becomes stale but the ID still works. Re-bind to refresh.
- **Outside a git repo.** The skill still writes `.alice/project.md` but skips the gitignore step. No git, no gitignore.
