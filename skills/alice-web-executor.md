---
name: alice-web-executor
description: Run automated web tests via Alice — executes test cases from a TC Markdown file against a website URL using Playwright and returns a result report.
scope: automation
triggers:
  - "run tests on"
  - "execute test cases"
  - "web automation"
  - "run web executor"
  - "test website"
  - "execute TCs on"
  - "web test"
  - "run automated tests"
---

# Skill: Web Automation Executor (Global Wrapper)

Run Playwright-based web automation tests from Alice's TC Markdown files.

Read and follow: `{ALICE_ROOT}/skills/web-executor-internal.md`

**Context for delegated skill:**
- Alice root is `{ALICE_ROOT}`
- Script: `{ALICE_ROOT}/auto-scripts/web_executor.py`
- TC files: `{ALICE_ROOT}/docs/tcs/`
- Reports written to: same directory as TC file, `<slug>-results-YYYY-MM-DD.md`
- Screenshots: `{ALICE_ROOT}/data/screenshots/<tc-id>/`
- Venv: `{ALICE_ROOT}/.venv/`
