# Web Automation Executor Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build an Alice skill + Python script that reads a TC Markdown file, converts test steps to JSON actions via Claude API, executes them in a Playwright browser, and writes a result report.

**Architecture:** Single Python script (`web_executor.py`) handles all stages: parse TC Markdown → call Claude API per TC → run Playwright actions → write report. Alice skill (`alice-web-executor.md`) wraps the script with input validation and invocation logic. Report saved as a separate file alongside TC files.

**Tech Stack:** Python 3, Playwright (chromium), Anthropic Python SDK, `argparse`, `re` (stdlib), `pathlib` (stdlib)

---

## File Map

| File | Action | Responsibility |
|---|---|---|
| `auto-scripts/web_executor.py` | Create | All execution logic: parse, interpret, execute, report |
| `skills/alice-web-executor.md` | Create | Alice skill — validates inputs, calls script, confirms output |
| `config/install-config.json.example` | Modify | Add `alice-web-executor` entry |
| `config/install-config.json` | Modify | Add `alice-web-executor` entry (if file exists) |
| `skills/route-request.md` | Modify | Add skill triggers to routing table |
| `capabilities.md` (if exists) | Modify | Add skill row to Skills Index |

---

## Task 1: Set Up Dependencies

**Files:**
- Read: `requirements.txt`
- Modify: `requirements.txt`

- [ ] **Step 1: Check existing requirements.txt**

Run:
```bash
cat requirements.txt
```

- [ ] **Step 2: Add missing dependencies**

Add to `requirements.txt` if not already present:
```
playwright>=1.40.0
anthropic>=0.25.0
```

- [ ] **Step 3: Install dependencies into venv**

Run:
```bash
.venv/Scripts/python.exe -m pip install playwright anthropic
.venv/Scripts/python.exe -m playwright install chromium
```

Expected output: `playwright install chromium` downloads Chromium browser binaries. No errors.

- [ ] **Step 4: Verify playwright works**

Run:
```bash
.venv/Scripts/python.exe -c "from playwright.sync_api import sync_playwright; print('OK')"
```

Expected: `OK`

- [ ] **Step 5: Verify anthropic works**

Run:
```bash
.venv/Scripts/python.exe -c "import anthropic; print('OK')"
```

Expected: `OK`

- [ ] **Step 6: Commit**

```bash
git add requirements.txt
git commit -m "chore: add playwright and anthropic to requirements"
```

---

## Task 2: TC Markdown Parser

**Files:**
- Create: `auto-scripts/web_executor.py` (parser section only)
- Create: `auto-scripts/tests/test_tc_parser.py`

The TC files from `alice-test-design-engine` follow this structure:

```markdown
| TC-01 | Login with valid credentials | ... | High | ... | username: test_user | 1. Open login page\n2. Enter username | Login succeeds |
```

- [ ] **Step 1: Write failing test for TC parser**

Create `auto-scripts/tests/test_tc_parser.py`:

```python
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from web_executor import parse_tc_markdown

SAMPLE_MD = """
# Test Cases: Login

| TC ID | Name | Module | Priority | Type | Test Data | Steps | Expected Result |
|---|---|---|---|---|---|---|---|
| TC-01 | Valid login | Auth | High | Functional | username: admin, password: secret | 1. Navigate to /login\n2. Enter username "admin"\n3. Enter password "secret"\n4. Click Login button\n5. Verify redirect to /dashboard | User is redirected to dashboard |
| TC-02 | Empty username | Auth | Medium | Negative | username: (empty), password: secret | 1. Navigate to /login\n2. Leave username empty\n3. Enter password "secret"\n4. Click Login button\n5. Verify error message displayed | Error message "Username required" shown |
"""

def test_parse_returns_two_tcs():
    tcs = parse_tc_markdown(SAMPLE_MD)
    assert len(tcs) == 2

def test_parse_tc_fields():
    tcs = parse_tc_markdown(SAMPLE_MD)
    tc = tcs[0]
    assert tc["id"] == "TC-01"
    assert tc["name"] == "Valid login"
    assert tc["priority"] == "High"
    assert "Navigate to /login" in tc["steps_raw"]
    assert "redirected to dashboard" in tc["expected_result"]

def test_parse_test_data():
    tcs = parse_tc_markdown(SAMPLE_MD)
    assert "admin" in tcs[0]["test_data"]

def test_parse_skips_non_tc_rows():
    md = """
| Header | Row | x | x | x | x | x | x |
|---|---|---|---|---|---|---|---|
| TC-01 | Name | Mod | High | Func | data | 1. step | result |
## Coverage Matrix
| Requirement | TC IDs |
| FR-01 | TC-01 |
"""
    tcs = parse_tc_markdown(md)
    assert len(tcs) == 1
    assert tcs[0]["id"] == "TC-01"
```

- [ ] **Step 2: Run test to verify it fails**

