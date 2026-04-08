---
name: save-memory
description: Save context, facts, preferences, decisions, or feedback to Alice's typed memory files. Use when the user shares something to remember, or when Alice detects a meaningful change.
scope: memory
triggers:
  - "remember"
  - "save this"
  - "note that"
  - "don't forget"
  - "update profile"
  - "update memory"
  - "forget"
  - "I prefer"
  - "from now on"
  - "next time"
---

# Skill: Save Memory

## When to Write (Auto-Write Rule)

Write memory **immediately** — do not wait for compact:

| Signal | Type | File |
|---|---|---|
| User shares role, preferences, habits | user | `memories/user_profile.md` |
| User corrects Alice's approach ("don't do that", "stop X") | feedback | `memories/feedback.md` |
| User confirms a non-obvious approach worked ("yes, exactly that") | feedback | `memories/feedback.md` |
| Active work, decisions, deadlines, or project status change | project | `memories/project.md` |
| New external system, API, credential, or resource identified | reference | `memories/reference.md` |
| Context shifts meaningfully between sessions | context | `memories/short_memory.md` |

---

## Memory Types & Files

| Type | File | What goes here |
|---|---|---|
| **user** | `memories/user_profile.md` | Name, role, preferences, communication style, habits |
| **feedback** | `memories/feedback.md` | Corrections AND confirmations — lead with rule, then **Why:** and **How to apply:** |
| **project** | `memories/project.md` | Ongoing work, key decisions, open questions, deadlines. Convert relative dates to absolute. |
| **reference** | `memories/reference.md` | Credentials, API endpoints, external systems, file paths |

> The index for all memory files is at `memories/MEMORY.md`.

---

## How to Save

### 1. Identify the type
Use the table above. If it could fit multiple types, choose the most specific.

### 2. Open the right file and update it
- **user_profile.md** — update the relevant field
- **feedback.md** — add a new `###` entry with rule + **Why:** + **How to apply:** lines
- **project.md** — add a row to the decisions table or update the relevant section
- **reference.md** — add a row to the appropriate table
- Always update the `*Last updated*` line

### 3. Confirm to the user
> "Saved to memory: [brief description of what was saved]."

---

## Feedback Memory Format

```markdown
### [Rule in imperative form]
[The rule itself — what Alice should or should not do]
**Why:** [Reason the user gave, or incident that prompted this]
**How to apply:** [When/where this rule kicks in — be specific enough to handle edge cases]
```

Both corrections AND confirmations are worth saving. Confirmations are quieter — watch for: "yes exactly", "perfect", "keep doing that", accepting an unusual choice without pushback.

---

## Example

**User:** "I prefer concise bullet-point reports, not long paragraphs."

1. Open `memories/user_profile.md`
2. Update `Report format:` to `concise bullet-point summaries`
3. Update `*Last updated*` line
4. Respond: *"Saved to memory: you prefer concise bullet-point reports."*

---

## When to Update `short_memory.md`

Update short memory when something meaningful changes that Alice needs to recall next session:
- A key decision was made
- Active work status changed
- A new cron/automation was registered
- Something from this conversation that won't be obvious from the files alone
