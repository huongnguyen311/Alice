---
name: responsive-layout
description: Use when defining a responsive grid system, layout rules, spacing tokens, or Auto Layout specs for a digital product — especially when given a platform (web, iOS, Android) and target screen sizes.
---

# Responsive Layout

## Overview

You are a layout specialist for digital products. Define a complete, token-referenced responsive grid system and layout rules for any given platform and screen configuration.

**Core principle:** All values MUST reference design tokens — never hardcode numbers. Always cover both portrait and landscape for mobile. Flag any pattern that breaks on 320pt-wide screens.

---

## Output Structure

When given a platform and screen sizes, produce all five sections below in order.

---

## 1. Grid System

For each breakpoint:

| Breakpoint | Width | Columns | Margin | Gutter |
|------------|-------|---------|--------|--------|
| xs (mobile) | `size.screen.xs` | `grid.cols.xs` | `space.margin.xs` | `space.gutter.xs` |
| sm (mobile-lg / phablet) | `size.screen.sm` | `grid.cols.sm` | `space.margin.sm` | `space.gutter.sm` |
| md (tablet) | `size.screen.md` | `grid.cols.md` | `space.margin.md` | `space.gutter.md` |
| lg (desktop) | `size.screen.lg` | `grid.cols.lg` | `space.margin.lg` | `space.gutter.lg` |
| xl (wide) | `size.screen.xl` | `grid.cols.xl` | `space.margin.xl` | `space.gutter.xl` |

**Typical reference values** (replace with project tokens):

| Breakpoint | Width | Columns | Margin | Gutter |
|------------|-------|---------|--------|--------|
| xs | 320–375pt | 4 | `space.4` (16pt) | `space.4` (16pt) |
| sm | 376–428pt | 4 | `space.4` (16pt) | `space.4` (16pt) |
| md | 768–1024pt | 8 | `space.6` (24pt) | `space.6` (24pt) |
| lg | 1024–1440pt | 12 | `space.8` (32pt) | `space.6` (24pt) |
| xl | 1440pt+ | 12 | `space.10` (40pt) | `space.8` (32pt) |

---

## 2. Mobile (iOS/Android)

### Safe Area Insets
| Edge | Token |
|------|-------|
| Top | `safe.inset.top` (Dynamic Island / notch — varies per device) |
| Bottom | `safe.inset.bottom` (Home indicator: ~34pt iPhone, ~0pt Android w/ gesture bar) |
| Left | `safe.inset.left` (0pt portrait; `safe.inset.side` landscape) |
| Right | `safe.inset.right` (0pt portrait; `safe.inset.side` landscape) |

### Standard Component Heights
| Component | Token |
|-----------|-------|
| Status bar | `height.status-bar` (~54pt iOS, ~24dp Android) |
| Navigation bar | `height.nav-bar` (~44pt iOS, ~56dp Android) |
| Tab bar | `height.tab-bar` (~49pt iOS, ~56dp Android) |
| Search bar | `height.search-bar` (`space.11`, ~44pt) |
| List row (standard) | `height.list-row.md` (`space.12`, ~48pt) |

### Thumb-Reach Zones (right-hand, portrait)
| Zone | Region | Guidance |
|------|--------|----------|
| Comfortable | Bottom 40% of screen | Primary actions, tab bar |
| Stretch | Middle 40% | Secondary actions |
| Hard to reach | Top 20% | Destructive or rare actions only |

> **Landscape note:** Thumb zones compress horizontally. Move primary actions to bottom corners or a floating action button. Avoid center-screen CTAs in landscape.

### Content Width Rules
- **Portrait:** `100vw - (2 × space.margin.xs)`
- **Landscape (mobile):** `100vw - (2 × safe.inset.side) - (2 × space.margin.xs)`
- **Max content width:** `size.content.max` (e.g., 720pt) — center on larger breakpoints

---

## 3. Layout Patterns

| Pattern | When to Use | Breakpoints | 320pt Risk |
|---------|-------------|-------------|------------|
| **Single Column** | Forms, article readers, onboarding | xs, sm | Safe |
| **Card Grid** | Content feeds, product listings | xs (1-col) → md (2-col) → lg (3-col) | Safe if 1-col on xs |
| **Split View** | Settings with detail pane, email clients | md+ only | ⚠️ Collapse to single-column below md |
| **Master-Detail** | Navigation-heavy apps (files, contacts) | md+ only | ⚠️ Stack vertically below md |
| **Sticky Header + Scroll** | Long-form content, data tables | All | Safe |
| **Bottom Sheet** | Contextual actions, filters, pickers | xs, sm | Safe |
| **Side Drawer** | Global navigation | xs, sm (hidden by default) | ⚠️ Overlay must not occlude content |
| **Tab Bar** | Top-level navigation (≤5 items) | xs, sm | Safe — but label text may clip below 375pt |
| **Floating Action Button (FAB)** | Single primary action | xs, sm | Safe — pin to `safe.inset.bottom + space.4` |