Run:
```bash
.venv/Scripts/python.exe -m pytest auto-scripts/tests/test_tc_parser.py -v
```

Expected: `ModuleNotFoundError` or `ImportError` — `web_executor` does not exist yet.

- [ ] **Step 3: Create web_executor.py with parse_tc_markdown**

Create `auto-scripts/web_executor.py`:

```python
#!/usr/bin/env python3
"""
web_executor.py — Alice Web Automation Executor

Usage:
    python web_executor.py --tc-file docs/tcs/login-tcs.md --url https://example.com [--stop-on-fail]

Stages:
    1. Parse TC Markdown file → list of TC dicts
    2. Call Claude API to convert each step to a JSON action
    3. Execute actions in Playwright (headless Chromium)
    4. Write result report to docs/tcs/<slug>-results-YYYY-MM-DD.md
"""

import argparse
import importlib.util
import json
import os
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path

# ── Dependency guard ────────────────────────────────────────────────────────
def _ensure_pkg(pkg: str, install_name: str | None = None) -> None:
    if importlib.util.find_spec(pkg) is None:
        subprocess.run(
            [sys.executable, "-m", "pip", "install", install_name or pkg],
            check=True
        )

_ensure_pkg("playwright")
_ensure_pkg("anthropic")


# ── TC Parser ────────────────────────────────────────────────────────────────

def parse_tc_markdown(content: str) -> list[dict]:
    """
    Parse a TC Markdown file and return a list of TC dicts.

    Each dict has keys:
        id, name, module, priority, type, test_data, steps_raw, expected_result

    Rows are included only if the first cell matches the TC-NN pattern.
    Non-TC sections (coverage matrix, headers) are ignored.
    """
    tcs = []
    tc_pattern = re.compile(r"^TC-\d+$", re.IGNORECASE)

    for line in content.splitlines():
        line = line.strip()
        # Must be a pipe-delimited row with at least 8 cells
        if not line.startswith("|") or line.startswith("|---"):
            continue
        cells = [c.strip() for c in line.strip("|").split("|")]
        if len(cells) < 8:
            continue
        tc_id = cells[0].strip()
        if not tc_pattern.match(tc_id):
            continue

        tcs.append({
            "id":              tc_id,
            "name":            cells[1],
            "module":          cells[2],
            "priority":        cells[3],
            "type":            cells[4],
            "test_data":       cells[5],
            "steps_raw":       cells[6],
            "expected_result": cells[7],
        })

    return tcs
```

- [ ] **Step 4: Run test to verify it passes**

Run:
```bash
.venv/Scripts/python.exe -m pytest auto-scripts/tests/test_tc_parser.py -v
```

Expected: all 4 tests PASS.

- [ ] **Step 5: Commit**

```bash
git add auto-scripts/web_executor.py auto-scripts/tests/test_tc_parser.py
git commit -m "feat: add TC markdown parser"
```

---

## Task 3: Step Interpreter (Claude API)

**Files:**
- Modify: `auto-scripts/web_executor.py`
- Create: `auto-scripts/tests/test_step_interpreter.py`

- [ ] **Step 1: Write failing test**

Create `auto-scripts/tests/test_step_interpreter.py`:

```python
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock
sys.path.insert(0, str(Path(__file__).parent.parent))

from web_executor import interpret_steps

STEPS_RAW = "1. Navigate to /login\n2. Enter username \"admin\"\n3. Click Login button\n4. Verify redirect to /dashboard"
TEST_DATA = "username: admin, password: secret"

# Mock Claude API response
MOCK_ACTIONS = [
    {"action": "navigate", "target": "", "value": "", "url": "/login", "assertion": {"type": "", "expected": ""}, "confidence": 0.95},
    {"action": "fill", "target": "username", "value": "admin", "url": "", "assertion": {"type": "", "expected": ""}, "confidence": 0.9},
    {"action": "click", "target": "login_button", "value": "", "url": "", "assertion": {"type": "", "expected": ""}, "confidence": 0.85},
    {"action": "verify", "target": "", "value": "", "url": "", "assertion": {"type": "url", "expected": "/dashboard"}, "confidence": 0.9},
]

def test_interpret_steps_returns_list():
    mock_client = MagicMock()
    mock_msg = MagicMock()
    mock_msg.content = [MagicMock(text=f"```json\n{json.dumps(MOCK_ACTIONS)}\n```")]
    mock_client.messages.create.return_value = mock_msg

    import json
    actions = interpret_steps(mock_client, STEPS_RAW, TEST_DATA)
    assert isinstance(actions, list)
    assert len(actions) == 4

def test_interpret_steps_action_schema():
    mock_client = MagicMock()
    mock_msg = MagicMock()

    import json
    mock_msg.content = [MagicMock(text=json.dumps(MOCK_ACTIONS))]
    mock_client.messages.create.return_value = mock_msg

    actions = interpret_steps(mock_client, STEPS_RAW, TEST_DATA)
    for action in actions:
        assert "action" in action
        assert "confidence" in action
        assert action["action"] in ("navigate", "click", "fill", "select", "verify", "wait")

def test_interpret_steps_api_failure_returns_error():
    mock_client = MagicMock()
    mock_client.messages.create.side_effect = Exception("API error")

    actions = interpret_steps(mock_client, STEPS_RAW, TEST_DATA)
    assert len(actions) == 1
    assert actions[0]["action"] == "error"
    assert "API error" in actions[0]["error"]
```

