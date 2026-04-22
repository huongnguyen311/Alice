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
