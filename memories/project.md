---
type: project
description: Ongoing decisions, active work, open questions, and key milestones for Alice and user projects
---

# Project Memory

## Current Status

Alice is fully operational as of 2026-03-25. No active build tasks in flight.

---

## Key Decisions

| Date | Decision | Why | Status |
|---|---|---|---|
| 2026-03-24 | Python + FastAPI for automations | No third-party platforms (Make, N8N, Zapier) | Confirmed |
| 2026-03-24 | Three running modes (Inactive / MCP-triggered / Scheduled) | Covers all automation patterns | Confirmed |
| 2026-03-24 | Markdown-first storage, CSV for structured data | Local-only, no database | Confirmed |
| 2026-03-24 | FastAPI on `localhost:8000` | Standard local automation layer | Confirmed |
| 2026-03-25 | Dynamic routing via `capabilities.md` | Avoid reading all files blindly on every request | Confirmed |
| 2026-03-25 | MCP vs Python script split | claude.ai MCPs are remote/session-bound; Python uses Google API directly with `credentials/google_token.json` | Confirmed |
| 2026-03-25 | Two-tier memory (short + long) | Short memory gives full recent context; long memory only when needed | Confirmed |
| 2026-03-25 | Adopt typed memory + MEMORY.md + implicit skill invocation + scoped skills from Claude Code agent architecture | Aligns Alice with best practices; reduces blind file loading | Confirmed |

---

## Active Tasks

- None.

---

## Open / Pending

- **Canva API key** — Store in `credentials/canva_api_key.txt` for Python batch Canva scripts. Identified but not yet set up.
- **Auto-memory without compact trigger** — Alice now writes memories immediately on trigger (not just on compact). Living context updated accordingly.
- **Vector database / semantic search** — Planned future enhancement for memory search. Not started.

---

## Active Projects (User-side)

| Project | Status | Notes |
|---|---|---|
| **Olivia MVP** | Active — kick-off Apr 1 4–5pm | Contract signed, payment received (as of 2026-03-25 email recap) |
| **ProMX / Michael Schlund NDA** | Blocked | NDA pending after 3 follow-ups — may need escalation |
| **Opticor** | Awaiting sign-off | Updated agreement sent to Evan Baldry |
| **Photofolio domain** | In progress | Google OAuth broken after domain change — Thuan/Son resolving |

---
*Last updated: 2026-03-25*
*Updated by: Alice*
