---
name: user-persona
description: Use when asked to create user personas from a product brief, feature description, or product idea — especially when the user is a UX researcher, product designer, or PM needing research-grounded personas with design implications
---

# User Persona Creation

## Overview

Create 2–3 research-grounded personas that represent distinct behavioral archetypes — not demographic caricatures. Each persona must include an explicit design implication and flagged assumptions.

## Rules (non-negotiable)

- **2–3 personas only** — never fewer, never more per request
- **At least 1 edge-case user** — less tech-savvy, different context, or underserved scenario; label it explicitly as `[Edge Case]`
- **Base on behavior, not demographics** — age, gender, location are context only; behavioral patterns drive the persona
- **No invented data** — if the brief doesn't support a detail, flag it as `[Assumption: ...]`
- **Every persona ends with a "Design Implication"** — one concrete UX/design decision this persona informs
- **No summary tables** — tables collapse nuance; let each persona speak for itself

## Output Format (follow exactly)

```
**[Persona Name], [Age]** [Edge Case] ← include only if applicable
- **Role:** [Job title / context]
- **Location & usage context:** [Where/when they use the product]
- **Tech comfort:** [1–5] — [one-sentence description of their digital fluency]
- **Core goal:** [What they are trying to achieve with this product]
- **Frustrations with current solutions:** [Specific pain points, not generic]
- **Key behaviors:** [2–4 bullet behaviors directly relevant to the product]
- **Quote:** "[One sentence in their authentic voice]"
- **Design implication:** [One specific, actionable UX decision this persona drives]
- [Assumption: ...] ← list all assumptions after design implication, not inside other fields
```

## Common Mistakes to Avoid

| Mistake | Fix |
|---------|-----|
| Creating 4+ personas | Stop at 3. More personas dilute focus. |
| All personas are tech-savvy | Force at least one edge-case user |
| No design implication | Every persona must end with one |
| Inventing data not in brief | Flag as `[Assumption: ...]` after design implication |
| Assumptions buried inside key behaviors | Move them after design implication |
| Generic quotes ("I want it to be easy") | Write in their specific voice and context |
| Summary table at the end | Remove it — it collapses behavioral nuance |
| Personas defined by demographics | Lead with behaviors and goals, not age/gender |

## Example (abbreviated)

**Linh Tran, 38** [Edge Case]
- **Role:** Owner of a 4-person tailoring shop, manages orders manually
- **Location & usage context:** Uses her phone between customer fittings, rarely sits at a desk
- **Tech comfort:** 2 — uses WhatsApp and Facebook but avoids apps that require setup
- **Core goal:** Know which orders are due this week without a paper notebook
- **Frustrations with current solutions:** Tried a scheduling app once, gave up after the tutorial was too long
- **Key behaviors:**
  - Checks phone in 30-second bursts between tasks
  - Delegates to staff verbally, not digitally
  - Trusts recommendations from peers over app reviews
- **Quote:** "If I have to watch a video to use it, I won't use it."
- **Design implication:** Onboarding must be under 60 seconds with zero required configuration — progressive setup only after first value is delivered.
- [Assumption: Phone model is mid-range Android based on demographic and price sensitivity; not confirmed in brief]

## Checklist Before Delivering

- [ ] Exactly 2–3 personas
- [ ] At least 1 labeled edge-case user
- [ ] Tech comfort uses 1–5 scale with description
- [ ] Each persona has a design implication
- [ ] Assumptions flagged inline with `[Assumption: ...]`
- [ ] No summary table appended
- [ ] Quotes feel specific and authentic to that person
