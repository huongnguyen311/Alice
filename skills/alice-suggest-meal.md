---
name: alice-suggest-meal
description: Suggest what to eat for a meal via Alice — Vietnamese-focused, personalised to user preferences, time of day, weather, and recent meals.
scope: personal
triggers:
  - "what should I eat"
  - "suggest food"
  - "what to eat"
  - "food suggestion"
  - "suggest a meal"
  - "gợi ý món ăn"
  - "ăn gì hôm nay"
  - "ăn gì"
  - "đề xuất bữa ăn"
  - "hôm nay ăn gì"
---

# Skill: Suggest What to Eat

## Overview

Alice suggests Vietnamese meals personalised to the user's context: time of day, mood, weather, recent meals, dietary restrictions, and budget.

---

## Step 1 — Gather context

Collect the following before suggesting. If the user's message already includes some, skip those questions. Ask all missing in one message — never one at a time.

| Context | Ask if missing |
|---|---|
| Time of day | Infer from current time — confirm if ambiguous (e.g. "late morning") |
| Mood / craving | "Feeling like something light, hearty, or comfort food?" |
| Who's eating | "Just you, or a group?" |
| Weather | Infer from season/location if known; otherwise ask "Hot or cold today?" |
| Budget | "Street food range or restaurant?" |
| Anything avoided today | "Anything you've already had today or don't feel like?" |

If the user just says "ăn gì hôm nay" or "what should I eat" with no other context — infer time from the system clock and skip straight to Step 2 with reasonable defaults.

---

## Step 2 — Apply personal preferences

Always factor in:
- `{DISLIKED_INGREDIENTS}` — never suggest dishes containing these
- `{DIETARY_RESTRICTIONS}` — hard filter (e.g. no pork, vegetarian)
- `{FAVORITE_DISHES}` — weight these higher but avoid repeating from recent log
- Recent meals from `data/meal_log.csv` — avoid the same dish within 2 days

---

## Step 3 — Suggest by time of day

### Sáng (Breakfast — before 10:00)
Prioritise lighter, broth-based, or quick options:
- Phở bò / phở gà
- Bún bò Huế
- Bánh mì
- Xôi (xôi xéo, xôi lạp xưởng)
- Cháo (trắng, lòng, gà)
- Bún riêu

### Trưa (Lunch — 11:00–13:30)
Balanced, filling options:
- Cơm tấm sườn bì chả
- Bún thịt nướng
- Cơm bình dân (nhiều món)
- Mì Quảng
- Bánh xèo (nếu ăn nhóm)
- Gỏi cuốn + bún thịt nướng

### Chiều (Snack — 14:00–17:00)
Lighter snacks or drinks:
- Bánh mì thịt / trứng
- Gỏi cuốn
- Chè (chè đậu đỏ, chè khúc bạch)
- Bắp xào / bánh tráng trộn

### Tối (Dinner — 18:00–21:00)
More varied; group-friendly options included:
- Lẩu (thái, hải sản, bò) — if group or cold weather
- Nướng (BBQ, hải sản nướng)
- Cơm niêu
- Bún bò Huế
- Hủ tiếu Nam Vang
- Cháo (comfort / rainy weather)

---

## Step 4 — Format the suggestion

Suggest **2–3 options** plus 1 wildcard. Format:

```
🍜 **[Dish name]** — [One-line reason it fits right now]
🍚 **[Dish name]** — [One-line reason]
🌿 **[Dish name]** — [One-line reason]

🎲 Wildcard: **[Dish name]** — something a bit different if you want a change.
```

Keep it short. No lengthy descriptions — the user just wants to decide.

---

## Step 5 — Offer to log the meal

After the user picks (or at end of conversation), ask:

> "Want me to log what you ate to keep track for next time?"

If yes → append a row to `data/meal_log.csv`:

| Column | Value |
|---|---|
| `date` | Today's date (YYYY-MM-DD) |
| `meal` | breakfast / lunch / snack / dinner |
| `dish` | Dish name |
| `rating` | Ask: "Rate it 1–5?" (optional) |
| `notes` | Any notes (optional) |

---

## Personal Config Tokens

| Token | Description |
|---|---|
| `{DISLIKED_INGREDIENTS}` | Ingredients to always exclude from suggestions |
| `{DIETARY_RESTRICTIONS}` | Hard dietary rules (e.g. "no pork", "vegetarian") |
| `{FAVORITE_DISHES}` | Dishes to prioritise |
| `{LOCATION}` | City/district — used to tailor street food vs. restaurant context |

---

## Notes

- Default cuisine focus: **Vietnamese**. If user asks for non-Vietnamese, suggest and ask if they want that added as a preference.
- No external APIs needed — this is purely a reasoning + logging skill.
- Meal log lives at `data/meal_log.csv` — create it if it doesn't exist (headers: `date,meal,dish,rating,notes`).
