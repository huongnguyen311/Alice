---
name: alice-odoo-cache
description: Local cache layer for Odoo MCP data in Alice — projects, stages, users, employees, field schemas. Lazy TTL refresh with fuzzy matching, self-warming on miss, force-refresh on request. Use this skill in Alice whenever an Odoo project/stage/user/employee lookup is needed.
scope: odoo
triggers:
  - "resolve project name"
  - "look up odoo stage"
  - "find odoo user"
  - "find odoo employee"
  - "odoo field schema"
  - "refresh odoo cache"
  - "reload odoo cache"
  - "refresh odoo projects"
  - "refresh odoo stages"
  - "refresh odoo users"
  - "refresh odoo employees"
  - "refresh odoo fields"
  - "odoo cache is stale"
mcp_required: odoo
mcp_scope: global
---

# Skill: Odoo Cache

Local file-backed cache that eliminates repeat Odoo MCP queries for low-volatility data (projects, stages, users, employees, field schemas). Other Odoo skills delegate lookups here instead of re-querying every session.

---

## Execution Strategy

Read and write JSON files under `{ALICE_ROOT}/data/odoo_cache/`. Query Odoo MCP only on cache miss, TTL expiry, or explicit force-refresh.

**MCP parameter types — always pass native JSON, never strings:**
- `fields`: array of strings → `["id", "name"]`, not `"[\"id\", \"name\"]"`
- `domain`: array of triplets → `[["name", "ilike", "foo"]]`, not a stringified version
- `ids`: array of integers → `[42]`, not `"[42]"`

---

## Cache Location & Files

All cache files live in `{ALICE_ROOT}/data/odoo_cache/` (per-device, gitignored via `data/`).

| File | Contents |
|---|---|
| `projects.json` | `{"projects": [{"id", "name", "active"}, ...]}` — all active projects |
| `stages.json` | `{"stages": [{"id", "name", "sequence", "project_ids"}, ...]}` — flat global list. Each record carries its own `project_ids` (empty = available to all projects). Stages are M2M to projects in Odoo, so the same record can belong to many projects — do not key by project_id. |
| `users.json` | `{"users": [{"id", "name", "login", "partner_id"}, ...]}` |
| `employees.json` | `{"employees": [{"id", "name", "work_email", "user_id"}, ...]}` |
| `fields_schemas.json` | `{"<model>": {"<field>": {"type", "required", ...}}}` |
| `cache_manifest.json` | freshness metadata per table |

If `{ALICE_ROOT}/data/odoo_cache/` does not exist, create it before first write.

---

## TTL Defaults

| Table | TTL (seconds) | Rationale |
|---|---|---|
| projects | 604800 (7 days) | New projects added occasionally |
| stages | 2592000 (30 days) | Stages defined at project setup |
| users | 1209600 (14 days) | Onboarding cadence |
| employees | 1209600 (14 days) | Same as users |
| fields_schemas | 31536000 (365 days) | Changes only on Odoo instance customisation |

`cache_manifest.json` shape:
```json
{
  "projects":       {"last_updated": "2026-05-19T10:30:00Z", "ttl_seconds": 604800,  "source_count": 47},
  "stages":         {"last_updated": "2026-05-19T10:30:00Z", "ttl_seconds": 2592000, "source_count": 70},
  "users":          {"last_updated": "2026-05-19T10:30:00Z", "ttl_seconds": 1209600, "source_count": 23},
  "employees":      {"last_updated": "2026-05-19T10:30:00Z", "ttl_seconds": 1209600, "source_count": 23},
  "fields_schemas": {"last_updated": "2026-05-19T10:30:00Z", "ttl_seconds": 31536000, "models": ["account.analytic.line", "project.task", "project.project"]}
}
```

---

## Lookup Escalation Ladder

This is the **canonical resolution flow** for any cacheable lookup. Each step runs only if the previous one failed.

**Input:** user query `q`, target table `T`.