---

## 4. Spacing Rules

All values reference spacing tokens (base-8 scale recommended):

| Token | Value | Usage |
|-------|-------|-------|
| `space.2` | 8pt | Icon-to-label gap, tight inline spacing |
| `space.3` | 12pt | Compact component padding |
| `space.4` | 16pt | Default component padding, edge margin (mobile) |
| `space.6` | 24pt | Section spacing (mobile), component spacing (desktop) |
| `space.8` | 32pt | Section spacing (tablet/desktop) |
| `space.10` | 40pt | Major section spacing (desktop) |
| `space.12` | 48pt | Hero/page-level section breaks |

### Rule Summary
| Spacing Type | Mobile Token | Desktop Token |
|--------------|-------------|---------------|
| Section spacing | `space.8` | `space.12` |
| Component spacing | `space.4` | `space.6` |
| Edge margin | `space.4` | `space.8` |
| Element gap (within component) | `space.2` | `space.3` |

---

## 5. Auto Layout Spec (Figma)

For each layout pattern, implement in Figma Auto Layout as follows:

### Single Column
| Property | Value |
|----------|-------|
| Direction | Vertical |
| Alignment | Top · Center |
| Gap | `space.6` |
| Padding (H) | `space.margin.xs` |
| Padding (V) | `space.6` |
| Width resizing | Fill container |
| Height resizing | Hug contents |

### Card Grid (responsive)
| Property | Value |
|----------|-------|
| Direction | Horizontal, wrap |
| Alignment | Top · Left |
| Gap | `space.4` |
| Padding | `space.margin.xs` |
| Card width | Fill (xs: 100%) / Fixed (md+: `grid.col.span-4`) |
| Height resizing | Hug contents |

### Split View (md+)
| Property | Value |
|----------|-------|
| Direction | Horizontal |
| Alignment | Top · Left |
| Gap | `space.gutter.md` |
| Left pane width | Fixed (`size.split.master`, e.g., 320pt) |
| Right pane width | Fill container |
| Height resizing | Fill container |

### Master-Detail (md+)
| Property | Value |
|----------|-------|
| Direction | Horizontal |
| Alignment | Top · Left |
| Gap | `0` (use border instead) |
| Master width | Fixed (`size.master.md`, e.g., 280pt) |
| Detail width | Fill container |
| Height resizing | Fill container |

### Bottom Sheet
| Property | Value |
|----------|-------|
| Direction | Vertical |
| Alignment | Top · Center |
| Gap | `space.4` |
| Padding (H) | `space.4` |
| Padding (top) | `space.6` |
| Padding (bottom) | `safe.inset.bottom + space.4` |
| Width resizing | Fill container |
| Height resizing | Hug contents |

### Sticky Header + Scroll (page frame)
| Property | Value |
|----------|-------|
| Header direction | Horizontal |
| Header alignment | Center · Left |
| Header height | Fixed (`height.nav-bar`) |
| Header padding (H) | `space.4` |
| Scroll area direction | Vertical |
| Scroll area width | Fill |
| Scroll area height | Fill |

---

## Common Mistakes

| Mistake | Fix |
|---------|-----|
| Hardcoding `16px` margin | Use `space.margin.xs` token |
| Forgetting landscape safe areas | Always add `safe.inset.side` in landscape margin calc |
| Split view on small screens | Collapse to single-column below `md` breakpoint |
| Tab labels clipping at 320pt | Limit to icon-only below `sm`, or shorten labels |
| FAB overlapping tab bar | Pin FAB above tab bar: `safe.inset.bottom + height.tab-bar + space.4` |
| Bottom sheet ignoring home indicator | Add `safe.inset.bottom` to bottom padding |

---

## 320pt Breakpoint Checklist

Before finalizing any layout pattern, verify at 320pt width:
- [ ] No horizontal overflow
- [ ] Single-column fallback active for grid/split/master-detail
- [ ] Tab bar labels do not clip (use icon-only mode if needed)
- [ ] FAB does not overlap critical content
- [ ] Modal/sheet does not exceed screen height
- [ ] Edge margins still apply (content not flush to screen edge)
