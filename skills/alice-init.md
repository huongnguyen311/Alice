---
name: alice-init
description: Interactive first-time setup for Alice — collects identity and preferences, writes config files, copies memory templates
scope: meta
triggers:
  - "setup alice"
  - "initialize alice"
  - "alice setup"
  - "configure alice"
  - "first time setup"
  - "init alice"
  - "run setup"
---

# Skill: Alice Init

## When to Use

Load this skill when the user says anything matching the triggers above — "setup alice", "alice setup", "initialize alice", "first time setup", "init alice", "configure alice", or "run setup".

Also proactively suggest this skill if `config/skill-personal.json` is missing or has placeholder values for `_user.name` / `_user.email`.

---

## Pre-flight Check

Before asking anything, check the current state:

1. Does `config/skill-personal.json` exist?
2. If yes — does it have a `_user` section with non-placeholder `name` and `email` (i.e. not `"Your Full Name"` or `"you@example.com"`)?
3. Which personal memory files are missing: `memories/user_profile.md`, `memories/reference.md`, `memories/short_memory.md`, `memories/project.md`?

**If everything looks configured:**
Tell the user: "Alice is already configured with [name]. Do you want to re-run setup to update your identity or preferences?"
Wait for their answer before proceeding.

**If config is missing or placeholder:**
Skip asking and go straight to Step 1.

---

## Step 1 — Collect Identity

Ask all identity questions in a single message. Keep it conversational — don't make it feel like a form.

Collect:
- **Full name** — how the user wants to be known
- **Work email** — primary email (used for meeting bookings, Gmail recap, etc.)
- **Job role / title** — e.g. "Mobile Dev", "Product Manager"
- **Organization / company** — e.g. "InApps Technology"
- **City and country** — e.g. "Ho Chi Minh City, Vietnam"
- **Timezone** — IANA format (e.g. `Asia/Ho_Chi_Minh`). Suggest one based on location if obvious.
- **Primary language** — language code, e.g. `vi` for Vietnamese, `en` for English

---

## Step 2 — Collect Skill-Specific Config (Optional)

Ask about skills that have configurable personal data. Tell the user upfront: "You can skip any section — just say skip or press enter."

### `alice-book-meeting` config

Ask:
1. **Meeting contacts** — people you regularly invite to meetings (name + email + optional note like "organizer" or "manager"). Collect as many as the user provides.
2. **Default meeting duration** — in hours (e.g. `1` for 1 hour). Default: `1`.
3. **Add Google Meet link for external attendees?** — yes/no. Default: `true`.

---

## Step 3 — Assemble JSON and Call `init.py`

Build the data object from what the user provided:

```json
{
  "_user": {
    "name": "<name>",
    "email": "<email>",
    "timezone": "<timezone>",
    "language": "<language>",
    "role": "<role>",
    "organization": "<organization>",
    "location": "<location>"
  },
  "alice-book-meeting": {
    "timezone": "<timezone>",
    "default_duration_hours": <duration>,
    "add_google_meet_for_external": <true|false>,
    "contacts": [
      { "name": "<name>", "email": "<email>", "note": "<note>" }
    ]
  }
}
```

Omit `alice-book-meeting` entirely if the user skipped that section.

Run:
```
python {ALICE_ROOT}/auto-scripts/init.py --data '<json>'
```

Show the output to the user.

---

## Step 4 — Run Install

After `init.py` succeeds, run install to bake the new identity into globally installed skill copies:

```
python {ALICE_ROOT}/auto-scripts/install.py
```

Show the output. Note which skills were installed as copies (tokens baked in) vs symlinks.

---

## Step 5 — Confirm

Summarize what was set up in a short message:

- Identity: name and email that were saved
- Skills updated: which installed skill copies now have identity baked in
- Memory files: which were newly created
- Reminder: "Run `python auto-scripts/install.py` again any time you change `config/skill-personal.json`."

---

## Notes

- `init.py` does a **non-destructive merge** — it won't overwrite existing config keys that aren't in the incoming data. Safe to re-run.
- If the user only wants to update one thing (e.g. add a contact), they can skip all other steps.
- After setup, Alice should update `memories/user_profile.md` with any additional preferences the user mentions during the conversation (using the `save-memory` skill).
