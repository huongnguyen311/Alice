# Short Memory — Rolling 5-Day Context

This file is Alice's **primary read target at the start of every session**. It captures the last ~5 days of conversation context, active work, and recent decisions. Alice should be able to understand the current situation from this file alone without reading long memory files.

Entries older than 5 days are pruned on each compact.

---

## 2026-03-25 (Today)

### Session Summary
- User confirmed Alice is fully set up and operational.
- Daily email recap upgraded: now runs via Windows Task Scheduler at 08:32 daily (persistent — no session needed).
- Google API auth set up: `credentials/google_token.json` generated. Gmail API enabled.
- `auto-scripts/daily_email_recap.py` created. Output: `data/outputs/email_recap_YYYYMMDD.txt`.
- `auto-scripts/gmail_mark_all_read.py` created. Ran once — marked 144 messages as read.

### Active Context
- **Daily email recap** is live and persistent — Windows Task Scheduler, 08:32 daily. No re-registration needed.
- **Short/Long memory split** — read `memories/short_memory.md` first always; long memory only when needed.
- **Internet search** capability confirmed. Use proactively when info is outdated or uncertain.
- **Dynamic routing system** live — `capabilities.md` is the master index for memories/skills/MCP. Always scan it to find what to read. Never load all files blindly. See `skills/route-request.md` for the full protocol.
- **MCP vs Python decision** — claude.ai MCPs (Gmail, Calendar, Canva) are remote/session-bound; Python scripts cannot connect to them. For batch/multi-step tasks, use Google API directly with `credentials/google_token.json`. See `skills/mcp-or-script.md`.

### Key Email Highlights (25 Mar 2026)
- **Olivia MVP** — contract signed, payment received, kick-off scheduled Apr 1 4–5pm.
- **ProMX / Michael Schlund** — NDA still pending after 3 follow-ups. May need escalation.
- **Opticor** — updated agreement sent to Evan Baldry, awaiting sign-off.
- **Photofolio domain** — Google OAuth broken after domain change, Thuan/Son resolving.

---

## 2026-03-24

### Session Summary
- Alice project initialized. Full folder structure created: `memories/`, `skills/`, `mcp/`, `auto-scripts/`, `data/`.
- Three running modes defined. FastAPI chosen for automation layer.
- `README.md` created as project overview. `PROJECT_RECAP.md` retired.
- Setup guides created: `setup/SETUP-WINDOWS.md` and `setup/SETUP-MAC.md` (fully self-contained).
- User confirmed assistant name is Alice. Profile updated to first-person.
- "compact now" confirmed as memory compact trigger.

---

*Last updated: 2026-03-25*
*Updated by: Alice*
