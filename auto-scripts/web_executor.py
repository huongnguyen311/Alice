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
    tc_pattern = re.compile(r"^TC-\d+$")

    for line in content.splitlines():
        line = line.strip()
        # Must be a pipe-delimited row
        if not line.startswith("|"):
            continue
        cells = [c.strip() for c in line.strip("|").split("|")]
        # Skip separator rows (detect dashes in any cell)
        if any(re.fullmatch(r"-+", c) for c in cells):
            continue
        # Must have at least 8 cells
        if len(cells) < 8:
            continue
        tc_id = cells[0].strip().upper()
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


# ── Step Interpreter ─────────────────────────────────────────────────────────

DEFAULT_MODEL = "claude-haiku-4-5-20251001"

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

Return a JSON array of actions — one per step. Nothing else.

Example output:
[
  {"action": "navigate", "target": "", "value": "", "url": "/login", "assertion": {"type": "", "expected": ""}, "confidence": 0.95},
  {"action": "fill", "target": "username_field", "value": "admin", "url": "", "assertion": {"type": "", "expected": ""}, "confidence": 0.9}
]
"""


def interpret_steps(client, steps_raw: str, test_data: str, model: str = DEFAULT_MODEL) -> list[dict]:
    """
    Call Claude API to convert raw step text into a list of JSON action dicts.

    Returns a list of action dicts. On API failure, returns a single error action dict.
    """
    user_prompt = f"""Convert the following test steps into a JSON array of actions.

Steps:
{steps_raw}

Test Data (if any):
{test_data}

Return ONLY the JSON array. No markdown, no explanation."""

    try:
        message = client.messages.create(
            model=model,
            max_tokens=2048,
            system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": user_prompt}],
        )
        if not message.content:
            raise ValueError("Claude returned an empty content list")
        raw = message.content[0].text.strip()
        # Strip markdown fences if present
        raw = re.sub(r"^```[a-z]*\s*\n?", "", raw)
        raw = re.sub(r"\n?\s*```$", "", raw)
        result = json.loads(raw)
        if not isinstance(result, list):
            result = [result]
        return result
    except Exception as e:
        return [{"action": "error", "error": str(e), "confidence": 0.0,
                 "target": "", "value": "", "url": "", "assertion": {"type": "", "expected": ""}}]


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


# ── Bootstrap ────────────────────────────────────────────────────────────────

def _bootstrap() -> None:
    _ensure_pkg("playwright")
    _ensure_pkg("anthropic")


if __name__ == "__main__":
    _bootstrap()