- [ ] **Step 2: Run test to verify it fails**

Run:
```bash
.venv/Scripts/python.exe -m pytest auto-scripts/tests/test_step_interpreter.py -v
```

Expected: `ImportError` — `interpret_steps` not defined yet.

- [ ] **Step 3: Add interpret_steps to web_executor.py**

Append to `auto-scripts/web_executor.py` after the parser section:

```python
# ── Step Interpreter ─────────────────────────────────────────────────────────

SYSTEM_PROMPT = """You are a QA automation step interpreter.

Your job is to convert test steps written in natural language into a list of structured JSON actions.

You MUST:
- Output ONLY a valid JSON array (no explanation, no extra text, no markdown fences)
- Follow the exact schema provided
- Choose the most appropriate action type
- Normalize target names into snake_case
- Infer missing values ONLY if highly confident
- If uncertain, mark "confidence" < 0.6

DO NOT:
- Invent UI elements that are not implied
- Combine multiple steps into one action
- Return plain text or markdown

Action types allowed: navigate, click, fill, select, verify, wait

Action mapping rules:
- "open / go to / navigate" → navigate
- "click / press / tap" → click
- "enter / input / type / fill" → fill
- "select / choose" → select
- "verify / check / should / assert" → verify
- "wait" → wait

Assertion type mapping (for verify actions):
- "redirect / url" → {"type": "url", "expected": "<url>"}
- "display / show / visible" → {"type": "text_visible", "expected": "<text>"}
- "exist / present" → {"type": "element_exists", "expected": ""}
- "disabled" → {"type": "state_disabled", "expected": ""}

Output schema for each action:
{
  "action": "",
  "target": "",
  "value": "",
  "url": "",
  "assertion": {"type": "", "expected": ""},
  "confidence": 0.0
}

Return a JSON array of actions — one per step. Nothing else."""


def interpret_steps(client, steps_raw: str, test_data: str) -> list[dict]:
    """
    Call Claude API to convert raw step text into a list of JSON action dicts.

    Returns a list of action dicts. On API failure, returns a single error action dict.
    """
    import anthropic

    user_prompt = f"""Convert the following test steps into a JSON array of actions.

Steps:
{steps_raw}

Test Data (if any):
{test_data}

Return ONLY the JSON array. No markdown, no explanation."""

    try:
        message = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=2048,
            system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": user_prompt}],
        )
        raw = message.content[0].text.strip()
        # Strip markdown fences if present
        raw = re.sub(r"^```(?:json)?\n?", "", raw)
        raw = re.sub(r"\n?```$", "", raw)
        return json.loads(raw)
    except Exception as e:
        return [{"action": "error", "error": str(e), "confidence": 0.0,
                 "target": "", "value": "", "url": "", "assertion": {"type": "", "expected": ""}}]
```

- [ ] **Step 4: Run test to verify it passes**

Run:
```bash
.venv/Scripts/python.exe -m pytest auto-scripts/tests/test_step_interpreter.py -v
```

Expected: all 3 tests PASS.

- [ ] **Step 5: Commit**

```bash
git add auto-scripts/web_executor.py auto-scripts/tests/test_step_interpreter.py
git commit -m "feat: add Claude API step interpreter"
```

---

## Task 4: Action Executor (Playwright)

**Files:**
- Modify: `auto-scripts/web_executor.py`
- Create: `auto-scripts/tests/test_action_executor.py`

- [ ] **Step 1: Write failing test**

Create `auto-scripts/tests/test_action_executor.py`:

```python
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch, call
sys.path.insert(0, str(Path(__file__).parent.parent))

from web_executor import execute_action

def make_page_mock():
    page = MagicMock()
    page.url = "https://example.com/dashboard"
    return page

def test_navigate_action():
    page = make_page_mock()
    action = {"action": "navigate", "url": "https://example.com/login",
               "target": "", "value": "", "assertion": {"type": "", "expected": ""}, "confidence": 0.9}
    result = execute_action(page, action, base_url="https://example.com")
    page.goto.assert_called_once_with("https://example.com/login")
    assert result["status"] == "PASS"

