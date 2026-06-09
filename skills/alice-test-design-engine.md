---
name: alice-test-design-engine
description: Use when the user asks to write test cases, test scenarios, or a test plan — especially for a feature, module, user story, or scope document. Triggers on "write TCs", "write test plan", "generate test scenarios", "ISTQB", "test design", "test coverage", or any request to create QA artifacts.
scope: meta
triggers:
  - "write test plan"
  - "generate test plan"
  - "write test cases"
  - "write TCs"
  - "generate test cases"
  - "write test scenarios"
  - "generate scenarios"
  - "ISTQB test"
  - "test design"
  - "test coverage"
  - "equivalence partitioning"
  - "boundary value analysis"
  - "decision table testing"
  - "state transition testing"
  - "use case testing"
  - "test design engine"
---

# Skill: Test Design Engine

Generates ISTQB-compliant QA artifacts — Test Plan, Test Cases, and Test Scenarios — from any input document (scope, requirement, user story, feature brief). Applies ISTQB test design techniques to ensure coverage. Never invents behavior not stated or implied in the source.

---

## Step 0 — Ask User to Select Artifacts

Before doing anything else, ask:

> "Which QA artifacts would you like me to generate?
> **A.** Test Plan (ISTQB 18-section template)
> **B.** Test Cases (structured format with ISTQB techniques)
> **C.** Test Scenarios (structured scenario format)
> **D.** All of the above"

If the source document is already provided inline or via file path, ask only the artifact selection question. If the source document is NOT provided, combine both into one message:

> "Which artifacts would you like? A / B / C / D
> Also, please share your source document — paste inline, provide a file path, or name a feature."

Wait for the answer. Generate only selected artifacts.

---

## Step 1 — Analyze Source Document

**Auto-run without asking** — do not pause for confirmation.

If the `alice-requirement-analysis` skill has already analyzed this feature, read its output from `docs/requirements/<feature-slug>.md` and skip re-analysis.

Otherwise, derive from the source document:
1. Feature name, actors, main flow, error cases — summarize in 3–5 bullets (print to chat)
2. Select applicable ISTQB techniques (see table below) — auto-select, do not ask user
3. **Flag gaps only** if a critical piece is genuinely missing (e.g., no actor defined, no flows described) — ask at most 5 focused questions in one message, then proceed

### ISTQB Technique Selection

| Technique | Apply when source has... |
|---|---|
| **Equivalence Partitioning (EP)** | Input fields with valid/invalid value ranges |
| **Boundary Value Analysis (BVA)** | Numeric ranges, character limits, dates, quantities |
| **Decision Table (DT)** | Multiple conditions with different outcomes (if/else logic) |
| **State Transition (ST)** | Objects/entities with statuses or lifecycle stages |
| **Use Case Testing (UCT)** | Defined user flows with alternates and exceptions |

Apply ALL relevant techniques. Do not apply only happy-path testing.

---

## Step 2 — Generate Test Cases (if selected)

Use the structured format in `tc-formats.md` (see supporting file).

**Coverage rules — mandatory:**
- EP: At least one TC per valid partition, one per invalid partition
- BVA: TC at min−1, min, min+1, max−1, max, max+1 for every boundary
- DT: One TC per rule row in the decision table
- ST: One TC per valid transition, one TC per invalid transition attempt
- UCT: TC for main flow, each alternate flow, each exception flow

**Group TCs into sections:**
1. Happy Path
2. Alternate Paths
3. Edge Cases / Boundary Values
4. Error Cases / Negative Tests
5. State Transitions (if applicable)

**Number sequentially:** TC-01, TC-02, ... across all groups.

**Priority rules:**
- High: Core happy path, security checks, data integrity
- Medium: Alternate paths, most edge cases
- Low: Cosmetic, rare edge cases

After generating, append **Coverage Matrix**:
```
| Requirement / Acceptance Criterion | TC IDs | Technique Used |
|---|---|---|
| [criterion] | TC-01, TC-04 | EP, BVA |
```
Every requirement must map to at least one TC. If any is uncovered, add a TC before finalizing.

---

## Step 3 — Generate Test Scenarios (if selected)

