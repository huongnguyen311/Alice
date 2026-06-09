# Design Spec: Web Automation Executor

> Source: User brief (web automation skill for Alice)
> Author: Alice (AI)
> Date: 2026-04-22
> Status: Approved

---

## Overview

A skill and Python script that accepts a TC Markdown file (produced by `alice-test-design-engine`) and a website URL, converts test steps to structured JSON actions via Claude API, executes them in a Playwright browser, and writes a separate result report file.

**Two deliverables:**
1. `skills/alice-web-executor.md` — Alice skill (global, installable)
2. `auto-scripts/web_executor.py` — Python execution script

---

## Architecture

### End-to-End Flow

```
User: "run tests on https://app.example.com using docs/tcs/login-tcs.md"
  ↓
Alice skill (alice-web-executor.md)
  → validates inputs (file exists, URL valid)
  → calls run_automation: web_executor.py --tc-file <path> --url <url> [--stop-on-fail]
  ↓
web_executor.py:
  1. TC Parser         — parse Markdown TC file → extract TC rows
  2. Step Interpreter  — call Claude API → convert steps to JSON actions
  3. Action Executor   — Playwright executes JSON actions on browser
  4. Result Collector  — capture pass/fail/skip + screenshots on FAIL
  5. Report Writer     — write docs/tcs/<slug>-results-YYYY-MM-DD.md
  ↓
Alice reads report → confirms file path to user → logs to data/logs.csv
```

---

## Script Internals (`auto-scripts/web_executor.py`)

### CLI Interface

```
python web_executor.py \
  --tc-file docs/tcs/login-tcs.md \
  --url https://app.example.com \
  [--stop-on-fail]
```

### Component 1 — TC Parser

- Reads the Markdown TC file
- Extracts per TC: ID, Name, Steps (numbered list), Expected Result, Test Data
- Skips: header rows, coverage matrix, non-TC sections
- Output: list of TC dicts

### Component 2 — Step Interpreter (Claude API)

- For each TC, batches all steps into one Claude API call
- System prompt: QA automation step interpreter (as defined in brief)
- Per step output schema:
```json
{
  "action": "",
  "target": "",
  "value": "",
  "url": "",
  "assertion": {
    "type": "",
    "expected": ""
  },
  "confidence": 0.0
}
```
- Action types: `navigate`, `click`, `fill`, `select`, `verify`, `wait`
- If Claude API call fails: mark all steps in that TC as ERROR, continue to next TC

### Component 3 — Action Executor (Playwright)

Action-to-Playwright mapping:

| Action | Playwright call |
|---|---|
| `navigate` | `page.goto(url)` |
| `click` | `page.click(target)` |
| `fill` | `page.fill(target, value)` |
| `select` | `page.select_option(target, value)` |
| `verify` | `expect(page).to_have_url()` / `page.locator().is_visible()` / etc. |
| `wait` | `page.wait_for_selector(target)` |

- Default step timeout: 10 seconds
- Browser: headless Chromium

### Component 4 — Result Collector

Per step records:
- Status: `PASS` / `FAIL` / `SKIP` / `ERROR` / `WARN`
- Actual result (what the browser returned)
- Error message (on FAIL/ERROR)
- Screenshot path (on FAIL — saved to `data/screenshots/<slug>/<tc-id>-step-<n>.png`)

`--stop-on-fail` behaviour:
- **Not set (default):** mark step FAIL, continue all remaining steps and TCs
- **Set:** mark step FAIL, mark remaining steps in current TC as SKIP, continue to next TC

Low confidence handling (`confidence < 0.6`): attempt the step, mark as WARN in report.

### Component 5 — Report Writer

Output file: `docs/tcs/<slug>-results-YYYY-MM-DD.md`

Report structure:
1. **Summary table** — TC ID, Name, Status, Duration, Pass/Fail count
2. **Overall stats** — Total TCs / Passed / Failed / Skipped / Errors
3. **Per-TC detail** — step-by-step status, error messages, screenshot links
4. **Run metadata** — URL tested, TC file used, run timestamp, `--stop-on-fail` setting

Report is always written — even if all TCs fail.

---

## Skill File (`skills/alice-web-executor.md`)

### Frontmatter

```yaml
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
```

### Skill Behaviour

1. Extract TC file path and URL from user message
2. Validate TC file exists; if not, report error and stop
3. Validate URL format; if invalid, report error and stop
4. Check for `--stop-on-fail` intent in user message
5. Call `run_automation`: `web_executor.py --tc-file <path> --url <url> [--stop-on-fail]`
6. Read output report path from script stdout
7. Confirm report path to user
8. Log run to `data/logs.csv`

### Example invocations

```
"run tests on https://app.example.com using docs/tcs/login-tcs.md"
"execute login test cases against https://staging.app.com --stop-on-fail"
"web test docs/tcs/checkout-tcs.md on https://app.com"
```

### Tokens

- `{ALICE_ROOT}` — resolves to Alice project root (built-in, no config needed)

### Global install

Yes — add to `config/install-config.json`. No personal data beyond `{ALICE_ROOT}`.

---

## Error Handling

### Script-level (before execution)

| Error | Behaviour |
|---|---|
| TC file not found | Exit immediately, Alice reports error |
| TC file has no parseable TCs | Exit: "No test cases found in file" |
| Claude API call fails | Mark all steps in that TC as ERROR, continue |
| Playwright not installed | Exit with install instructions |
| URL unreachable | Exit immediately, Alice reports error |

### Step-level (during execution)

| Error | Behaviour |
|---|---|
| Element not found | FAIL + screenshot, continue or stop per flag |
| Assertion fails | FAIL + actual vs expected in report |
| Step timeout (10s) | FAIL + "Timeout waiting for element" |
| Low confidence JSON (`< 0.6`) | WARN + attempt step anyway |
| Multiple elements matched | FAIL + "Multiple elements matched target" |

---

## File Locations

| File | Path |
|---|---|
| Skill | `skills/alice-web-executor.md` |
| Script | `auto-scripts/web_executor.py` |
| Reports | `docs/tcs/<slug>-results-YYYY-MM-DD.md` |
| Screenshots | `data/screenshots/<slug>/<tc-id>-step-<n>.png` |
| Run log | `data/logs.csv` |

---

## Dependencies

- `playwright` (Python) — `pip install playwright && playwright install chromium`
- `anthropic` — `pip install anthropic`
- All deps managed via `{ALICE_ROOT}/.venv/`

---

## Out of Scope

- Locator fallback via Claude Vision (can be added later as enhancement)
- Intermediate JSON file between parsing and execution
- Parallel TC execution
- Non-Chromium browsers