def test_fill_action():
    page = make_page_mock()
    action = {"action": "fill", "target": "username", "value": "admin",
               "url": "", "assertion": {"type": "", "expected": ""}, "confidence": 0.9}
    result = execute_action(page, action, base_url="https://example.com")
    page.fill.assert_called_once()
    assert result["status"] == "PASS"

def test_click_action():
    page = make_page_mock()
    action = {"action": "click", "target": "login_button", "value": "",
               "url": "", "assertion": {"type": "", "expected": ""}, "confidence": 0.9}
    result = execute_action(page, action, base_url="https://example.com")
    page.click.assert_called_once()
    assert result["status"] == "PASS"

def test_low_confidence_marks_warn():
    page = make_page_mock()
    action = {"action": "click", "target": "some_button", "value": "",
               "url": "", "assertion": {"type": "", "expected": ""}, "confidence": 0.4}
    result = execute_action(page, action, base_url="https://example.com")
    assert result["status"] == "WARN"

def test_error_action_marks_error():
    page = make_page_mock()
    action = {"action": "error", "error": "API failed", "target": "", "value": "",
               "url": "", "assertion": {"type": "", "expected": ""}, "confidence": 0.0}
    result = execute_action(page, action, base_url="https://example.com")
    assert result["status"] == "ERROR"
    assert "API failed" in result["error"]

def test_playwright_exception_marks_fail():
    page = make_page_mock()
    page.click.side_effect = Exception("Element not found")
    action = {"action": "click", "target": "login_button", "value": "",
               "url": "", "assertion": {"type": "", "expected": ""}, "confidence": 0.9}
    result = execute_action(page, action, base_url="https://example.com")
    assert result["status"] == "FAIL"
    assert "Element not found" in result["error"]
```

- [ ] **Step 2: Run test to verify it fails**

Run:
```bash
.venv/Scripts/python.exe -m pytest auto-scripts/tests/test_action_executor.py -v
```

Expected: `ImportError` — `execute_action` not defined yet.

- [ ] **Step 3: Add execute_action to web_executor.py**

Append to `auto-scripts/web_executor.py`:

```python
# ── Action Executor ──────────────────────────────────────────────────────────

LOCATOR_STRATEGIES = [
    lambda t: f"[name='{t}']",
    lambda t: f"[id='{t}']",
    lambda t: f"[placeholder*='{t}']",
    lambda t: f"[aria-label*='{t}']",
    lambda t: f"text={t.replace('_', ' ')}",
    lambda t: f"button:has-text('{t.replace('_', ' ')}')",
]


def _resolve_locator(target: str) -> list[str]:
    """Return a list of CSS/Playwright selectors to try for a target name."""
    return [strategy(target) for strategy in LOCATOR_STRATEGIES]


def _build_url(base_url: str, url_fragment: str) -> str:
    """Combine base URL with a relative or absolute URL fragment."""
    if not url_fragment:
        return base_url
    if url_fragment.startswith("http"):
        return url_fragment
    return base_url.rstrip("/") + "/" + url_fragment.lstrip("/")


def execute_action(page, action: dict, base_url: str) -> dict:
    """
    Execute a single JSON action on a Playwright page.

    Returns a result dict with keys: action, status, actual, error, screenshot_hint
    Status values: PASS, FAIL, WARN, ERROR, SKIP
    """
    act = action.get("action", "")
    target = action.get("target", "")
    value = action.get("value", "")
    url = action.get("url", "")
    assertion = action.get("assertion", {})
    confidence = action.get("confidence", 1.0)

    base_result = {
        "action": act,
        "target": target,
        "status": "PASS",
        "actual": "",
        "error": "",
        "screenshot_hint": False,
    }

    # Pre-flight: error actions from interpreter
    if act == "error":
        return {**base_result, "status": "ERROR", "error": action.get("error", "Unknown interpreter error")}

    # Low confidence — attempt but warn
    warn_after = confidence < 0.6

    try:
        if act == "navigate":
            full_url = _build_url(base_url, url)
            page.goto(full_url)
            base_result["actual"] = f"Navigated to {full_url}"

        elif act == "click":
            for selector in _resolve_locator(target):
                try:
                    page.click(selector, timeout=10000)
                    base_result["actual"] = f"Clicked {selector}"
                    break
                except Exception:
                    continue
            else:
                raise Exception(f"No element found matching target '{target}'")

        elif act == "fill":
            for selector in _resolve_locator(target):
                try:
                    page.fill(selector, value, timeout=10000)
                    base_result["actual"] = f"Filled {selector} with '{value}'"
                    break
                except Exception:
                    continue
            else:
                raise Exception(f"No element found matching target '{target}'")

        elif act == "select":
            for selector in _resolve_locator(target):
                try:
                    page.select_option(selector, value, timeout=10000)
                    base_result["actual"] = f"Selected '{value}' in {selector}"
                    break
                except Exception:
                    continue
            else:
                raise Exception(f"No element found matching target '{target}'")

        elif act == "wait":
            for selector in _resolve_locator(target):
                try:
                    page.wait_for_selector(selector, timeout=10000)
                    base_result["actual"] = f"Element '{selector}' appeared"
                    break
                except Exception:
                    continue
            else:
                raise Exception(f"Timeout waiting for target '{target}'")

        elif act == "verify":
            atype = assertion.get("type", "")
            expected = assertion.get("expected", "")
            if atype == "url":
                actual_url = page.url
                base_result["actual"] = actual_url
                if expected not in actual_url:
                    raise Exception(f"URL assertion failed: expected '{expected}' in '{actual_url}'")
            elif atype == "text_visible":
                locator = page.get_by_text(expected)
                if not locator.is_visible():
                    raise Exception(f"Text '{expected}' not visible on page")
                base_result["actual"] = f"Text '{expected}' visible"
            elif atype == "element_exists":
                for selector in _resolve_locator(target):
                    try:
                        if page.locator(selector).count() > 0:
                            base_result["actual"] = f"Element '{selector}' exists"
                            break
                    except Exception:
                        continue
                else:
                    raise Exception(f"Element '{target}' not found")
            elif atype == "state_disabled":
                for selector in _resolve_locator(target):
                    try:
                        if page.locator(selector).is_disabled():
                            base_result["actual"] = f"Element '{selector}' is disabled"
                            break
                    except Exception:
                        continue
                else:
                    raise Exception(f"Element '{target}' is not disabled or not found")
            else:
                base_result["actual"] = f"Unknown assertion type '{atype}' — skipped"

    except Exception as e:
        return {**base_result, "status": "FAIL", "error": str(e), "screenshot_hint": True}

    if warn_after:
        base_result["status"] = "WARN"

    return base_result
