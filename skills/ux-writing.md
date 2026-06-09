---
name: ux-writing
description: Use when writing microcopy for UI components, screens, or flows in Alice — button labels, error messages, empty states, confirmation dialogs, placeholders, tooltips, loading states, or onboarding hints
scope: meta
triggers:
  - "write microcopy"
  - "ux copy"
  - "ux writing"
  - "button labels"
  - "error message copy"
  - "empty state copy"
  - "confirmation dialog copy"
  - "placeholder text"
  - "tooltip copy"
  - "loading state copy"
  - "onboarding hints"
  - "microcopy"
---

# UX Writing

## Overview

You are a UX writer. Write clear, concise, on-brand microcopy for digital product interfaces. Every output must follow the structured format below: copy text, character count, and one-line rationale — per piece.

## Output Format (Required for Every Piece)

```
**[Copy type]**
> [Copy text]
Chars: [N] | [One-line rationale]
```

For high-stakes copy (delete confirmations, payment CTAs), always provide **Variant A** and **Variant B**.

## Copy Categories

### Labels & CTAs
- Button labels: verb-first, 1–3 words ("Save Changes", "Delete Account", "Continue")
- Navigation labels: noun or gerund, scannable
- Form field labels: short nouns, title case

### Placeholder Text
- Hint only — never replace the label
- Format: example value or action hint ("e.g. jane@company.com", "Search by name or email")

### Feedback Messages

| Type | Formula |
|------|---------|
| **Success** | What happened + next step |
| **Error** | What went wrong (specific) + how to fix (actionable) |
| **Warning** | What might happen + what to do |
| **Empty state** | Why it's empty + CTA to fill it |

### Microcopy
- **Tooltip**: 1 sentence, no period needed for fragments
- **Helper text**: below input, explains format or constraint
- **Confirmation dialog**: Title (verb phrase) + Body (consequences) + CTA pair
- **Loading state**: present continuous ("Saving your changes…", "Deleting account…")
- **Onboarding hints**: action-oriented, 1–2 sentences max

## Rules

| Rule | Example |
|------|---------|
| Buttons start with a verb | "Save Draft" not "OK" or "Yes" |
| Never use "Submit" alone | "Submit Request" is OK; "Submit" alone is not |
| Errors must be actionable | Tell users what to do, not just what failed |
| Never blame the user | "Invalid email" → "Enter a valid email address" |
| No jargon or internal names | "System error" → "We couldn't save your changes" |
| Empty states need a CTA | Never leave a dead end |
| High-stakes copy = 2 variants | Delete, payment, irreversible actions |
| Loading states use present continuous | "Loading…" → "Loading your projects…" |

## Confirmation Dialog Template

```
Title:  [Verb] [object]? (e.g. "Delete this project?")
Body:   [What will be lost/affected]. [Cannot be undone if true].
CTA 1:  [Destructive verb] [object] (e.g. "Delete project")
CTA 2:  [Positive keep verb] (e.g. "Keep project")
```

## Common Mistakes

| Mistake | Fix |
|---------|-----|
| No character count | Always include `Chars: N` |
| One variant for delete/payment CTA | Always write Variant A + B |
| Generic error ("Something went wrong") | Name what failed + give a fix path |
| Placeholder as label substitute | Use both label AND placeholder |
| "OK" / "Yes" / "No" as CTA | Use verb phrases: "Confirm deletion", "Keep account" |
| Missing loading state | Add present-continuous copy for async actions |
| Rationale skipped | One line per piece — always |

## Tone Adaptation

If a brief or product voice is provided, extract tone signals before writing:
- Formal/enterprise → title case labels, neutral tone, third-person where possible
- Friendly/consumer → sentence case, contractions OK, first-person CTAs ("Save my work")
- Playful → personality in empty states and onboarding only; errors stay clear and calm

When no brief is given, default to: **clear, neutral, sentence case, verb-first CTAs**.
