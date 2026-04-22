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


# ── Bootstrap ────────────────────────────────────────────────────────────────

def _bootstrap() -> None:
    _ensure_pkg("playwright")
    _ensure_pkg("anthropic")


if __name__ == "__main__":
    _bootstrap()