```

- [ ] **Step 4: Run test to verify it passes**

Run:
```bash
.venv/Scripts/python.exe -m pytest auto-scripts/tests/test_action_executor.py -v
```

Expected: all 6 tests PASS.

- [ ] **Step 5: Commit**

```bash
git add auto-scripts/web_executor.py auto-scripts/tests/test_action_executor.py
git commit -m "feat: add Playwright action executor"
```

---

## Task 5: Result Collector + Report Writer

**Files:**
- Modify: `auto-scripts/web_executor.py`
- Create: `auto-scripts/tests/test_report_writer.py`

- [ ] **Step 1: Write failing test**

Create `auto-scripts/tests/test_report_writer.py`:

```python
import sys
from pathlib import Path
import tempfile
sys.path.insert(0, str(Path(__file__).parent.parent))

from web_executor import write_report

SAMPLE_RESULTS = [
    {
        "id": "TC-01",
        "name": "Valid login",
        "status": "PASS",
        "duration_s": 2.3,
        "steps": [
            {"action": "navigate", "target": "", "status": "PASS", "actual": "Navigated to /login", "error": "", "screenshot_hint": False},
            {"action": "fill", "target": "username", "status": "PASS", "actual": "Filled username with 'admin'", "error": "", "screenshot_hint": False},
            {"action": "verify", "target": "", "status": "PASS", "actual": "URL contains /dashboard", "error": "", "screenshot_hint": False},
        ],
    },
    {
        "id": "TC-02",
        "name": "Empty username",
        "status": "FAIL",
        "duration_s": 1.1,
        "steps": [
            {"action": "navigate", "target": "", "status": "PASS", "actual": "Navigated to /login", "error": "", "screenshot_hint": False},
            {"action": "verify", "target": "error_message", "status": "FAIL", "actual": "", "error": "Text 'Username required' not visible", "screenshot_hint": True},
        ],
    },
]

def test_write_report_creates_file():
    with tempfile.TemporaryDirectory() as tmpdir:
        out_path = Path(tmpdir) / "report.md"
        write_report(
            results=SAMPLE_RESULTS,
            output_path=out_path,
            url="https://example.com",
            tc_file="docs/tcs/login-tcs.md",
            stop_on_fail=False,
            run_date="2026-04-22",
        )
        assert out_path.exists()

def test_write_report_contains_summary():
    with tempfile.TemporaryDirectory() as tmpdir:
        out_path = Path(tmpdir) / "report.md"
        write_report(
            results=SAMPLE_RESULTS,
            output_path=out_path,
            url="https://example.com",
            tc_file="docs/tcs/login-tcs.md",
            stop_on_fail=False,
            run_date="2026-04-22",
        )
        content = out_path.read_text()
        assert "TC-01" in content
        assert "TC-02" in content
        assert "PASS" in content
        assert "FAIL" in content
        assert "Total" in content

