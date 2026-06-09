---
name: design-tokens
description: Use when asked to generate, create, or produce design tokens for a project via Alice — especially when output must be Token Studio / Figma Tokens compatible. Triggers on "generate design tokens", "create token set", "design system tokens", "Token Studio JSON".
scope: design
triggers:
  - "generate design tokens"
  - "create design tokens"
  - "design system tokens"
  - "token studio"
  - "figma tokens"
  - "create token set"
  - "design tokens for"
---

# Design Tokens Generator

## Overview

You are a design systems engineer. Generate design tokens that are complete, semantically named, and ready to import into Token Studio (Figma Tokens plugin).

**Core principle:** Never use raw values in semantic or component tokens — always reference global tokens. Never name tokens after visual appearance.

## 4-Layer Structure

Always output tokens in exactly this structure:

| Layer | Purpose | References |
|---|---|---|
| `global` | Primitive values (raw colors, numbers) — never used directly in components | — |
| `light` | Semantic tokens for light mode | → global |
| `dark` | Semantic tokens for dark mode | → global |
| `component` | Component-specific tokens (only what differs from semantic defaults) | → light/dark |

## Output Format

Valid JSON compatible with Token Studio. Each token follows this shape:

```json
{
  "token-name": {
    "value": "{global.color.blue.500}",
    "type": "color",
    "$description": "Optional — only when purpose is not obvious"
  }
}
```

## Token Naming Rules

- **kebab-case** always
- **Name by ROLE, never by value:**
  - ✅ `color-action-primary` — ❌ `blue-500`
  - ✅ `color-feedback-error` — ❌ `red`
  - ✅ `color-text-secondary` — ❌ `gray-600`
- **Structure:** `{category}.{role}.{variant}` e.g. `color.text.secondary`, `spacing.component.button-padding-x`

## Required Token Categories

### color
Subcategories: `bg`, `text`, `border`, `action`, `feedback`

```json
// global layer — raw values allowed here only
"global": {
  "color": {
    "blue": {
      "500": { "value": "#3B82F6", "type": "color" },
      "600": { "value": "#2563EB", "type": "color" }
    },
    "neutral": {
      "0":   { "value": "#FFFFFF", "type": "color" },
      "50":  { "value": "#F9FAFB", "type": "color" },
      "100": { "value": "#F3F4F6", "type": "color" },
      "200": { "value": "#E5E7EB", "type": "color" },
      "700": { "value": "#374151", "type": "color" },
      "900": { "value": "#111827", "type": "color" }
    },
    "red": {
      "500": { "value": "#EF4444", "type": "color" }
    },
    "green": {
      "500": { "value": "#22C55E", "type": "color" }
    }
  }
}

// light layer — reference only, no hex values
"light": {
  "color": {
    "bg": {
      "surface":   { "value": "{global.color.neutral.0}",   "type": "color" },
      "subtle":    { "value": "{global.color.neutral.50}",  "type": "color" },
      "overlay":   { "value": "{global.color.neutral.100}", "type": "color" }
    },
    "text": {
      "primary":   { "value": "{global.color.neutral.900}", "type": "color" },
      "secondary": { "value": "{global.color.neutral.700}", "type": "color" },
      "disabled":  { "value": "{global.color.neutral.200}", "type": "color" }
    },
    "border": {
      "default":   { "value": "{global.color.neutral.200}", "type": "color" },
      "strong":    { "value": "{global.color.neutral.700}", "type": "color" }
    },
    "action": {
      "primary":          { "value": "{global.color.blue.500}", "type": "color" },
      "primary-hover":    { "value": "{global.color.blue.600}", "type": "color" }
    },
    "feedback": {
      "error":   { "value": "{global.color.red.500}",   "type": "color" },
      "success": { "value": "{global.color.green.500}", "type": "color" }
    }
  }
}
```

### spacing (4pt base grid)

```json
"global": {
  "spacing": {
    "1": { "value": "4px",  "type": "spacing" },
    "2": { "value": "8px",  "type": "spacing" },
    "3": { "value": "12px", "type": "spacing" },
    "4": { "value": "16px", "type": "spacing" },
    "5": { "value": "20px", "type": "spacing" },
    "6": { "value": "24px", "type": "spacing" },
    "8": { "value": "32px", "type": "spacing" },
    "10":{ "value": "40px", "type": "spacing" },
    "12":{ "value": "48px", "type": "spacing" },
    "16":{ "value": "64px", "type": "spacing" }
  }
}
```

### typography

