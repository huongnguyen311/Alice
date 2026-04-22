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
    if url_fragment.startswith(("http://", "https://")):
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
    # WARN only applies when the action SUCCEEDS with low confidence.
    # If execution raises an exception, the except block returns FAIL directly,
    # bypassing this flag. FAIL always takes precedence over WARN.
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
                locator = page.get_by_text(expected).first
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
                matched_selector = None
                for selector in _resolve_locator(target):
                    try:
                        loc = page.locator(selector)
                        if loc.count() > 0:
                            matched_selector = selector
                            break
                    except Exception:
                        continue
                if matched_selector is None:
                    raise Exception(f"Element '{target}' not found")
                if not page.locator(matched_selector).is_disabled():
                    raise Exception(f"Element '{target}' found but is not disabled")
                base_result["actual"] = f"Element '{matched_selector}' is disabled"
            else:
                raise Exception(f"Unknown assertion type '{atype}'")

    except Exception as e:
        return {**base_result, "status": "FAIL", "error": str(e), "screenshot_hint": True}

    if warn_after:
        base_result["status"] = "WARN"

    return base_result


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
        "| Total | Passed | Failed | Errors | Skipped | Warned |",
        "|---|---|---|---|---|---|",
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
            lines += ["", f"> Screenshots saved to `data/screenshots/{r['id'].lower()}/`"]

    lines += ["", "---", ""]

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text("\n".join(lines), encoding="utf-8")


# ── Orchestrator ─────────────────────────────────────────────────────────────

def run_tc(client, page, tc: dict, base_url: str, stop_on_fail: bool, screenshot_dir: Path) -> dict:
    """
    Run a single TC: interpret steps → execute actions → collect results.

    Returns a TC result dict with keys: id, name, status, duration_s, steps
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
    import anthropic
    from playwright.sync_api import sync_playwright

    parser = argparse.ArgumentParser(description="Alice Web Automation Executor")
    parser.add_argument("--tc-file", required=True, help="Path to TC Markdown file")
    parser.add_argument("--url", required=True, help="Base URL to test against")
    parser.add_argument("--stop-on-fail", action="store_true",
                        help="Stop TC execution on first failing step")
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


# ── Bootstrap ────────────────────────────────────────────────────────────────

def _bootstrap() -> None:
    _ensure_pkg("playwright")
    _ensure_pkg("anthropic")


if __name__ == "__main__":
    _bootstrap()
    main()