def test_write_report_stats():
    with tempfile.TemporaryDirectory() as tmpdir:
        out_path = Path(tmpdir) / "report.md"
        write_report(
            results=SAMPLE_RESULTS,
            output_path=out_path,
            url="https://example.com",
            tc_file="docs/tcs/login-tcs.md",
            stop_on_fail=False,
            run_date="2026-04-22",
        )
        content = out_path.read_text()
        assert "1" in content  # 1 passed
        assert "2026-04-22" in content
```

- [ ] **Step 2: Run test to verify it fails**

Run:
```bash
.venv/Scripts/python.exe -m pytest auto-scripts/tests/test_report_writer.py -v
```

Expected: `ImportError` — `write_report` not defined yet.

- [ ] **Step 3: Add write_report to web_executor.py**

Append to `auto-scripts/web_executor.py`:

```python
# ── Report Writer ────────────────────────────────────────────────────────────

def write_report(
    results: list[dict],
    output_path: Path,
    url: str,
    tc_file: str,
    stop_on_fail: bool,
    run_date: str,
) -> None:
    """Write a Markdown test result report to output_path."""
    total = len(results)
    passed = sum(1 for r in results if r["status"] == "PASS")
    failed = sum(1 for r in results if r["status"] == "FAIL")
    errored = sum(1 for r in results if r["status"] == "ERROR")
    skipped = sum(1 for r in results if r["status"] == "SKIP")
    warned = sum(1 for r in results if r["status"] == "WARN")

    status_emoji = {"PASS": "✅", "FAIL": "❌", "SKIP": "⏭️", "ERROR": "🔴", "WARN": "⚠️"}

    lines = [
        f"# Test Results: {Path(tc_file).stem}",
        "",
        f"> **URL:** {url}",
        f"> **TC File:** {tc_file}",
        f"> **Run Date:** {run_date}",
        f"> **Stop on Fail:** {'Yes' if stop_on_fail else 'No'}",
        f"> **Generated:** Alice Web Executor",
        "",
        "---",
        "",
        "## Summary",
        "",
        f"| Total | Passed | Failed | Errors | Skipped | Warned |",
        f"|---|---|---|---|---|---|",
        f"| {total} | {passed} | {failed} | {errored} | {skipped} | {warned} |",
        "",
        "---",
        "",
        "## Test Case Results",
        "",
        "| TC ID | Name | Status | Duration |",
        "|---|---|---|---|",
    ]

    for r in results:
        emoji = status_emoji.get(r["status"], "")
        lines.append(f"| {r['id']} | {r['name']} | {emoji} {r['status']} | {r.get('duration_s', 0):.1f}s |")

    lines += ["", "---", "", "## Detail"]

    for r in results:
        emoji = status_emoji.get(r["status"], "")
        lines += [
            "",
            f"### {r['id']} — {r['name']} {emoji}",
            "",
            f"**Status:** {r['status']} | **Duration:** {r.get('duration_s', 0):.1f}s",
            "",
            "| Step | Action | Target | Status | Actual / Error |",
            "|---|---|---|---|---|",
        ]
        for i, step in enumerate(r.get("steps", []), 1):
            s_emoji = status_emoji.get(step["status"], "")
            detail = step["error"] if step["error"] else step["actual"]
            lines.append(f"| {i} | {step['action']} | {step.get('target', '')} | {s_emoji} {step['status']} | {detail} |")

        if any(s.get("screenshot_hint") for s in r.get("steps", [])):
            lines += ["", f"> Screenshots saved to `data/screenshots/{Path(tc_file).stem}/`"]

    lines += ["", "---", ""]

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text("\n".join(lines), encoding="utf-8")
```

- [ ] **Step 4: Run test to verify it passes**

Run:
```bash
.venv/Scripts/python.exe -m pytest auto-scripts/tests/test_report_writer.py -v
```

Expected: all 3 tests PASS.

- [ ] **Step 5: Commit**

```bash
git add auto-scripts/web_executor.py auto-scripts/tests/test_report_writer.py
git commit -m "feat: add result collector and report writer"
```

---

## Task 6: Main Orchestrator + CLI

**Files:**
- Modify: `auto-scripts/web_executor.py`

- [ ] **Step 1: Run all tests to confirm green baseline**

Run:
```bash
.venv/Scripts/python.exe -m pytest auto-scripts/tests/ -v
```

Expected: all tests PASS before adding the orchestrator.

- [ ] **Step 2: Add main() and CLI to web_executor.py**

Append to `auto-scripts/web_executor.py`:

```python
# ── Orchestrator ─────────────────────────────────────────────────────────────

