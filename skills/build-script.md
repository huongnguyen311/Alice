---
name: build-script
description: Write and register a new Python automation script. Use when the user asks to automate a task, build something that runs on a schedule, or create a script that processes data.
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

# Skill: Build Script

## When to Use
- User asks to automate a task
- User wants something to run on a schedule
- User wants to process, transform, or summarise data
- User asks to "build", "write", or "create" a script

## Script Conventions

All scripts in `/auto-scripts/` follow this pattern:

```python
import argparse
import csv
import os
from datetime import datetime

def main():
    parser = argparse.ArgumentParser(description="Script description")
    parser.add_argument("--input",  default="data/input.csv")
    parser.add_argument("--output", default="data/output.csv")
    parser.add_argument("--log",    default="data/logs.csv")
    args = parser.parse_args()

    os.makedirs(os.path.dirname(args.output), exist_ok=True)

    # --- Core logic here ---

    # Log the run
    log_run(args.log, "script_name", "success", "brief summary")
    print("Done: brief human-readable summary")


def log_run(log_path, script_name, status, summary):
    os.makedirs(os.path.dirname(log_path), exist_ok=True)
    file_exists = os.path.exists(log_path)
    with open(log_path, "a", newline="") as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow(["timestamp", "script", "status", "summary"])
        writer.writerow([datetime.now().isoformat(), script_name, status, summary])


if __name__ == "__main__":
    main()
```

## Checklist Before Finishing

- [ ] Script accepts `--input`, `--output`, `--log` CLI args with sensible defaults
- [ ] Input read from `/data/`, output written to `/data/`
- [ ] Run logged to `/data/logs.csv` via `log_run()`
- [ ] `os.makedirs(..., exist_ok=True)` used before any file write
- [ ] Human-readable summary printed to stdout on completion
- [ ] Script saved to `/auto-scripts/script_name.py`
- [ ] Dependency guard included at top (auto-install missing libs via `importlib.util.find_spec`)

## After Creating the Script

Tell the user:
1. What the script does
2. How to run it directly: `.venv/bin/python auto-scripts/script_name.py`
3. Offer to schedule it if relevant