### Step 1 — Cache freshness check
- Read `cache_manifest.json`.
- **Self-heal first.** If `<T>.json` exists with records BUT the manifest is missing the entry for `T`, this is a leftover from a prior Step 2c failure. Re-derive the manifest entry from the file (`source_count = len(records)`, `last_updated = file mtime`, `ttl_seconds` from the TTL table) and atomic-write the manifest back. Then re-read the manifest and continue below — do NOT mark the cache as stale and do NOT re-query Odoo just to fix this.
- **Treat as fully stale (go to Step 2) if ANY of these hold AFTER self-heal:**
  - `cache_manifest.json` does not exist (and there's no JSON file to self-heal from)
  - `cache_manifest.json` has no entry for table `T` AND `<T>.json` does not exist (first-ever lookup)
  - The JSON file for `T` (`<T>.json`) does not exist on disk
  - `T.last_updated + T.ttl_seconds <= now` (TTL expired)
- Otherwise cache is fresh → Step 3.

> **Why this matters:** a missing manifest key is NOT the same as "no refresh needed". The first lookup of any table will have no manifest entry — Step 2 must fire to populate it. But if the JSON file ALREADY has data (Step 2b ran, Step 2c didn't), self-heal the manifest from the file instead of pointlessly re-fetching from Odoo.

### Step 2 — TTL refresh (passive)

Three sub-steps. **All three MUST run** — skipping (c) is the most common bug because it produces a JSON file without a manifest entry, which makes the next session declare the cache stale again and re-fetch forever. The user sees repeated Odoo queries for data that's already on disk.

a. Query Odoo MCP for the full table (see **Per-Table Recipes** below).
b. **Atomic write** the JSON file (`<T>.tmp` → rename over `<T>.json`).
c. **Update `cache_manifest.json` for table `T`** — set `last_updated` to now (ISO 8601 UTC), `ttl_seconds` per the TTL table, and any per-table metadata (`source_count`, `project_ids`, `models`). If the manifest file or the `T` key doesn't exist yet, create it. Atomic write the manifest the same way.
d. Continue to Step 3.

> **Recovery rule (silent self-heal).** If at Step 1 you find a JSON file that exists with records but the manifest is missing the entry for `T`, treat it as a Step 2c failure from a prior session — re-derive the manifest entry from the file contents (`source_count = len(records)`, `last_updated = file mtime`) and write it back atomically. Do NOT re-query Odoo just to fix this. Then proceed to Step 3.

### Step 3 — Local fuzzy match against cache
- Read the cached JSON, run the **Fuzzy Matcher** (below) on the records
- **MATCH** if top score ≥ 0.85 AND (top − second) ≥ 0.15 → return the record
- **AMBIGUOUS** if 2–3 candidates ≥ 0.4 with no clear winner → ask user to pick from top 3, return chosen
- **NO MATCH** if no candidate ≥ 0.4 → Step 4

### Step 4 — Force-refresh that table (last-resort refresh)
- Cache may be technically fresh but missing a record added since last refresh
- Silently force-refresh **only** table `T` (no diff report)
- Re-run Step 3 against fresh data
- If match found, prepend `(via force-refresh)` to the resolution message so the user knows the cache was stale
- Else → Step 5

### Step 5 — Live Odoo single-record search (final fallback)
- Run targeted `odoo_search` with the user's raw query, e.g. `domain=[["name", "ilike", q]]`
- If found: append the record to the cache JSON, then return it
  - If `<T>.json` doesn't exist yet, create it with a single-record list under the table's top-level key (e.g. `{"users": [<record>]}`)
  - Do **NOT** touch the manifest timestamp — append is not a full refresh
- Else → Step 6

### Step 6 — Declare not found
- Tell the user: `"Could not find <table singular> matching '<q>' in cache, after refresh, or via live search. Want to (1) try a different name, (2) create a new one, or (3) skip?"`
- Never guess an ID

**Worst-case cost:** 1 full-table refresh + 1 single-record search = 2 MCP calls. Best case (fresh cache + clean fuzzy match): 0 MCP calls.

---

## Fuzzy Matcher (Tiered)

Applies to: projects, users, employees, stages. **Not** field schemas (exact only).

Run all four tiers, take `max(score_t2, score_t3, score_t4)` per candidate; if all zero, candidate has no match.

**Tier 1 — Exact** (case-insensitive, trimmed)
- If exactly one record matches: return immediately with score 1.0

**Tier 2 — Substring**
- `q.lower() in name.lower()` OR `name.lower() in q.lower()`
- Score = `len(shorter) / len(longer)`

**Tier 3 — Token overlap (Jaccard)**
- Tokenise both: lowercase, strip punctuation, drop stopwords (`the`, `a`, `an`, `of`, `for`, `project`, `inapps`)
- Score = `|intersection| / |union|`
- Handles word-order swaps and abbreviations

**Tier 4 — Fuzzy ratio**
- `difflib.SequenceMatcher(None, q.lower(), name.lower()).ratio()` (stdlib, no extra deps)
- Catches typos

**Decision rule:**
- Top score ≥ 0.85 AND (top − second) ≥ 0.15 → auto-pick
- 2–3 candidates ≥ 0.4, gap < 0.15 → ask user with top 3:
  ```
  I found a few matches for "<q>":
  1. <name1>  (score 0.92, fuzzy)
  2. <name2>  (score 0.81, token)
  3. <name3>  (score 0.65, substring)

  Which one? Reply with the number or the exact name.
  ```
- Top score < 0.4 → treat as no match, escalate to Step 4

Always show the **resolved full name** in the confirmation message so the user can verify.

---

## Per-Table Recipes

### projects (`project.project`)

**Full refresh query:**
```
odoo_search(model="project.project",
  domain=[["active", "=", true]],
  fields=["id", "name", "active"],
  limit=500)
```
Write to `projects.json` as `{"projects": [...]}`. **Then update `cache_manifest.json.projects` (Step 2c)** — `last_updated = now`, `ttl_seconds = 604800`, `source_count = len(projects)`.

**Single-record fallback (Step 5):**
```
odoo_search(model="project.project",
  domain=[["name", "ilike", "<q>"]],
  fields=["id", "name", "active"],
  limit=5)
```
If 1 result: append; if multiple: present with fuzzy scores and ask user.

**Lookup uses fuzzy matcher.**

---

### stages (`project.task.type`) — flat global list

Stages in `project.task.type` are M2M to projects (`project_ids` field). The same stage record can belong to many projects, or to none (an unassigned/global stage). Caching per-project would duplicate every shared record and force redundant refreshes — so cache the whole table once and filter at lookup time.

**Full refresh query (entire table):**
```
odoo_search(model="project.task.type",
  fields=["id", "name", "sequence", "project_ids"],
  limit=500)
```
Write to `stages.json` as `{"stages": [...]}`. Update `cache_manifest.json.stages` — `last_updated = now`, `ttl_seconds = 2592000`, `source_count = len(stages)`.

**Lookup `Skill(skill="alice-odoo-cache", args="look up stage '<q>' in project <project_id>")`:**
1. Filter the flat list to candidates for `<project_id>`: records where `<project_id> in record.project_ids` OR `record.project_ids == []` (empty = available to any project).
2. Run the fuzzy matcher on that filtered subset, sorted by `sequence`.
3. If multiple candidates have the same name (e.g. "Done" exists as both a global record and a project-specific one), prefer the project-specific match (non-empty `project_ids` containing the target).

**Lookup without a project (`args="look up stage '<q>'"`):** fuzzy match against the entire flat list. If multiple records share the name, list them with their `project_ids` and ask the user which one.

---

### users (`res.users`)

**Full refresh query:**
```
odoo_search(model="res.users",
  domain=[["active", "=", true]],
  fields=["id", "name", "login", "partner_id"],
  limit=500)
```
Write to `users.json` as `{"users": [...]}`. **Then update `cache_manifest.json.users` (Step 2c)** — `last_updated = now`, `ttl_seconds = 1209600`, `source_count = len(users)`.

**Lookup uses fuzzy matcher** on `name` field (also accept exact match on `login` for emails).

---

### employees (`hr.employee`)

**Full refresh query:**
```
odoo_search(model="hr.employee",
  domain=[["active", "=", true]],
  fields=["id", "name", "work_email", "user_id"],
  limit=500)
```
Write to `employees.json` as `{"employees": [...]}`. **Then update `cache_manifest.json.employees` (Step 2c)** — `last_updated = now`, `ttl_seconds = 1209600`, `source_count = len(employees)`.

**Lookup:** if user gives an email, try exact match on `work_email` first; otherwise fuzzy on `name`.

---

### fields_schemas (`odoo_fields` output) — exact match only

Field-schema lookups do NOT use the generic escalation ladder (Steps 1–6) because schemas are keyed exactly by model name — no fuzzy matching, no "single-record search" fallback. Use this procedure instead.

**Invocation:** `Skill(skill="alice-odoo-cache", args="check fields for model '<model_name>'")`

**Cached shape** (one entry per cached model, verified against `odoo_fields(model="account.analytic.line")`):
```json
{
  "account.analytic.line": {
    "name":    {"required": true,  "string": "Description", "type": "char"},
    "date":    {"required": true,  "string": "Date",        "type": "date"},
    "task_id": {"required": false, "string": "Task",        "type": "many2one"},
    "...":     "..."
  }
}
```
Each model maps to the full `odoo_fields` response — a flat dict keyed by field name with `string`, `type`, `required`, and sometimes `help`. **Note:** `odoo_fields` does NOT return allowed values for `selection`-type fields; if a caller needs those, query a sample record or use `odoo_execute`.

**Step 1 — Cache freshness check (per-model)**
- Read `cache_manifest.json` and `fields_schemas.json`.
- **Self-heal:** if `fields_schemas.json` contains `<model_name>` but the manifest's `fields_schemas.models` list does not, re-derive the manifest entry (`last_updated = file mtime`, `ttl_seconds = 31536000`, add `<model_name>` to `models`) and atomic-write the manifest. Continue below.
- **Treat as stale (go to Step 2) if ANY of these hold:**
  - `fields_schemas.json` does not exist
  - `fields_schemas.json` has no key for `<model_name>`
  - `cache_manifest.json.fields_schemas.last_updated + ttl_seconds <= now`
- Otherwise → Step 3.

**Step 2 — Refresh from Odoo**
a. Query: `odoo_fields(model="<model_name>")`. The MCP tool takes only `model` — there is no `fields=` parameter; it always returns the full schema.
b. Load existing `fields_schemas.json` (or start with `{}`), set `schemas["<model_name>"] = <response>`, atomic-write.
c. Update `cache_manifest.json.fields_schemas` — set `last_updated = now` (ISO 8601 UTC), `ttl_seconds = 31536000`, ensure `<model_name>` is in `models`. Atomic-write the manifest.
d. Continue to Step 3.

**Step 3 — Return**
- Return `schemas["<model_name>"]` to the caller.
- If the caller asked about a specific field that's missing from the cached schema, that's a genuine "field doesn't exist on this model" — report it as such, do NOT re-query. `odoo_fields` returns the exhaustive schema; a missing field in fresh data means it isn't defined.

**No fuzzy match** — exact model-name key only.

**Recommended models to seed (lazy, on first lookup — do NOT pre-warm):**
- `account.analytic.line` (timesheet)
- `project.task`
- `project.project`

---

## Force-Refresh Mechanism

Bypass TTL when the user knows the cache is stale.

| Trigger phrase | Action |
|---|---|
| "refresh odoo cache" / "reload odoo cache" / "odoo cache is stale" | Refresh ALL tables |
| "refresh odoo projects" | projects only |
| "refresh odoo stages" | stages only (single full-table refresh) |
| "refresh odoo users" | users only |
| "refresh odoo employees" | employees only |
| "refresh odoo fields" | fields_schemas only (loop over `cache_manifest.json.fields_schemas.models`) |

**Per-table behaviour:**
1. Run the **Full refresh query** from **Per-Table Recipes**
2. Diff against current cache: new IDs, removed IDs, unchanged count
3. Atomic write the JSON file (write to `<name>.tmp`, then rename)
4. Update `cache_manifest.json.<table>.last_updated` to now
5. Report one line per table:
   ```
   ✅ projects: 47 → 49 (+2 new: "Q3 Launch Plan", "Mobile App v2"; 0 removed)
   ✅ employees: 23 → 23 (no change)
   ✅ users: 26 → 25 (0 new, -1 removed: "alex@old.example.com")
   ```

**Failure handling:**
- If Odoo MCP errors mid-refresh, leave the existing cache file untouched (atomic write means partial writes never land)
- Report the error and which table failed; do not roll back tables that already succeeded

---

## Write Rules

- **Atomic writes only.** Write to `<name>.tmp` then rename over `<name>` — prevents corruption if a read happens mid-write.
- **Create directory if missing.** If `{ALICE_ROOT}/data/odoo_cache/` does not exist, create it on first write.
- **Single-record append (Step 5) does NOT touch `cache_manifest.json` timestamps.** Only full refreshes update timestamps.
- **Always update `cache_manifest.json` immediately after a full refresh.** Source-of-truth for freshness.

---

## Delegating from Other Skills

Other Odoo skills MUST invoke this skill **via the Skill tool** — not by reading this file with the Read tool. Reading the file inline bypasses the cache runtime, skips the JSON file I/O, and leaves the manifest unwritten, so the next session re-queries Odoo for data already on disk.

**Correct (invoke via Skill tool):**

```
Skill(skill="alice-odoo-cache", args="resolve project name '<q>'")
Skill(skill="alice-odoo-cache", args="look up stage '<q>' in project <project_id>")
Skill(skill="alice-odoo-cache", args="find user matching '<name-or-email>'")
Skill(skill="alice-odoo-cache", args="find employee for '{USER_EMAIL}'")
Skill(skill="alice-odoo-cache", args="check fields for model 'account.analytic.line'")
```

**Incorrect (do NOT do this):**

- `Read(file_path=".../alice-odoo-cache.md")` followed by running the escalation ladder yourself — this is the bug that produces repeated Odoo queries and missing manifest entries.

The cache skill runs the escalation ladder and returns the resolved record (or asks the user / declares not-found).

---

## Limitations

- **Per-device cache** — files live inside this Alice install. If Alice is moved to a different directory, reinstall (`python auto-scripts/install.py`) to update the baked `{ALICE_ROOT}` path in the global skill copy.
- **No cron refresh** — purely lazy TTL + on-demand force-refresh. If the user adds a project in Odoo and the cache is still fresh, the first lookup of that project will trigger Step 4 (silent force-refresh).
- **No cache invalidation hooks** on Odoo writes — TTL + self-warming on miss is the trade-off.
- **Tasks, timesheet entries, comments are NOT cached** — they are volatile by design.

---

## Field Reference

| Cache file | Key | Fields stored |
|---|---|---|
| `projects.json` | `projects[]` | `id`, `name`, `active` |
| `stages.json` | `stages[]` | `id`, `name`, `sequence`, `project_ids` |
| `users.json` | `users[]` | `id`, `name`, `login`, `partner_id` |
| `employees.json` | `employees[]` | `id`, `name`, `work_email`, `user_id` |
| `fields_schemas.json` | `<model>` | full `odoo_fields` response |
| `cache_manifest.json` | `<table>` | `last_updated` (ISO 8601 UTC), `ttl_seconds`, plus per-table metadata (`source_count`, `models`) |
