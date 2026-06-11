---
name: alice-uninstall
description: Uninstall Alice skills from ~/.claude/skills/, removing all symlinks/copies and the install manifest
scope: meta
triggers:
  - "uninstall alice"
  - "uninstall alice skills"
  - "remove alice skills"
  - "remove alice globally"
---

# Skill: Uninstall Alice Skills

## When to Use

When the user wants to remove Alice's globally installed skills from `~/.claude/skills/`.

---

## What This Does

Reads `data/install-manifest.json` and removes exactly what Alice installed — symlinks (or copies on Windows) and their empty parent directories. Does not touch any file not recorded in the manifest.

---

## Execution

Run the uninstall script from Alice's root directory:

```
# Mac/Linux
python auto-scripts/uninstall.py

# Windows (if 'python' not in PATH)
py auto-scripts/uninstall.py
```

Show the user the full script output. The script:
1. Reads `data/install-manifest.json` — stops cleanly if no manifest found
2. For each skill: removes the symlink (or copied file on Windows)
3. Removes the skill's subdirectory if it is now empty
4. Removes Alice's MCP servers from `~/.claude.json` — only if the name **and config** exactly match `.mcp.json` (unrelated global MCPs are never touched)
5. Deletes the manifest file

Alice's source skill files in `skills/` are never touched.

---

## Notes

- If a skill was manually edited after install (making `SKILL.md` a real file instead of a symlink), the script will skip it and warn — remove manually in that case
- After uninstall, the skills are no longer available in other projects
- To reinstall: say "install alice skills"
