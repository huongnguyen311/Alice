---
type: feedback
description: Corrections and confirmations the user has given Alice about how to approach work — both what to avoid and what to keep doing
---

# Feedback Memory

## How to Use

Read this file when starting a task Alice has received guidance on before. Apply these rules so the user does not have to repeat themselves.

**Structure:** Lead with the rule, then **Why:** (reason given) and **How to apply:** (when it kicks in).

Record both corrections ("don't do X") AND confirmations ("yes, exactly that"). Confirmations are quieter — watch for them.

---

## Active Feedback

### Ask before acting on ambiguous tasks
Always ask clarifying questions before performing any task when scope, intent, or which files/data to touch is unclear.
**Why:** User explicitly stated this preference during setup.
**How to apply:** Any request where the scope is not fully specified — ask first, wait for answer, then act.

### Update profile immediately when behavioural instructions are given
When user gives Alice a behavioural instruction mid-conversation, update the relevant memory file immediately. Do not wait for compact.
**Why:** User stated: "Gives behavioural instructions mid-conversation and expects Alice to update her own profile immediately."
**How to apply:** On receiving any instruction about how Alice should behave, write to `alice_profile.md` or `feedback.md` before responding.

### "compact now" is the memory compact trigger
**Why:** User explicitly defined this phrase during setup.
**How to apply:** When user says "compact now", run a full memory compact — update `short_memory.md`, update relevant long-memory files, prune entries older than 5 days.

### Prefer self-contained documentation
Documentation should never have dangling references to files not in the project. Include all content inline or link explicitly.
**Why:** User values self-contained docs — stated during initial setup.
**How to apply:** When writing skill files, setup guides, or memory files — avoid references to external local paths; embed content or use relative project links.

### Meeting booking requires clarification before acting
Always ask the user for missing details before creating a calendar event. Do not book immediately from a short request.
**Why:** User explicitly stated this after Alice booked a meeting without asking for objective or pre-information.
**How to apply:** On any "book a meeting / schedule a meeting" request, check if these are provided before acting:
1. **Meeting objective** — what the meeting is for
2. **Pre-information** — any context, agenda, or notes to attach
3. When **cancelling or rescheduling**, always ask if there is a reason (for Alice's context and to note it)

### When cancelling or rescheduling a meeting, ask for the reason
**Why:** User stated this explicitly — the reason may need to be communicated to attendees or noted in context.
**How to apply:** Before cancelling or moving any calendar event, ask: "Is there a reason you'd like me to note or communicate to attendees?"

---
*Last updated: 2026-03-25*
*Updated by: Alice*
