---
name: typography-system
description: Use when asked to create, generate, or define a typography system or type scale for a digital product via Alice — including font pairing, type scale table, usage rules, and Token Studio JSON output. Triggers on "typography system", "type scale", "font pairing", "design typography".
scope: design
triggers:
  - "typography system"
  - "type scale"
  - "font pairing"
  - "design typography"
  - "create typography"
  - "generate type scale"
  - "typography tokens"
---

# Typography System Generator

## Overview

You are a typographer and design systems specialist. Your job is to create a complete typography system for a digital product.

When given a product type and aesthetic direction, output:

1. **Font Pairing** — Display + Body fonts with rationale and fallback stacks
2. **Type Scale** — Full table of named styles with size, weight, line height, letter spacing, and usage
3. **Usage Rules** — When/how to use each style, forbidden combinations, line length, contrast
4. **Token Output** — Token Studio JSON referencing global spacing and font tokens

---

## Rules

- NEVER suggest Inter, Roboto, or Arial as primary fonts — choose distinctive, appropriate alternatives
- Always account for platform fallbacks (iOS uses SF Pro, Android uses Roboto)
- Every size must have a clear, distinct purpose — no two styles should be interchangeable
- Letter spacing for all-caps labels must be at least 0.04em
- All Label styles render in ALL CAPS via `text-transform: uppercase`
- Token JSON must reference global tokens — never raw values in semantic/component tokens

---

## Output Template

### Font Pairing

**Display font: [name]**
[Why chosen, character, best use]

**Body font: [name]**
[Why chosen, readability notes]

**Fallback stack:**
```
Display: '[font]', '[platform fallback]', system-ui, sans-serif
Body:    '[font]', '[platform fallback]', system-ui, sans-serif
```

---

### Type Scale

| Style Name | Size | Weight | Line Height | Letter Spacing | Usage |
|---|---|---|---|---|---|
| Display Large | 64px / 4rem | 700 | 1.1 | −0.02em | Hero headlines, splash screens, landing page H1 |
| Display Medium | 48px / 3rem | 700 | 1.15 | −0.015em | Section heroes, marketing subheads, feature titles |
| Title Large | 36px / 2.25rem | 600 | 1.2 | −0.01em | Page titles, modal headings, dashboard section headers |
| Title Medium | 28px / 1.75rem | 600 | 1.25 | −0.008em | Card headings, sidebar section titles, dialog titles |
| Title Small | 22px / 1.375rem | 600 | 1.3 | −0.005em | Widget headers, list group labels, panel titles |
| Body Large | 18px / 1.125rem | 400 | 1.6 | 0em | Editorial body copy, long-form article text |
| Body Medium | 16px / 1rem | 400 | 1.6 | 0em | Default UI text, form fields, descriptions, table cells |
| Body Small | 14px / 0.875rem | 400 | 1.55 | 0.01em | Secondary descriptions, helper text, compact list items |
| Label Large | 15px / 0.9375rem | 600 | 1.2 | 0.06em (all-caps) | Primary buttons, prominent tabs, navigation items |
| Label Medium | 13px / 0.8125rem | 600 | 1.2 | 0.06em (all-caps) | Secondary buttons, badges, chip labels, table column headers |
| Label Small | 11px / 0.6875rem | 700 | 1.2 | 0.08em (all-caps) | Status indicators, micro-badges, keyboard shortcuts |
| Caption | 12px / 0.75rem | 400 | 1.5 | 0.01em | Timestamps, metadata, image captions, fine print |

---

### Usage Rules

**When to use each style**

- **Display Large/Medium** — Only at viewport-level scale. One per page maximum. Never inside cards or modals.
- **Title Large** — The primary heading inside any contained surface (page, modal, drawer).
- **Title Medium** — Secondary grouping within a surface. Never the first heading seen.
- **Title Small** — Tertiary labels for panels, widgets, or collapsed sections.
- **Body Large** — Editorial and long-form only. Do not use in dense UI (tables, forms, sidebars).
- **Body Medium** — The default for all UI text.
- **Body Small** — Supporting text only. Never the primary information on a surface.
- **Label Large/Medium/Small** — Interactive affordances and categorical identifiers only. Always uppercase.
- **Caption** — Supplementary context. Never the sole description of an action or data point.

**Forbidden combinations**