Use the structured format in `tc-formats.md` (see supporting file).

Each scenario covers a meaningful end-to-end user journey — NOT a single step.

**Coverage rules:**
- One scenario per main actor goal
- One scenario per significant alternate path
- One scenario per exception flow
- Scenarios reference their covered TCs

**Number sequentially:** TS-01, TS-02, ...

---

## Step 4 — Generate Test Plan (if selected)

Use the full ISTQB template in `test-plan-template.md` (see supporting file).

**Mandatory sections:** All 18 sections must be present. Never omit a section — write "N/A — [reason]" if genuinely not applicable.

**Key rules:**
- Section 6.3 Test Techniques must list which ISTQB techniques are used and WHY
- Entry Criteria and Exit Criteria must be measurable (%, count, specific condition)
- Risk table must have likelihood, impact, AND mitigation for every risk

---

## Step 5 — Save Artifacts

Save all files to the project directory. Do NOT just print to chat.

| Artifact | File path |
|---|---|
| Test Plan | `docs/tcs/<feature-slug>-plan.md` |
| Test Cases | `docs/tcs/<feature-slug>-tcs.md` |
| Test Scenarios | `docs/tcs/<feature-slug>-scenarios.md` |

**Feature slug:** Lowercase, hyphens, no special characters. Example: "User Login" → `user-login`.

If file exists, append numeric suffix: `<feature-slug>-2.md`.

Each file begins with:
```markdown
# [Artifact Title]: <Feature Name>

> Source: <file path or inline summary>
> Generated: <YYYY-MM-DD>
> Standard: ISTQB / ISO/IEC/IEEE 29119

---
```

After saving, confirm file paths and ask:
> "Would you like me to export to Google Drive, add more techniques, or adjust coverage?"

---

## Quality Check (self-run before saving)

- [ ] All selected ISTQB techniques applied (EP, BVA, DT, ST, UCT as applicable)
- [ ] Every TC has: ID, Name, Module, Priority, Type, Preconditions, Test Data, Steps, Expected Result
- [ ] Every Scenario has: ID, Title, Module, Description, Role, Preconditions, Main Flow, Alternate Flows, Exception Flows, Type, Priority
- [ ] Test Plan has all 18 sections present (none silently omitted)
- [ ] Coverage matrix maps every requirement to at least one TC
- [ ] BVA boundaries: min−1, min, min+1, max−1, max, max+1 all covered
- [ ] Decision Table: every rule row has a TC
- [ ] State Transition: every valid + invalid transition has a TC
- [ ] TC numbers sequential with no gaps
- [ ] Scenario Alternate and Exception flows are present (not just main flow)

---

## Common Mistakes

| Mistake | Fix |
|---|---|
| Only writing happy path TCs | Apply EP and BVA — invalid partitions and boundary values must be tested |
| Confusing Scenario with TC | Scenario = end-to-end journey (narrative); TC = single executable check (steps + expected result) |
| Skipping Decision Table | Any if/else logic in requirements needs a DT-derived TC set |
| Omitting State Transition TCs | Any entity with a status field (order, ticket, user account) needs ST testing |
| Missing BVA boundaries | Must test min−1, min, min+1, max−1, max, max+1 — not just "valid" and "invalid" |
| Test Plan with missing sections | All 18 sections mandatory — write N/A with reason rather than omit |
| No coverage matrix | Every TC must trace to a requirement or acceptance criterion |

---

## Red Flags — Stop and Correct

| Thought | Reality |
|---|---|
| "Happy path covers the main cases" | EP requires invalid partitions. BVA requires boundaries. Both are mandatory. |
| "The scenario has steps so it's fine as a TC" | Scenarios are journeys, not executable checks. Write separate TCs. |
| "I'll skip the Decision Table — it's obvious" | If there are conditions with different outcomes, a Decision Table is required. |
| "State transitions aren't relevant here" | Any field named status, stage, state, or phase requires State Transition testing. |
| "Some Test Plan sections don't apply" | Write "N/A — [reason]". Never silently omit a section. |
| "I'll add the coverage matrix later" | Coverage matrix is part of TC generation. Do it before saving. |
