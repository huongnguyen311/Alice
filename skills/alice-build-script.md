---
name: alice-build-script
description: Write and register a new Python automation script in Alice's auto-scripts directory. Use when adding automation to Alice.
scope: automation
triggers:
  - "write a script"
  - "build a script"
  - "create a script"
  - "make a script"
  - "automate"
  - "automation"
  - "python script"
---

# Skill: Build Script (Global Wrapper)

This skill delegates to Alice's full implementation.

Read and follow: `{ALICE_ROOT}/skills/build-script.md`

**Context for delegated skill:**
- Alice root is `{ALICE_ROOT}`
- Scripts are saved to: `{ALICE_ROOT}/auto-scripts/`
- Data input/output directory: `{ALICE_ROOT}/data/`
- Logs go to: `{ALICE_ROOT}/data/logs.csv`
- Treat all relative paths in the delegated skill as relative to `{ALICE_ROOT}`
