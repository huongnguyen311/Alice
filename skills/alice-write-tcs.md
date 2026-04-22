---
name: alice-write-tcs
description: Generate Test Cases, Testing Plan, and Test Scenarios from project documents via Alice — following general QA/QC standards, with AI follow-up for missing info, output language choice, and Google Workspace export.
scope: meta
triggers:
  - "write test cases"
  - "write TCs"
  - "generate test cases"
  - "create test cases"
  - "write TC for"
  - "test cases for"
  - "generate TCs"
  - "write test scenarios"
  - "create TCs"
  - "write testing plan"
  - "generate test plan"
  - "write QA artifacts"
---

# Skill: Write Test Cases (TCs)

Generates full QA artifacts — Test Cases, Testing Plan, and Test Scenarios — from project documents. Follows general QA/QC standards. Supports English, Vietnamese, or Bilingual output. Saves locally and optionally exports to Google Workspace.

---

## Step 1 — Input Documents

Ask the user for **two things in one message**:

1. **Output language**: English / Vietnamese / Bilingual (EN + VI side by side)
2. **Project documents**: Paste inline, share a scope file path, or upload a file (TXT, PDF, DOCX)

Priority order for locating documents:
1. User pastes content inline → use directly
2. User names a feature → look for `docs/scope/<feature-slug>.md` in the project
3. User provides a file path → read the file
4. None provided → ask: *"Please share your project documents — paste them here, or tell me the feature name or file path."*

---

## Step 2 — AI Analysis & Follow-up

After receiving the documents:

1. **Summarise** what was understood — feature name, actors, main flow, listed error cases
2. **Identify gaps** — information required to write complete TCs that is missing from the doc
3. If gaps exist: ask **at most 5 focused questions** in a single message
4. If the document is complete and no gaps exist: **skip this step automatically** and proceed to Step 3

Questions must be specific and actionable. Do not ask vague questions like "Can you clarify the scope?" — instead ask "What should happen when a user submits with an empty required field?"

---

## Step 3 — Generate QA Artifacts

Before generating anything, ask the user which artifacts they want:

> "Which artifacts would you like me to generate?
> - A. Test Cases
> - B. Testing Plan
> - C. Test Scenarios
> - D. All of the above"

Wait for the user's answer. Generate only the selected artifacts.

All artifacts must follow general QA/QC standards. All output must be in the language chosen in Step 1.

---

### Artifact A: Test Cases

Each test case uses this format:

```
**TC-[number]: [Short descriptive title]**
| Field | Value |
|---|---|
| **Test Case ID** | TC-[number] |
| **Test Case Name** | [Descriptive name of the test case] |
| **Feature** | [Feature name] |
| **Type** | Happy Path / Edge Case / Error Case |
| **Test Type** | Functional / Regression / Smoke / Sanity / Integration / UI |
| **Priority** | High / Medium / Low |
| **Preconditions** | [System state before test] |
| **Test Data** | [Input values, user accounts, or data needed to run this TC] |
| **Test Steps** | 1. [Action] → 2. [Action] → ... |
| **Expected Result** | [What correct behavior looks like] |
| **Actual Result** | _(leave blank — filled during execution)_ |
| **Status** | _(Passed / Failed — filled during execution)_ |
| **Note** | _(leave blank — optional remarks during execution)_ |
```

Group into sections:
- **Happy Path** — main success flows from the User Flow
- **Edge Cases** — boundary inputs and non-obvious valid states implied by scope
- **Error Cases** — one TC per error case listed in scope (omit section if none)

Number sequentially across all groups: TC-01, TC-02, ...

---

### Artifact B: Testing Plan

Produce a document with these sections:

1. **Introduction** — purpose, scope of testing, referenced documents
2. **Test Objectives** — what the test effort aims to verify
3. **Test Scope**
   - In scope: features and flows covered
   - Out of scope: explicitly excluded areas
4. **Test Approach** — types of testing (functional, regression, boundary, etc.)
5. **Entry & Exit Criteria**
   - Entry: conditions required before testing begins
   - Exit: conditions that mark testing as complete
6. **Test Environment** — required system setup, tools, data
7. **Test Deliverables** — list of artifacts produced (this plan, TCs, scenarios, reports)
8. **Risks & Mitigations** — known risks and how they are handled
9. **Schedule** — phases and activities (use placeholder dates if not provided)

---

### Artifact C: Test Scenarios

High-level end-to-end scenarios, each covering a meaningful user journey:

```
**TS-[number]: [Scenario title]**
- **Goal**: What this scenario validates end-to-end
- **Actor**: Who performs the actions
- **Preconditions**: Starting system state
- **Flow summary**: Narrative of actions and outcomes (not step-by-step)
- **Covered TCs**: TC-01, TC-03, TC-07
- **Pass Criteria**: Conditions under which this scenario is considered passed
```

Number sequentially: TS-01, TS-02, ...

---

### Coverage Checklist

After all artifacts, add a checklist mapping every acceptance criterion to at least one TC and one TS:

```
- ✅ [Acceptance criterion] → TC-01, TC-03 | TS-01
- ✅ [Acceptance criterion] → TC-05 | TS-02
```

Every criterion must be covered. If any is missing, add a TC before finalising.

---

## Step 4 — Save & Export

### Local Save

Save three files in the current project:

| Artifact | File path |
|---|---|
| Test Cases | `docs/tcs/<feature-slug>.md` |
| Testing Plan | `docs/tcs/<feature-slug>-plan.md` |
| Test Scenarios | `docs/tcs/<feature-slug>-scenarios.md` |

**Feature slug:** Derive from the feature name — lowercase, hyphens, no special characters.
If a file already exists, append a numeric suffix: `<feature-slug>-2.md`.

Each file begins with:
```markdown
# [Artifact Title]: <Feature Name>

> Source: <scope file path or inline summary>
> Generated: <YYYY-MM-DD>
> Standard: QA/QC general standards

---
```

### Google Workspace Export

After saving locally, ask: *"Would you like me to export these artifacts to Google Drive as a Google Doc?"*

If yes:
1. Create a Google Doc for each artifact using `mcp__google-workspace__createDocument`
2. Write the full markdown content into the doc using `mcp__google-workspace__replaceDocumentWithMarkdown`
3. Confirm the doc link(s) to the user

---

## Quality Check (self-run before saving)

- [ ] Every TC step is clear and executable by any team member
- [ ] Every TC has preconditions, steps, and expected result filled
- [ ] No TC tests behavior not stated or implied in the source documents
- [ ] Every acceptance criterion covered by at least one TC and one TS
- [ ] Testing Plan covers all 9 required sections
- [ ] Test Scenarios reference their covered TCs
- [ ] TC numbers are sequential with no gaps
- [ ] Output language matches the user's choice from Step 1

---

## Rules

- Base all TCs strictly on the provided documents — do not invent untested behavior
- Each TC must be independently executable — no hidden dependencies on other TCs
- Use clear, unambiguous language that any QA engineer can follow
- Every TC maps to at least one acceptance criterion or system behavior
- Follow general QA/QC standards for all artifact structure and content
