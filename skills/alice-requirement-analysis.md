---
name: alice-requirement-analysis
description: Use when the user provides a feature description, product brief, user story, or rough idea that needs to be broken down into structured requirements — covering business flow, functional requirements, non-functional requirements, missing cases, and ambiguities before any design or development work begins.
scope: meta
triggers:
  - "analyze requirements"
  - "requirement analysis"
  - "break down requirements"
  - "analyze this feature"
  - "what are the requirements"
  - "identify requirements"
  - "analyze this scope"
  - "find missing cases"
  - "detect ambiguity"
  - "extract use cases"
  - "requirement risks"
---

# Skill: Requirement Analysis

Transforms a rough feature idea or brief into a structured requirement document — covering business flow, functional requirements (FR), non-functional requirements (NFR), extracted use cases, missing cases, ambiguities, and a risk analysis. No assumptions added. No implementation details.

---

## Rules

- Base strictly on what the user provided — do not invent requirements
- Every gap, ambiguity, or risk must be flagged, not filled silently
- Separate FR (what the system does) from NFR (how well it does it)
- Ask clarifying questions before analysis if the brief is too vague to proceed
- Never suggest implementation approach — this skill is analysis only

---

## Step 1 — Receive Input

**Always ask the user this question first before proceeding:**

> "What would you like me to analyze? You can:
> 1. **Paste the text directly** — paste your feature brief, user story, or requirement description here
> 2. **Provide a file path** — share the path to a document (`.md`, `.txt`, `.docx`, etc.) and I'll read it
> 3. **Describe it briefly** — give me a rough description and I'll ask follow-up questions"

Wait for the user's response before continuing.

**If the user provides a file path:**
- Use the Read tool to read the file contents
- Confirm what was read: "I've read `<filename>` — it contains [1-sentence summary]. Proceeding with analysis."
- Use the file contents as the input brief

**If the user provides inline text:**
- Accept it as-is and proceed to Step 2

**If the input is fewer than 2 sentences and has no actor or goal, ask:**
> "Could you tell me more? Specifically: who uses this feature, what do they want to achieve, and what triggers this feature?"

**Optional context to collect (ask only if not already provided):**
- Who are the actors?
- What is the business goal?
- What system does this belong to?

---

## Step 2 — Understand Business Flow

Map the end-to-end flow as the business sees it — not the technical flow.

Output a numbered flow:
```
1. [Actor] initiates [trigger]
2. System performs [action]
3. [Actor] receives [outcome]
4. (Alternate) If [condition], system does [alternative]
```

Identify:
- **Primary actors**: Who interacts with the feature?
- **Trigger**: What starts the flow?
- **Goal**: What is the successful end state?
- **Alternate paths**: What valid variations exist?

---

## Step 3 — Extract Functional Requirements

List what the system **must do** to support the business flow.

Format:
```
FR-01: [System] shall [action] when [condition]
FR-02: [System] shall [action] to [outcome]
```

Group by:
- **Core FRs** — required for the happy path
- **Alternate FRs** — required for valid alternate paths
- **Edge FRs** — boundary conditions the system must handle

Rules:
- Each FR is independently verifiable
- One FR = one behavior
- Do not include "the system should be fast" here → that is an NFR

---

## Step 4 — Extract Non-Functional Requirements

List how well the system must perform — derived only from what is implied or stated.

| Category | Requirement | Source |
|---|---|---|
| Performance | e.g., "Response within 2s under 1000 concurrent users" | [implied / stated] |
| Security | e.g., "Tokens must expire after 30 minutes" | [implied / stated] |
| Availability | e.g., "Feature must be accessible 99.9% of the time" | [implied / stated] |
| Usability | e.g., "Flow must complete in under 3 steps on mobile" | [implied / stated] |
| Scalability | e.g., "Must support 10× current user load" | [implied / stated] |
| Compliance | e.g., "Must store data per GDPR Article 17" | [implied / stated] |

Mark each row **[stated]** or **[implied]**. If neither, omit the row.

---

## Step 5 — Extract Use Cases

Write concise use cases derived from the business flow and FRs.

Format per use case:
```
UC-[number]: [Use Case Title]
- Actor: [who]
- Precondition: [system state before]
- Main Flow: [numbered steps]
- Alternate Flow: [if any]
- Postcondition: [system state after success]
```

Cover:
- Happy path use case(s)
- Alternate path use cases
- Exception use cases (if implied)

---

## Step 6 — Detect Missing Cases & Ambiguities

This is the highest-value section. Identify what the brief did NOT say but must be decided.

### Missing Cases

Things the system will definitely encounter that are not addressed:

| # | Missing Case | Risk if Ignored |
|---|---|---|
| M-01 | What happens when [unaddressed scenario]? | [consequence] |
| M-02 | Who handles [unaddressed actor/role]? | [consequence] |

