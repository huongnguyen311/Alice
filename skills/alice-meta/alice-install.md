---
name: alice-install
description: Install Alice skills as personal global skills at ~/.claude/skills/ so they are available in any Claude Code project on this machine
scope: meta
triggers:
  - "install alice"
  - "install alice skills"
  - "alice install"
  - "alice global skills"
  - "make alice skills global"
---

# Skill: Install Alice Skills Globally

## When to Use

When the user wants Alice's skills available in other projects (not just inside the Alice directory).

---

## What This Does

Installs skills from `config/install-config.json` as personal global Claude Code skills at `~/.claude/skills/`. Once installed, these skills are available in **every project** on this machine.

**Priority warning:** Personal skills have HIGHER priority than project-level skills. An installed skill will override any project-local skill with the same name in every project on this machine.

---

## Step 1 — Show current config before installing

Read and display `config/install-config.json` (or `config/install-config.json.example` if the personal config does not exist yet). Show the user exactly which skills are enabled and what type they are:

```
Read: config/install-config.json
```

Also check `config/skill-personal.json` exists — if missing, warn the user that personal tokens (contacts, timezone, etc.) will use example placeholder values.

Present the enabled skills as a table:

| Skill | Type | MCP required | Has personal tokens? |
|---|---|---|---|
| (from config) | mcp / python | ... | yes / no |

If `config/install-config.json` does not exist, tell the user:
> "No personal install config found — using defaults from `config/install-config.json.example`.
> To customise:
> - Mac/Linux: `cp config/install-config.json.example config/install-config.json`
> - Windows: `copy config\install-config.json.example config\install-config.json`"

If `config/skill-personal.json` does not exist, tell the user:
> "No personal data config found — contacts, timezone, etc. will use placeholder values from the example.
> To add your real data:
> - Mac/Linux: `cp config/skill-personal.json.example config/skill-personal.json`
> - Windows: `copy config\skill-personal.json.example config\skill-personal.json`"

Ask the user to confirm before proceeding.

---

## Step 2 — Run the install script

```
# Mac/Linux
python auto-scripts/install.py

# Windows (if 'python' not in PATH)
py auto-scripts/install.py
```

Show the user the full script output.

The script:
1. Reads `config/install-config.json` (falls back to `.example` if absent)
2. Reads `config/skill-personal.json` for personal token values (falls back to `.example` with a notice)
3. For each enabled skill:
   - **No tokens** → symlink to source; edits propagate automatically; falls back to copy on Windows
   - **Has `{ALICE_ROOT}` or personal tokens** → substitutes all tokens, writes as a copy
4. Writes `data/install-manifest.json`

**On success**, skills are immediately available in all projects. No restart needed.

---

## Config file reference

| File | Purpose | Committed? |
|---|---|---|
| `config/install-config.json.example` | Template — which skills are available and their defaults | Yes |
| `config/install-config.json` | Personal install config — enable/disable skills | No (gitignored) |
| `config/skill-personal.json.example` | Template — personal token placeholder values | Yes |
| `config/skill-personal.json` | Your real personal data (contacts, timezone, etc.) | No (gitignored) |

**To add or remove a skill:** edit `config/install-config.json`, set `"enabled": true/false`, re-run install.

**To update personal data** (contacts, timezone): edit `config/skill-personal.json`, re-run install.

**Skill type field:**
- `"type": "mcp"` — skill has no tokens; symlinked, edits propagate automatically.
- `"type": "python"` — skill uses `{ALICE_ROOT}` for script/data paths; always installed as a copy.
- Any skill using personal tokens (`{CONTACTS}`, `{TIMEZONE}`, etc.) is automatically installed as a copy.

---

## Adding a New Skill to Global Install

Follow this checklist when a new skill should be available in other projects:

### Step 1 — Determine the install pattern

| Skill characteristics | Pattern | Type in config |
|---|---|---|
| Pure MCP calls, no file paths, no personal data | Install directly | `"type": "mcp"` |
| References `{ALICE_ROOT}` paths or scripts | Install directly | `"type": "python"` |
| References other Alice skills / `memories/` / `data/` | Create a wrapper | `"type": "python"` (wrapper file) |
| Writes to `memories/`, Alice routing logic | Do NOT install | — |

### Step 2 — If a wrapper is needed

Create `skills/<skill-name>-global.md` with this structure:

```markdown
---
name: <skill-name>
description: <same as internal skill>
scope: <same scope>
triggers:
  - <same triggers as internal skill>
---

# Skill: <Name> (Global Wrapper)

This skill delegates to Alice's full implementation.

Read and follow: `{ALICE_ROOT}/skills/<skill-name>.md`

**Context for delegated skill:**
- Alice root is `{ALICE_ROOT}`
- <any other paths the internal skill needs, prefixed with {ALICE_ROOT}>
- Treat all relative paths in the delegated skill as relative to `{ALICE_ROOT}`
```

### Step 3 — If the skill needs personal tokens

1. Add the token placeholder to `config/skill-personal.json.example`:
   ```json
   "<skill-name>": {
     "my_token": "placeholder-value"
   }
   ```
   **Naming rule:** The key must exactly match the skill's `name` field in `install-config.json` (e.g. `alice-book-meeting`, not `book-meeting`). The install script looks up personal data by skill name — a mismatch will silently leave tokens unresolved.
2. Add real values to `config/skill-personal.json` (gitignored) using the same key
3. Add substitution logic to `_apply_tokens()` in `auto-scripts/install.py`:
   ```python
   my_val = skill_personal.get("my_token", "")
   content = content.replace("{MY_TOKEN}", my_val)
   ```
   Note: all `open()` calls in `install.py` / `uninstall.py` use `encoding="utf-8"` — maintain this for any new file I/O added.
4. Use `{MY_TOKEN}` in the skill file — never hardcode personal values

### Step 4 — Register in install config

Add to **both** `config/install-config.json.example` and `config/install-config.json`:

```json
{
  "name": "<skill-name>",
  "file": "<skill-file>.md",
  "type": "mcp | python",
  "mcp_required": "<mcp-name> or null",
  "warning": "<optional warning> or null",
  "enabled": true
}
```

### Step 5 — Re-run install

```
# Mac/Linux
python auto-scripts/install.py

# Windows (if 'python' not in PATH)
py auto-scripts/install.py
```

---

## Notes

- Skills without tokens are symlinked — edits to source propagate automatically, no reinstall needed
- Skills with tokens (`{ALICE_ROOT}` or personal) are copied — re-run `install alice` after editing source or personal config
- Wrapper skills read Alice's internal skill at runtime — the internal skill can be updated without reinstalling the wrapper
- The manifest (`data/install-manifest.json`) is required for clean uninstall — do not delete it manually
- To uninstall: say "uninstall alice skills"
- If Alice's project directory is moved, re-run install to update all baked-in absolute paths
