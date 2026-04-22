---
name: alice-scope-detail
description: Expand a brief primary scope into a structured specification document via Alice — covering short description, user flow, system behavior, error cases, constraints, and acceptance criteria without adding assumptions.
scope: meta
triggers:
  - "write scope detail"
  - "expand scope"
  - "scope detail"
  - "scope specification"
  - "write specification from scope"
  - "detail this scope"
  - "expand this feature scope"
---

# Skill: Scope Detail Writer

Transforms a brief primary scope into a structured specification document. Expands content to be clear, structured, and detailed — without assuming, inventing, or adding features not mentioned in the original scope.

## Rules

- Base strictly on the provided primary scope
- Do NOT assume, invent, or add features not in the scope
- Stay aligned with the original intent and boundaries
- Every section derives only from what is explicitly or clearly implicitly stated

## Input

Ask for (or accept inline):
- **Primary scope**: The feature description to expand

If not provided, ask: *"Please share the primary scope you'd like me to expand."*

## Output Structure

Produce a markdown document with the following sections in order:

---

### 1. Short Description

What the feature does. 1–3 sentences max. Restate the core purpose without embellishment.

---

### 2. User Flow

Step-by-step: what the user does → how the system responds. Format as a numbered list. Each step = one user action or system response.

Example format:
1. User navigates to [screen]
2. User enters [input]
3. System validates [condition]
4. System displays [result]

---

### 3. System Behavior

- **Validations**: Rules the system enforces (only those implied by scope)
- **System behavior**: How the system processes or responds internally — e.g. "saves to database", "calls API", "sends notification"
- **State changes**: What changes in the system as a result of the user action

---

### 4. Error Cases *(if any)*

Only include cases clearly implied by the primary scope. Omit this section entirely if no error cases apply.

For each case:
- **Condition**: When does this occur?
- **System response**: What happens?

---

### 5. Constraints

Respect any limitations explicitly stated in the scope. If none stated, omit this section.

---

### 6. Acceptance Criteria

Defines when the feature is considered done — clear, testable bullet points organized by category.

Format:
**Happy path:**
- ✅ User can...
- ✅ System...

**System behavior:**
- ✅ System processes/stores/sends...
- ✅ System prevents...

**Error handling:** *(only if Section 4 has error cases)*
- ✅ System displays [error message] when [condition]

Guidelines:
- One bullet = one clear, testable outcome
- Use simple statements: "User can…", "System…"
- Avoid implementation details
- Do not include assumptions outside the given scope
- Cover the happy path, system behavior, and all error cases listed in Section 4

---

## Execution Algorithm

1. Receive primary scope from user
2. Read the scope carefully — identify: domain, action type, actors, implied backend
3. Draft each section strictly from the scope — if a section has nothing to say, omit it
4. Write Acceptance Criteria last — every item must map back to a specific point in sections 1–5
6. Run the Quality Check below before saving
7. Save the document (see **Output File** section below)
8. After saving, confirm the file path to the user and ask: *"Would you like me to adjust any section or add constraints?"*

## Quality Check (self-run before saving)

- [ ] Every statement in Short Description is in the scope
- [ ] Every step in User Flow follows logically without gaps
- [ ] Every system behavior listed is implied by the scope
- [ ] Every error case is implied, not invented
- [ ] Every acceptance criterion is testable and maps to a section above
- [ ] Acceptance Criteria covers happy path, system behavior, and error cases
- [ ] No section contains assumed features

## Output File

Save the document as a file in the current project — do NOT just print it to chat.

**Location:** `docs/scope/<feature-slug>.md` relative to the current working directory (the project root Claude Code is open in).

**Feature slug:** Derive from the feature name — lowercase, words separated by hyphens, no special characters. Example: "User Login with Email" → `user-login-with-email`.

**Steps:**
1. Determine the current project root (the directory Claude Code is open in)
2. Create `docs/scope/` if it does not exist
3. Write the full document to `docs/scope/<feature-slug>.md`
4. If a file with that name already exists, append a numeric suffix: `<feature-slug>-2.md`
5. If `CLAUDE.md` does not exist at the project root, create it with the content below — if it already exists, skip this step entirely (never overwrite)

**`CLAUDE.md` bootstrap content (only written when file is absent):**
```markdown
# CLAUDE.md

## Scope Documents

Feature scope specifications live in `docs/scope/`.
Each file is named `<feature-slug>.md` and was generated by the `alice-scope-detail` skill.

When working on a feature, read the corresponding scope file in `docs/scope/` for the definition of done and accepted behavior.
```

**Document header:** Begin the saved file with:
```markdown
# <Feature Name>

> Source scope: <original scope text, verbatim>
> Generated: <YYYY-MM-DD>

---
```
Then the 6 sections follow.