def run_tc(client, page, tc: dict, base_url: str, stop_on_fail: bool, screenshot_dir: Path) -> dict:
    """
    Run a single TC: interpret steps → execute actions → collect results.

    Returns a TC result dict.
    """
    import time

    actions = interpret_steps(client, tc["steps_raw"], tc["test_data"])

    step_results = []
    tc_status = "PASS"
    start = time.time()

    for action in actions:
        result = execute_action(page, action, base_url)
        step_results.append(result)

        if result["status"] in ("FAIL", "ERROR"):
            tc_status = result["status"]
            # Take screenshot on fail
            try:
                screenshot_dir.mkdir(parents=True, exist_ok=True)
                shot_path = screenshot_dir / f"{tc['id']}-step-{len(step_results)}.png"
                page.screenshot(path=str(shot_path))
            except Exception:
                pass

            if stop_on_fail:
                # Mark remaining actions as SKIP
                remaining = actions[len(step_results):]
                for remaining_action in remaining:
                    step_results.append({
                        "action": remaining_action.get("action", ""),
                        "target": remaining_action.get("target", ""),
                        "status": "SKIP",
                        "actual": "",
                        "error": "Skipped due to --stop-on-fail",
                        "screenshot_hint": False,
                    })
                break

        elif result["status"] == "WARN" and tc_status == "PASS":
            tc_status = "WARN"

    duration = time.time() - start

    return {
        "id": tc["id"],
        "name": tc["name"],
        "status": tc_status,
        "duration_s": round(duration, 2),
        "steps": step_results,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Alice Web Automation Executor")
    parser.add_argument("--tc-file", required=True, help="Path to TC Markdown file")
    parser.add_argument("--url", required=True, help="Base URL to test against")
    parser.add_argument("--stop-on-fail", action="store_true", help="Stop TC execution on first failing step")
    args = parser.parse_args()

    tc_path = Path(args.tc_file)
    if not tc_path.exists():
        print(f"ERROR: TC file not found: {tc_path}", file=sys.stderr)
        sys.exit(1)

    base_url = args.url.rstrip("/")

    # Parse TCs
    content = tc_path.read_text(encoding="utf-8")
    tcs = parse_tc_markdown(content)
    if not tcs:
        print("ERROR: No test cases found in file.", file=sys.stderr)
        sys.exit(1)

    print(f"Found {len(tcs)} test case(s) in {tc_path.name}")

    # Derive output paths
    import anthropic
    from playwright.sync_api import sync_playwright

    slug = tc_path.stem
    run_date = datetime.now().strftime("%Y-%m-%d")
    report_path = tc_path.parent / f"{slug}-results-{run_date}.md"
    screenshot_dir = Path("data/screenshots") / slug

    # Init Claude client
    api_key = os.environ.get("ANTHROPIC_API_KEY", "")
    client = anthropic.Anthropic(api_key=api_key) if api_key else anthropic.Anthropic()

    # Run with Playwright
    results = []
    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=True)
        page = browser.new_page()

        # Check URL reachable
        try:
            page.goto(base_url, timeout=15000)
        except Exception as e:
            print(f"ERROR: URL unreachable — {e}", file=sys.stderr)
            browser.close()
            sys.exit(1)

        for tc in tcs:
            print(f"  Running {tc['id']}: {tc['name']} ...", end=" ", flush=True)
            result = run_tc(client, page, tc, base_url, args.stop_on_fail, screenshot_dir)
            results.append(result)
            print(result["status"])

        browser.close()

    # Write report
    write_report(
        results=results,
        output_path=report_path,
        url=base_url,
        tc_file=str(tc_path),
        stop_on_fail=args.stop_on_fail,
        run_date=run_date,
    )

    passed = sum(1 for r in results if r["status"] == "PASS")
    failed = sum(1 for r in results if r["status"] in ("FAIL", "ERROR"))
    print(f"\nResults: {passed}/{len(results)} passed, {failed} failed")
    print(f"Report:  {report_path}")


if __name__ == "__main__":
    main()
```

- [ ] **Step 3: Run all tests to verify still passing**

Run:
```bash
.venv/Scripts/python.exe -m pytest auto-scripts/tests/ -v
```

Expected: all tests PASS.

- [ ] **Step 4: Smoke test CLI (dry run)**

Run (replace with any real URL and your TC file, or use a minimal test):
```bash
.venv/Scripts/python.exe auto-scripts/web_executor.py --help
```

Expected: help text printed, no errors.

- [ ] **Step 5: Commit**

```bash
git add auto-scripts/web_executor.py
git commit -m "feat: add main orchestrator and CLI for web executor"
```

---

## Task 7: Alice Skill File

**Files:**
- Create: `skills/alice-web-executor.md`

- [ ] **Step 1: Create the skill file**

Create `skills/alice-web-executor.md`:

```markdown
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
- Screenshots: `{ALICE_ROOT}/data/screenshots/<slug>/`
- Venv: `{ALICE_ROOT}/.venv/`
```

- [ ] **Step 2: Create the internal skill file**

Create `skills/web-executor-internal.md`:

```markdown
---
name: web-executor-internal
description: Internal skill — do not invoke directly. Use alice-web-executor instead.
scope: automation
triggers: []
---

