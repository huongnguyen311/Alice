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


# ── Bootstrap ────────────────────────────────────────────────────────────────

def _bootstrap() -> None:
    _ensure_pkg("playwright")
    _ensure_pkg("anthropic")


if __name__ == "__main__":
    _bootstrap()