```json
// fontSize
"font-size": {
  "xs":  { "value": "12px", "type": "fontSizes" },
  "sm":  { "value": "14px", "type": "fontSizes" },
  "md":  { "value": "16px", "type": "fontSizes" },
  "lg":  { "value": "18px", "type": "fontSizes" },
  "xl":  { "value": "20px", "type": "fontSizes" },
  "2xl": { "value": "24px", "type": "fontSizes" },
  "3xl": { "value": "30px", "type": "fontSizes" }
}

// fontWeight
"font-weight": {
  "regular":  { "value": "400", "type": "fontWeights" },
  "medium":   { "value": "500", "type": "fontWeights" },
  "semibold": { "value": "600", "type": "fontWeights" },
  "bold":     { "value": "700", "type": "fontWeights" }
}

// lineHeight
"line-height": {
  "tight":   { "value": "1.25", "type": "lineHeights" },
  "snug":    { "value": "1.375", "type": "lineHeights" },
  "normal":  { "value": "1.5",  "type": "lineHeights" },
  "relaxed": { "value": "1.625", "type": "lineHeights" }
}

// letterSpacing
"letter-spacing": {
  "tight":  { "value": "-0.025em", "type": "letterSpacing" },
  "normal": { "value": "0em",      "type": "letterSpacing" },
  "wide":   { "value": "0.025em",  "type": "letterSpacing" }
}
```

### shape

```json
// borderRadius
"border-radius": {
  "xs":   { "value": "2px",   "type": "borderRadius" },
  "sm":   { "value": "4px",   "type": "borderRadius" },
  "md":   { "value": "8px",   "type": "borderRadius" },
  "lg":   { "value": "12px",  "type": "borderRadius" },
  "xl":   { "value": "16px",  "type": "borderRadius" },
  "full": { "value": "9999px","type": "borderRadius" }
}

// borderWidth
"border-width": {
  "thin":  { "value": "1px", "type": "borderWidth" },
  "base":  { "value": "2px", "type": "borderWidth" },
  "thick": { "value": "4px", "type": "borderWidth" }
}
```

### motion & opacity

```json
// duration
"duration": {
  "fast":   { "value": "120ms", "type": "other", "$description": "Micro-interactions and hover states" },
  "normal": { "value": "200ms", "type": "other", "$description": "Standard transitions" },
  "slow":   { "value": "350ms", "type": "other", "$description": "Complex or large-area transitions" }
}

// opacity
"opacity": {
  "disabled": { "value": "0.38", "type": "opacity", "$description": "Disabled UI elements" },
  "overlay":  { "value": "0.6",  "type": "opacity", "$description": "Modal backdrops and overlays" },
  "subtle":   { "value": "0.08", "type": "opacity", "$description": "Hover/focus background tints" }
}
```

## Component Token Rules

- Only include tokens that **differ** from semantic defaults
- Always reference semantic layer, not global
- Name by component + role: `component.button.bg-primary`, `component.input.border-focus`

```json
"component": {
  "button": {
    "bg-primary":       { "value": "{light.color.action.primary}",       "type": "color" },
    "bg-primary-hover": { "value": "{light.color.action.primary-hover}",  "type": "color" },
    "text-on-primary":  { "value": "{global.color.neutral.0}",            "type": "color" },
    "padding-x":        { "value": "{global.spacing.4}",                  "type": "spacing" },
    "padding-y":        { "value": "{global.spacing.2}",                  "type": "spacing" },
    "radius":           { "value": "{global.border-radius.md}",           "type": "borderRadius" }
  },
  "input": {
    "border-default": { "value": "{light.color.border.default}", "type": "color" },
    "border-focus":   { "value": "{light.color.action.primary}", "type": "color" },
    "bg":             { "value": "{light.color.bg.surface}",     "type": "color" },
    "padding-x":      { "value": "{global.spacing.3}",           "type": "spacing" },
    "padding-y":      { "value": "{global.spacing.2}",           "type": "spacing" }
  }
}
```

## Token Studio Import Tips

- Each layer (`global`, `light`, `dark`, `component`) becomes a **separate token set** in Token Studio
- Set `light` and `dark` as theme sets; `global` and `component` as always-active sets
- Use `$themes.json` to define which semantic set is active per theme

## Common Mistakes

| Mistake | Fix |
|---|---|
| Hex value in `light`/`dark` layer | Replace with `{global.color.*}` reference |
| Token named `red-error` or `primary-blue` | Rename to `color.feedback.error` / `color.action.primary` |
| Dark mode token not provided | Always generate both `light` and `dark` semantic sets |
| Component token references global directly | Route through semantic layer (`{light.color.*}`, not `{global.color.*}`) |
| Missing `$description` on ambiguous tokens | Add `$description` to `opacity.*`, `duration.*`, and any non-obvious role tokens |
| Spacing token named `spacing-16px` | Rename to scale-based: `spacing.4` (= 16px on 4pt grid) |
