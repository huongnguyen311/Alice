---
name: alice-run-automation
description: Run or schedule an existing script in Alice's auto-scripts directory. Use when triggering or scheduling Alice automations.
scope: automation
triggers:
  - "run"
  - "schedule"
  - "cron"
  - "trigger"
  - "execute script"
  - "set up recurring"
  - "every day"
  - "every week"
  - "automatically"
  - "recurring"
---

# Skill: Run Automation (Global Wrapper)

This skill delegates to Alice's full implementation.

Read and follow: `{ALICE_ROOT}/skills/run-automation.md`

**Context for delegated skill:**
- Alice root is `{ALICE_ROOT}`
- Scripts are located at: `{ALICE_ROOT}/auto-scripts/`
- FastAPI server runs at: `http://localhost:8000`
- Treat all relative paths in the delegated skill as relative to `{ALICE_ROOT}`