Common missing case categories to check:
- **Error states**: What if the action fails? What if input is invalid?
- **Concurrent access**: What if two users do this simultaneously?
- **Data states**: Empty state, partial data, corrupted data
- **Permissions**: What if an unauthorized user attempts this?
- **Time/expiry**: Tokens, sessions, scheduled tasks — do they expire?
- **Integration failures**: What if a downstream API is unavailable?
- **Volume edge cases**: Zero items, maximum items, bulk operations
- **Undo/cancel**: Can the user reverse the action?

### Ambiguities

Statements that can be interpreted more than one way:

| # | Ambiguous Statement | Possible Interpretations | Needs Decision From |
|---|---|---|---|
| A-01 | "[quote from brief]" | Option A / Option B | [product owner / tech lead / legal] |

---

## Step 7 — Risk Analysis

Assess risk for the feature based on findings above.

| Risk | Likelihood | Impact | Mitigation Suggestion |
|---|---|---|---|
| [Risk from missing case or ambiguity] | High/Med/Low | High/Med/Low | [one-line suggestion] |

Focus on:
- Requirements that are ambiguous and have high-impact interpretations
- Missing cases that could cause data loss, security breach, or UX failure
- NFRs that are implied but not confirmed — may not be built to spec

---

## Step 8 — Summary & Next Steps

Close with a compact summary:

```
## Summary

- Business Flow: [1-sentence summary]
- Functional Requirements: [count] FRs identified ([count] core, [count] alternate, [count] edge)
- Non-Functional Requirements: [count] NFRs ([list categories])
- Use Cases: [count] UCs extracted
- Missing Cases: [count] flagged
- Ambiguities: [count] flagged
- Risk Level: High / Medium / Low

## Recommended Next Steps

1. Resolve ambiguities A-01, A-02 with [owner]
2. Decide on missing cases M-01, M-03 before development
3. Proceed to scope detail / test case writing / design
```

---

## Output File

Save the document to the project directory — do NOT just print it to chat.

**Location:** `docs/requirements/<feature-slug>.md`

**Feature slug:** Lowercase, hyphens, no special characters. Example: "User Login" → `user-login`.

**Steps:**
1. Determine the current project root
2. Create `docs/requirements/` if it does not exist
3. Write the full document to `docs/requirements/<feature-slug>.md`
4. If the file already exists, append numeric suffix: `<feature-slug>-2.md`

**Document header:**
```markdown
# Requirement Analysis: <Feature Name>

> Source brief: <original input, verbatim or summarised if long>
> Analyst: Alice (AI)
> Date: <YYYY-MM-DD>

---
```

After saving, confirm the file path and ask:
> "Would you like me to adjust any section, resolve specific ambiguities, or proceed to scope detail / test case writing?"

---

## Quality Check (self-run before saving)

- [ ] Every FR is independently verifiable (one behavior per FR)
- [ ] No FR contains performance/quality constraints (those belong in NFRs)
- [ ] Every NFR is marked [stated] or [implied] with source
- [ ] Every use case has actor, precondition, main flow, and postcondition
- [ ] Missing cases cover all 8 categories checked (or marked N/A)
- [ ] Every ambiguity includes at least 2 interpretations and a decision owner
- [ ] Risk table includes likelihood, impact, and mitigation
- [ ] Summary counts match actual content

---

## Common Mistakes

| Mistake | Fix |
|---|---|
| Mixing FR and NFR | FRs = what; NFRs = how well. "Must authenticate users" = FR. "Must authenticate in <500ms" = NFR. |
| Filling in missing cases silently | Flag them — let the product owner decide, not the analyst |
| Writing ambiguities without decision owner | Every ambiguity needs a human to resolve it |
| Treating use cases as test cases | Use cases describe behavior; test cases verify it |
| Risk analysis without mitigation | Always pair risk with at least a one-line mitigation |

---

## Red Flags — Stop and Correct

These thoughts mean you are about to violate the skill's rules:

| Thought | Reality |
|---|---|
| "I'll just assume it works like X" | You are inventing a requirement. Flag it as ambiguous instead. |
| "This missing case is obvious, so I'll fill it in" | Missing cases are decisions for product owners, not analysts. List it in Section 6. |
| "Performance requirements aren't relevant here" | Performance is always relevant. Mark implied NFRs as [implied] if not stated. |
| "I'll skip the risk table since the feature is simple" | Simple features have overlooked risks. Always complete the risk table. |
| "The user flow is clear, I don't need to map it" | The business flow is the foundation — every FR traces back to it. Always map it. |
| "I'll combine FR and NFR to save space" | Mixing them creates ambiguous requirements. Keep them separate, always. |
| "There are no ambiguities in this brief" | Every brief has ambiguities. Look harder — especially at actors, triggers, and error cases. |
