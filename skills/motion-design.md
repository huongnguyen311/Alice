---
name: motion-design
description: Use when defining animation specs for UI components or transitions in Alice — entrance/exit animations, interactive feedback, screen transitions, modals, drawers, toasts, or any element that moves in a digital interface
scope: meta
triggers:
  - "animation spec"
  - "motion spec"
  - "animate a component"
  - "easing"
  - "entrance animation"
  - "exit animation"
  - "transition duration"
  - "reduced motion"
  - "motion design"
---

# Motion Design

## Overview

UI animations must be purposeful, performant, and always have a reduced-motion fallback. Every spec includes: why the animation exists, precise values with token names, keyframe states, platform notes, and a reduced-motion alternative.

## Duration Rules

| Category | Duration | Examples |
|----------|----------|---------|
| Interactive feedback | ≤ 120ms | Tap, press, toggle |
| Simple transitions | 200–300ms | Tooltip, dropdown, fade |
| Complex transitions | 350–500ms | Sheet, modal, page |

**NEVER use linear easing.** Always use a named curve.

## Easing Tokens

| Token | Curve | When |
|-------|-------|------|
| `easing.decelerate` | `cubic-bezier(0.0, 0.0, 0.2, 1)` | Entrance (starts fast, settles) |
| `easing.accelerate` | `cubic-bezier(0.4, 0.0, 1, 1)` | Exit (starts slow, leaves fast) |
| `easing.standard` | `cubic-bezier(0.4, 0.0, 0.2, 1)` | Elements moving within screen |
| `easing.spring` | platform spring params | Interactive drag/snap-back (iOS/Android) |

## Required Output Format

### Animation Purpose
- **Category:** feedback / navigation / delight / orientation
- **Message:** what it communicates to the user (one sentence)

### Specification Table

| Property | Value | Token |
|----------|-------|-------|
| Duration | Xms | `duration.fast` (120ms) / `duration.normal` (250ms) / `duration.complex` (400ms) |
| Easing | `cubic-bezier(...)` | `easing.decelerate` / `easing.accelerate` / `easing.standard` |
| Delay | 0ms (default) | — |
| Properties animated | list each | — |

**NEVER animate more than 2–3 properties simultaneously.**
Preferred pairs: `opacity + transform`, `transform` only, `opacity` only.

### Keyframes

```
[property]: [start value] → [end value]
```

List every animated property. Be explicit — no "fades in" without opacity values.

### Platform Notes

**iOS:** Prefer `UISpringTimingParameters` for interactive elements (drag, swipe). Use `useNativeDriver: true` in React Native — only `transform` and `opacity` are supported. Never animate `height` or `width` on native driver.

**Android:** Follow Material Motion patterns — shared axis (same-hierarchy nav), container transform (persistent element), fade through (unrelated destinations). Honor predictive back gesture (Android 13+): begin exit animation immediately on back gesture initiation.

**Web:**
- **CSS `transition`:** For state changes triggered by class/property — preferred for simple hover, focus, show/hide.
- **CSS `@keyframes` / `animation`:** For looping, multi-step, or choreographed sequences.
- **Web Animations API (`element.animate()`):** For JS-controlled, dynamic, or interruptible animations. Preferred when animation must be cancelled or reversed mid-play.
- Always add `will-change: transform` or `will-change: opacity` to promote composited layers — never `will-change: height`.

### Reduced Motion

Always define. Check via:
- **Web:** `@media (prefers-reduced-motion: reduce)` / `window.matchMedia('(prefers-reduced-motion: reduce)')`
- **iOS / React Native:** `AccessibilityInfo.isReduceMotionEnabled()`
- **Android:** `Settings.Global.TRANSITION_ANIMATION_SCALE`

**Default fallback:** instant opacity switch (`opacity: 0 → 1`, duration 0ms). If state change needs acknowledgement, allow a simple 80ms fade — no transform, no movement.

---

## Entrance vs Exit Rule

```
Entrance → easing.decelerate  (element arrives, decelerates to rest)
Exit     → easing.accelerate  (element departs, accelerates away)
Within screen → easing.standard
```

## Common Mistakes

| Mistake | Fix |
|---------|-----|
| Linear easing on any UI element | Use `easing.standard` minimum |
| Entrance and exit same duration | Exit should be 20–30% shorter — it should "get out of the way" |
| Animating `height` on mobile native | Animate `scaleY` + `translateY` instead |
| No reduced-motion alternative | Always define — skip transform, keep fade or instant |
| Animating 4+ properties at once | Max 2–3; prioritize `transform` + `opacity` |
| Same easing for enter and exit | Entrance = decelerate, exit = accelerate |

---

## Example: Bottom Sheet (Enter / Exit)

**Animation Purpose**
- Category: navigation / orientation
- Message: "Content is arriving from below; dismiss it the same way."

**Enter Specification**

| Property | Value | Token |
|----------|-------|-------|
| Duration | 400ms | `duration.complex` |
| Easing | `cubic-bezier(0.0, 0.0, 0.2, 1)` | `easing.decelerate` |
| Delay | 0ms | — |
| Properties | `translateY`, `opacity` (scrim) | — |

**Enter Keyframes**
```
translateY: 100% → 0%
scrim opacity: 0 → 0.5
```

**Exit Specification**

| Property | Value | Token |
|----------|-------|-------|
| Duration | 280ms | — |
| Easing | `cubic-bezier(0.4, 0.0, 1, 1)` | `easing.accelerate` |
| Properties | `translateY`, `opacity` (scrim) | — |

**Exit Keyframes**
```
translateY: 0% → 100%
scrim opacity: 0.5 → 0
```

**Reduced Motion:** Instant show/hide via `opacity: 0 ↔ 1` at 0ms. No translate.