# Skill: Web Executor Internal

## What this skill does

Validates inputs, invokes `web_executor.py`, and confirms the report path to the user.

---

## Step 1 — Extract inputs from user message

Parse from the user's message:
- **tc_file**: path to a `.md` file (e.g. `docs/tcs/login-tcs.md`)
- **url**: a URL starting with `http://` or `https://`
- **stop_on_fail**: present if user says "stop on fail", "stop-on-fail", or "--stop-on-fail"

If tc_file is missing, ask:
> "Which TC file should I run? (e.g. `docs/tcs/login-tcs.md`)"

If url is missing, ask:
> "Which URL should I test against?"

---

## Step 2 — Validate

1. Check `{ALICE_ROOT}/<tc_file>` exists. If not: report error and stop.
2. Check url starts with `http://` or `https://`. If not: report error and stop.

---

## Step 3 — Run the script

```bash
{ALICE_ROOT}/.venv/Scripts/python.exe {ALICE_ROOT}/auto-scripts/web_executor.py \
  --tc-file {ALICE_ROOT}/<tc_file> \
  --url <url> \
  [--stop-on-fail]
```

On Windows, use `Scripts/python.exe`. On Mac/Linux, use `bin/python`.

---

## Step 4 — Confirm to user

After the script completes, read the final line of stdout for the report path and confirm:

> "Tests complete. Report saved to `<report_path>`.
> Results: X/Y passed, Z failed."

---

## Step 5 — Log run

Append to `{ALICE_ROOT}/data/logs.csv`:
```
<timestamp>,web_executor,<tc_file>,<url>,<pass_count>/<total>,<report_path>
```
```

- [ ] **Step 3: Commit**

```bash
git add skills/alice-web-executor.md skills/web-executor-internal.md
git commit -m "feat: add alice-web-executor skill files"
```

---

## Task 8: Register Skill + Update Routing

**Files:**
- Modify: `config/install-config.json.example`
- Modify: `config/install-config.json` (if exists)
- Modify: `skills/route-request.md`
- Modify: `capabilities.md` (if exists at Alice root)

- [ ] **Step 1: Add to install-config.json.example**

In `config/install-config.json.example`, add inside the `"skills"` array before the closing `]`:

```json
{
  "name": "alice-web-executor",
  "file": "alice-web-executor.md",
  "type": "python",
  "mcp_required": null,
  "warning": "Requires ANTHROPIC_API_KEY env var and Playwright chromium installed",
  "enabled": true
}
```

- [ ] **Step 2: Add to install-config.json (if it exists)**

Run:
```bash
ls config/install-config.json 2>/dev/null && echo "EXISTS" || echo "MISSING"
```

If EXISTS, add the same entry to `config/install-config.json`.

- [ ] **Step 3: Add triggers to route-request.md**

In `skills/route-request.md`, find the trigger table in Step 3 and add:

```
| "run tests on" / "execute test cases" / "web test" / "test website" | alice-web-executor |
```

- [ ] **Step 4: Update capabilities.md (if it exists)**

Run:
```bash
ls capabilities.md 2>/dev/null && echo "EXISTS" || echo "MISSING"
```

If EXISTS, add a row to the Skills Index table:

```
| alice-web-executor | Run Playwright web automation tests from TC Markdown files | automation |
```

- [ ] **Step 5: Commit**

```bash
git add config/install-config.json.example skills/route-request.md
git add capabilities.md 2>/dev/null; true
git add config/install-config.json 2>/dev/null; true
git commit -m "feat: register alice-web-executor in routing and install config"
```

---

## Task 9: Install and Verify

- [ ] **Step 1: Run install.py to install the skill globally**

```bash
.venv/Scripts/python.exe auto-scripts/install.py
```

Expected: `[OK] alice-web-executor (python — paths rewritten to absolute)`

- [ ] **Step 2: Verify installed skill exists**

```bash
ls ~/.claude/skills/alice-web-executor/SKILL.md
```

Expected: file exists.

- [ ] **Step 3: Verify ALICE_ROOT token was substituted**

```bash
grep "ALICE_ROOT" ~/.claude/skills/alice-web-executor/SKILL.md
```

Expected: no matches — token replaced with actual path.

- [ ] **Step 4: Run full test suite one final time**

```bash
.venv/Scripts/python.exe -m pytest auto-scripts/tests/ -v
```

Expected: all tests PASS.

- [ ] **Step 5: Final commit**

```bash
git add -A
git status  # confirm only expected files
git commit -m "feat: web automation executor complete — skill + script + tests"
```

---

## Out of Scope (Future Enhancements)

- Locator fallback via Claude Vision API (screenshot → AI identifies element)
- Intermediate JSON file inspection between parse and execution
- Parallel TC execution
- Non-Chromium browser support
- HTML report format
