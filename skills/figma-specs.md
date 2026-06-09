---
name: figma-specs
description: Use when writing Figma developer handoff specs for components or screens in Alice — Auto Layout, layer hierarchy, constraints, tokens, interaction notes, or any spec a developer needs to implement without opening Figma
scope: meta
triggers:
  - "figma spec"
  - "figma handoff"
  - "developer handoff"
  - "component spec"
  - "auto layout spec"
  - "layer structure"
  - "token references"
  - "figma specs"
  - "design spec"
  - "handoff documentation"
---

# Figma Specs

## Overview

Developer handoff specs must be complete enough that no developer ever needs to open Figma to guess a value. Every section is required. Never write "see design."

## Required Output Sections (all mandatory)

### 1. Component Specs
- **Component name:** exact Figma component name (e.g. `Button/Primary/md/default`)
- **Figma location:** Page > Frame > Component path
- **Variant properties:** list all (e.g. Size: sm/md/lg, State: default/hover/pressed/disabled/loading)

### 2. Auto Layout Table

| Property | Value | Token |
|----------|-------|-------|
| Direction | Horizontal / Vertical | — |
| Alignment | Top-left / Center / Space-between / etc. | — |
| Gap | Xpt | `spacing.X` |
| Padding | top Xpt / right Xpt / bottom Xpt / left Xpt | `spacing.X` |
| Width | Fixed Xpt / Fill container / Hug content | — |
| Height | Fixed Xpt / Fill container / Hug content | — |

**All measurements in pt (not px).** Mobile min touch target: 44×44pt [iOS] / 48×48pt [Android].

### 3. Layer Structure

Exact layer tree with element types:

```
ComponentName/
├── Background (rectangle)
├── Content (frame, horizontal auto-layout)
│   ├── LeadingIcon (24×24pt, SVG)
│   └── Label (text, type.label.md)
└── FocusRing (rectangle, stroke only, hidden by default)
```

Rules:
- Use PascalCase layer names
- State each element's type in parentheses
- List all layers including hidden ones (note: `hidden by default`)
- Note absolute-positioned layers explicitly

### 4. Constraints

- How the component stretches or pins within its parent frame
- Min/Max width or height (e.g. `min-width: 80pt`, `max-width: fill`)
- Responsive behavior: does it fill width on mobile?

### 5. Interactive States

List **every** state — not just default:

| State | Visual Change | Behavioral Change |
|-------|---------------|-------------------|
| default | ... | ... |
| hover | ... | pointer cursor |
| pressed | ... | scale 0.98 |
| focus-visible | focus ring visible | keyboard nav only |
| disabled | opacity 0.4, no pointer events | aria-disabled="true" |
| loading | spinner visible | aria-busy="true", blocks interaction |

For animation on state change → reference **motion-design skill** for full spec.

### 6. Interaction Notes

- Tap/click behavior (what happens)
- Transition target: screen name or overlay name (e.g. "→ Sheet/Confirmation")
- Animation: reference motion-design skill (e.g. "entrance: bottom sheet enter spec")

### 7. Token References Table

Every token used — no raw values, no "see design":

| Element | Property | Token |
|---------|----------|-------|
| Background | fill | `color.bg.primary.default` |
| Label | color | `color.text.inverse` |
| Label | typography | `type.label.md` |
| Border | stroke | `color.border.default` |
| Root | border-radius | `radius.md` |
| Root | padding-x | `spacing.md` |

---

## Platform Flags

Flag any spec that differs between iOS and Android with `[iOS]` / `[Android]` inline:

```
Border radius: 8pt [iOS] / 4pt [Android — follows Material shape tokens]
Tap feedback: scale 0.98 [iOS] / ripple effect [Android]
Min touch target: 44×44pt [iOS HIG] / 48×48pt [Android Material]
```

---

## Common Mistakes

| Mistake | Fix |
|---------|-----|
| "See design for exact values" | Never. Specify every value. |
| px instead of pt | Mobile specs use pt. Web: px is fine, flag it. |
| Missing states | List all 6 states minimum: default, hover, pressed, focus-visible, disabled, loading |
| Missing layer hierarchy | Always include ASCII tree with element types |
| No Figma file location | Always include Page > Frame > Component path |
| Tokens without element mapping | Use Token References table — element + property + token per row |
| No platform flags | Call out iOS vs Android differences explicitly |
| No touch target note | Always note 44pt (iOS) / 48pt (Android) minimum |

---

## Example: Primary Button (md, default state)

**Component Specs**
- Name: `Button/Primary/md/default`
- Location: Design System > Components > Buttons > PrimaryButton
- Variants: Size (sm/md/lg) × State (default/hover/pressed/focus-visible/disabled/loading) × hasLeadingIcon (true/false)

**Auto Layout**

| Property | Value | Token |
|----------|-------|-------|
| Direction | Horizontal | — |
| Alignment | Center / Center | — |
| Gap | 8pt | `spacing.xs` |
| Padding | top 12pt / right 20pt / bottom 12pt / left 20pt | `spacing.sm` / `spacing.md` |
| Width | Hug content | — |
| Height | Fixed 44pt | `size.height.md` |

**Layer Structure**
```
PrimaryButton/
├── Background (rectangle, fill + radius)
├── Content (frame, horizontal auto-layout, hug×hug)
│   ├── LeadingIcon (16×16pt, SVG, hidden when hasLeadingIcon=false)
│   └── Label (text, type.label.md)
└── FocusRing (rectangle, stroke only, hidden by default)
```

**Constraints**
- Hugs content horizontally; stretches to Fill if placed in a full-width container
- Min-width: 80pt
- Touch target: naturally 44pt height at md size

**Token References**

| Element | Property | Token |
|---------|----------|-------|
| Background | fill | `color.bg.primary.default` |
| Background | border-radius | `radius.md` |
| Label | color | `color.text.inverse` |
| Label | typography | `type.label.md` |
| LeadingIcon | color | `color.icon.inverse` |
| Root | padding-x | `spacing.md` |
| Root | padding-y | `spacing.sm` |
| FocusRing | stroke | `color.border.focus` |
| FocusRing | stroke-width | 2pt |

**Platform Flags**
- Pressed feedback: scale 0.98 [iOS] / ripple effect [Android]
- Min touch target: 44×44pt [iOS HIG] / 48×48pt [Android Material]
