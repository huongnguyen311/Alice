---
name: component-design
description: Use when designing a UI component from scratch, specifying a component for Figma handoff, documenting component anatomy and variants, or producing component specs for a design system. Triggers on "component spec", "component design", "design component", "Figma component", "component anatomy", "variant matrix".
---

# Component Design

## Overview

Produce a complete component specification ready for Figma implementation. Every component must be fully defined — anatomy, variants, specs, accessibility, and states — before any design or code work begins.

**Core rule:** Never hardcode values. Always reference design tokens (spacing, color, typography, radius).

---

## Output Structure

Deliver all six sections below, in order, for every component.

---

### 1. Component Overview

- **Purpose** — what problem it solves in one sentence
- **When to use** — concrete scenarios where this component is appropriate
- **When NOT to use** — anti-patterns or cases where a different component fits better
- **Related components** — list siblings/parents/children by name

---

### 2. Anatomy

List every layer that makes up the component. Use **PascalCase** for all layer names (matches Figma convention).

| Layer Name | Element Type | Required? |
|------------|-------------|-----------|
| Root | container | Required |
| Label | text | Required |
| LeadingIcon | icon | Optional |
| TrailingIcon | icon | Optional |
| Spinner | icon/animation | Optional |

> Add or remove rows to match the actual component. Never leave unnamed layers.

---

### 3. Variant Matrix

Enumerate every property and its allowed values as a table. These become Figma component properties.

| Property | Values |
|----------|--------|
| Size | sm / md / lg |
| State | default / hover / pressed / disabled / loading |
| Type | [component-specific — e.g. primary / secondary / ghost / danger] |
| hasLeadingIcon | true / false |
| hasTrailingIcon | true / false |

> Only add properties that produce a visually or behaviorally distinct output. Avoid combinatorial explosion — flag impossible combinations explicitly (e.g., "loading + disabled not supported").

---

### 4. Specs

For each **Size × Type** combination, define:

| Token Category | Spec |
|----------------|------|
| Width | hug / fill / fixed (reference breakpoint token if fixed) |
| Height | `size.height.{sm\|md\|lg}` |
| Padding (horizontal) | `spacing.{xs\|sm\|md\|lg}` |
| Padding (vertical) | `spacing.{xs\|sm\|md\|lg}` |
| Gap (between elements) | `spacing.{xs\|sm\|md\|lg}` |
| Border radius | `radius.{none\|sm\|md\|lg\|full}` |
| Typography | `type.{label\|body\|caption}.{sm\|md\|lg}` |
| Background color | `color.bg.{primary\|secondary\|surface\|...}` |
| Text color | `color.text.{primary\|inverse\|disabled\|...}` |
| Border color | `color.border.{default\|focus\|error\|...}` |
| Icon color | `color.icon.{default\|inverse\|disabled\|...}` |
| Shadow | `elevation.{none\|sm\|md\|lg}` |

> One table per size tier (sm / md / lg). Call out any token that differs between Types within the same size.

---

### 5. Accessibility

| Attribute | Value |
|-----------|-------|
| ARIA role | e.g. `button`, `checkbox`, `dialog` |
| ARIA label | How to label when no visible text |
| ARIA expanded / selected / checked | If applicable |
| Minimum touch target | 44×44pt (mobile) — pad with invisible area if needed |
| Contrast ratio | Text on background ≥ 4.5:1 (WCAG AA); large text ≥ 3:1 |
| Focus indicator | Visible ring using `color.border.focus`; ≥ 3:1 contrast against adjacent color |
| Keyboard navigation | Tab, Enter/Space, Arrow keys — describe expected behavior |
| Screen reader announcement | What the SR reads on focus and on activation |

---

### 6. States

Describe **visual changes** and **behavioral changes** for every state. Flag animations.

| State | Visual Change | Behavioral Change | Animation? |
|-------|--------------|-------------------|------------|
| default | — | Fully interactive | — |
| hover | `color.bg.{component}.hover` | Cursor: pointer | — |
| pressed | `color.bg.{component}.pressed`, scale `0.98` | Active feedback | `transition: transform 100ms ease-out` ⚡ |
| focus-visible | Focus ring: `color.border.focus`, `2px` offset | Keyboard focus indicator | — |
| disabled | `color.bg.disabled`, `color.text.disabled`, `opacity.disabled` | No interaction, `aria-disabled="true"` | — |
| loading | Spinner replaces or overlays content | Blocks interaction | `Spinner` rotates `360deg` loop `600ms` linear ⚡ |
| error | `color.border.error`, error icon visible | Validation message shown | — |

> ⚡ = animation required. For each animation: describe property, duration, easing, and trigger.

**Every component MUST have a disabled state. No exceptions.**

---

## Rules (Non-Negotiable)

1. **No hardcoded values** — every measurement, color, and type style must reference a token.
2. **Disabled state required** — every component, every variant.
3. **Touch targets ≥ 44×44pt** on mobile — add invisible padding zones if the visual is smaller.
4. **Layer names in PascalCase** — e.g. `LeadingIcon`, not `leading-icon` or `icon_left`.
5. **Flag every animation** with ⚡ and specify: property, duration, easing, trigger.
6. **No impossible combinations** — list them explicitly in the Variant Matrix section.

---

## Quick Reference Checklist

Before handing off, verify:

- [ ] All 6 sections present
- [ ] Every layer named in PascalCase
- [ ] No raw hex/px values — only token references
- [ ] Disabled state defined
- [ ] Touch target ≥ 44×44pt documented
- [ ] Contrast ratios called out
- [ ] Animations flagged with ⚡ + full transition spec
- [ ] Impossible variant combinations noted

---

## Common Mistakes

| Mistake | Fix |
|---------|-----|
| `padding: 12px` | `padding: spacing.md` |
| `color: #0070F3` | `color: color.bg.primary` |
| Missing disabled state | Always add disabled — it's required |
| Layer named `icon-left` | Rename to `LeadingIcon` |
| Loading + disabled combined | Flag as unsupported in Variant Matrix |
| Skipping focus-visible state | Required for keyboard accessibility |
| Touch target only described visually | Specify invisible padding zone for targets < 44pt |