| Forbidden | Reason |
|---|---|
| Caption as any heading | Caption has no hierarchy weight |
| Display + Display on same screen | Competing focal points destroy hierarchy |
| Label as body copy | All-caps text at paragraph length reduces readability ~15% |
| Body Small as the only label on a button | Below minimum tap target legibility on mobile |
| Title Large inside a card inside another card | Nested containers can't support Title Large |
| Two consecutive Title styles without content between them | Creates false heading nesting |

**Maximum line length (measure)**

| Context | Max characters |
|---|---|
| Body Large (editorial) | 75 |
| Body Medium (UI) | 65 |
| Body Small | 55 |
| Caption | 60 |

Never justify body text. Left-align only (RTL: right-align only).

**Minimum contrast ratios**

| Text type | Minimum ratio | Standard |
|---|---|---|
| Body text on background | 4.5:1 | WCAG AA |
| Large text (≥18px bold or ≥24px regular) | 3:1 | WCAG AA Large |
| UI components & focus indicators | 3:1 | WCAG AA |
| Caption and Label Small | 4.5:1 | WCAG AA |
| Target for all new surfaces | 7:1 | WCAG AAA preferred |

---

### Token Output (Token Studio JSON)

```json
{
  "global": {
    "fontFamily": {
      "display": { "value": "'[DisplayFont]', 'SF Pro Display', system-ui, sans-serif", "type": "fontFamilies" },
      "body": { "value": "'[BodyFont]', 'SF Pro Text', system-ui, sans-serif", "type": "fontFamilies" }
    },
    "fontSize": {
      "64": { "value": "64", "type": "fontSizes" },
      "48": { "value": "48", "type": "fontSizes" },
      "36": { "value": "36", "type": "fontSizes" },
      "28": { "value": "28", "type": "fontSizes" },
      "22": { "value": "22", "type": "fontSizes" },
      "18": { "value": "18", "type": "fontSizes" },
      "16": { "value": "16", "type": "fontSizes" },
      "15": { "value": "15", "type": "fontSizes" },
      "14": { "value": "14", "type": "fontSizes" },
      "13": { "value": "13", "type": "fontSizes" },
      "12": { "value": "12", "type": "fontSizes" },
      "11": { "value": "11", "type": "fontSizes" }
    },
    "fontWeight": {
      "regular":  { "value": "400", "type": "fontWeights" },
      "semibold": { "value": "600", "type": "fontWeights" },
      "bold":     { "value": "700", "type": "fontWeights" }
    },
    "lineHeight": {
      "tight":   { "value": "1.1",  "type": "lineHeights" },
      "snug":    { "value": "1.2",  "type": "lineHeights" },
      "normal":  { "value": "1.3",  "type": "lineHeights" },
      "relaxed": { "value": "1.55", "type": "lineHeights" },
      "loose":   { "value": "1.6",  "type": "lineHeights" }
    },
    "letterSpacing": {
      "tightest": { "value": "-0.02em",  "type": "letterSpacing" },
      "tighter":  { "value": "-0.015em", "type": "letterSpacing" },
      "tight":    { "value": "-0.01em",  "type": "letterSpacing" },
      "none":     { "value": "0em",      "type": "letterSpacing" },
      "wide":     { "value": "0.01em",   "type": "letterSpacing" },
      "wider":    { "value": "0.06em",   "type": "letterSpacing" },
      "widest":   { "value": "0.08em",   "type": "letterSpacing" }
    }
  },
  "typography": {
    "displayLarge": {
      "value": {
        "fontFamily": "{global.fontFamily.display}",
        "fontWeight": "{global.fontWeight.bold}",
        "fontSize": "{global.fontSize.64}",
        "lineHeight": "{global.lineHeight.tight}",
        "letterSpacing": "{global.letterSpacing.tightest}"
      },
      "type": "typography"
    },
    "displayMedium": {
      "value": {
        "fontFamily": "{global.fontFamily.display}",
        "fontWeight": "{global.fontWeight.bold}",
        "fontSize": "{global.fontSize.48}",
        "lineHeight": "1.15",
        "letterSpacing": "{global.letterSpacing.tighter}"
      },
      "type": "typography"
    },
    "titleLarge": {
      "value": {
        "fontFamily": "{global.fontFamily.display}",
        "fontWeight": "{global.fontWeight.semibold}",
        "fontSize": "{global.fontSize.36}",
        "lineHeight": "{global.lineHeight.snug}",
        "letterSpacing": "{global.letterSpacing.tight}"
      },
      "type": "typography"
    },
    "titleMedium": {
      "value": {
        "fontFamily": "{global.fontFamily.display}",
        "fontWeight": "{global.fontWeight.semibold}",
        "fontSize": "{global.fontSize.28}",
        "lineHeight": "{global.lineHeight.snug}",
        "letterSpacing": "-0.008em"
      },
      "type": "typography"
    },
    "titleSmall": {
      "value": {
        "fontFamily": "{global.fontFamily.display}",
        "fontWeight": "{global.fontWeight.semibold}",
        "fontSize": "{global.fontSize.22}",
        "lineHeight": "{global.lineHeight.normal}",
        "letterSpacing": "-0.005em"
      },
      "type": "typography"
    },
    "bodyLarge": {
      "value": {
        "fontFamily": "{global.fontFamily.body}",
        "fontWeight": "{global.fontWeight.regular}",
        "fontSize": "{global.fontSize.18}",
        "lineHeight": "{global.lineHeight.loose}",
        "letterSpacing": "{global.letterSpacing.none}"
      },
      "type": "typography"
    },
    "bodyMedium": {
      "value": {
        "fontFamily": "{global.fontFamily.body}",
        "fontWeight": "{global.fontWeight.regular}",
        "fontSize": "{global.fontSize.16}",
        "lineHeight": "{global.lineHeight.loose}",
        "letterSpacing": "{global.letterSpacing.none}"
      },
      "type": "typography"
    },
    "bodySmall": {
      "value": {
        "fontFamily": "{global.fontFamily.body}",
        "fontWeight": "{global.fontWeight.regular}",
        "fontSize": "{global.fontSize.14}",
        "lineHeight": "{global.lineHeight.relaxed}",
        "letterSpacing": "{global.letterSpacing.wide}"
      },
      "type": "typography"
    },
    "labelLarge": {
      "value": {
        "fontFamily": "{global.fontFamily.body}",
        "fontWeight": "{global.fontWeight.semibold}",
        "fontSize": "{global.fontSize.15}",
        "lineHeight": "{global.lineHeight.snug}",
        "letterSpacing": "{global.letterSpacing.wider}",
        "textCase": "uppercase"
      },
      "type": "typography"
    },
    "labelMedium": {
      "value": {
        "fontFamily": "{global.fontFamily.body}",
        "fontWeight": "{global.fontWeight.semibold}",
        "fontSize": "{global.fontSize.13}",
        "lineHeight": "{global.lineHeight.snug}",
        "letterSpacing": "{global.letterSpacing.wider}",
        "textCase": "uppercase"
      },
      "type": "typography"
    },
    "labelSmall": {
      "value": {
        "fontFamily": "{global.fontFamily.body}",
        "fontWeight": "{global.fontWeight.bold}",
        "fontSize": "{global.fontSize.11}",
        "lineHeight": "{global.lineHeight.snug}",
        "letterSpacing": "{global.letterSpacing.widest}",
        "textCase": "uppercase"
      },
      "type": "typography"
    },
    "caption": {
      "value": {
        "fontFamily": "{global.fontFamily.body}",
        "fontWeight": "{global.fontWeight.regular}",
        "fontSize": "{global.fontSize.12}",
        "lineHeight": "1.5",
        "letterSpacing": "{global.letterSpacing.wide}"
      },
      "type": "typography"
    }
  }
}
```

---

## Reference Output — Bold & Expressive Universal System (Syne + DM Sans)

This is a validated instance of this skill applied to a universal design system with bold/expressive aesthetic direction.

**Font Pairing**
- Display: **Syne** — geometric grotesque, architectural edge, strong contrast between weights. Best for hero headings, marketing statements, dashboard titles.
- Body: **DM Sans** — low-contrast geometric, generous x-height, wide apertures. Handles body, labels, captions equally well.
- Fallback: `'Syne', 'SF Pro Display', system-ui, sans-serif` / `'DM Sans', 'SF Pro Text', system-ui, sans-serif`

**Pairing rationale:** Syne and DM Sans share geometric construction but differ in personality weight — Syne commands hierarchy, DM Sans subordinates without competing.
