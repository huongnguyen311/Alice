# Alice — Memory Index

This is Alice's **memory index**. It is always loaded at the start of every session alongside `short_memory.md`. Lines after 200 are truncated — keep this concise.

Scan this to find which memory file to read. Do NOT read all files — read only what is needed.

---

## Memory Files

| File | Type | Description | When to read |
|---|---|---|---|
| `short_memory.md` | context | Rolling 5-day context: recent conversations, active work, current state | **Always first** |
| `user_profile.md` | user | User identity, preferences, communication style, behavioral patterns | When personalising response or updating user info |
| `alice_profile.md` | core | Alice personality, running modes, capabilities, tone | When asked about Alice's behaviour or updating it |
| `feedback.md` | feedback | Corrections and confirmations the user has given Alice | Before taking an approach Alice has been guided on before |
| `project.md` | project | Ongoing decisions, active work, open questions, milestones | When context changes or a project status needs checking |
| `reference.md` | reference | Credentials, API endpoints, external systems, file locations | When writing scripts or connecting to external services |

---

## Memory Types

| Type | Trigger to write | File |
|---|---|---|
| **user** | User shares role, preferences, habits, or corrections about identity | `user_profile.md` |
| **feedback** | User corrects Alice's approach or confirms a non-obvious approach worked | `feedback.md` |
| **project** | Active work changes, new decision made, deadline set, task completed | `project.md` |
| **reference** | New external system, credential, API endpoint, or resource identified | `reference.md` |

---

## Auto-Writing Rule

Alice writes memories **immediately** when triggered — do NOT wait for compact:

- User shares a preference → `user_profile.md`
- User corrects Alice's behaviour → `feedback.md`
- User confirms an approach → `feedback.md`
- Active project/decision changes → `project.md`
- New external resource or credential → `reference.md`
- Context changes meaningfully → `short_memory.md`

After writing: confirm with one line — *"Saved to memory: [brief description]."*

---

## What NOT to Save

- Code patterns or file structure (derivable from codebase)
- Ephemeral task details or in-progress work (use TodoWrite)
- Git history (use `git log`)
- Anything already documented in CLAUDE.md

---
*Last updated: 2026-03-25*
*Updated by: Alice*
