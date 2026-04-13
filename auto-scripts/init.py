#!/usr/bin/env python3
"""
Alice init script — write config files and copy missing memory templates.

Called by Alice after collecting identity and skill preferences conversationally.
Accepts collected data as a JSON string via --data flag.

Usage:
    python auto-scripts/init.py --data '{"_user": {...}, "alice-book-meeting": {...}}'

What it does:
  1. Writes / merges config/skill-personal.json with the provided _user section
     and any skill-specific sections (non-destructive: preserves existing keys
     not in the incoming data).
  2. Copies config/install-config.json from .example if it doesn't exist.
  3. Copies each missing personal memory file from its .example counterpart:
       memories/user_profile.md
       memories/reference.md
       memories/short_memory.md
       memories/project.md
  4. Fills in identity fields in memories/user_profile.md using the _user data.

Does NOT run install.py — Alice handles that step separately.
"""

import argparse
import json
import re
import shutil
import sys
from pathlib import Path

ALICE_ROOT = Path(__file__).parent.parent.resolve()

MEMORY_FILES = [
    "user_profile.md",
    "reference.md",
    "short_memory.md",
    "project.md",
]

IDENTITY_FIELD_MAP = {
    "name":         ("Name",         "Your Full Name"),
    "email":        ("Email",        "you@example.com"),
    "role":         ("Role",         "Your Job Title"),
    "organization": ("Organization", "Your Company"),
    "location":     ("Location",     "Your City, Country"),
    "timezone":     ("Timezone",     "UTC"),
    "language":     ("Language",     "en"),
}


def load_json(path: Path) -> dict:
    if path.exists():
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    return {}


def write_json(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
        f.write("\n")


def merge_personal(existing: dict, incoming: dict) -> dict:
    """Non-destructive merge: incoming values overwrite existing for matching keys,
    but existing keys not present in incoming are preserved."""
    result = dict(existing)
    for key, value in incoming.items():
        if isinstance(value, dict) and isinstance(result.get(key), dict):
            # Deep merge one level for dicts (e.g. _user, alice-book-meeting)
            merged = dict(result[key])
            merged.update(value)
            result[key] = merged
        else:
            result[key] = value
    return result


def fill_user_profile(profile_path: Path, user: dict) -> None:
    """Replace placeholder identity values in user_profile.md with real data."""
    if not profile_path.exists():
        return

    content = profile_path.read_text(encoding="utf-8")

    for field_key, (label, placeholder) in IDENTITY_FIELD_MAP.items():
        value = user.get(field_key, "").strip()
        if not value:
            continue
        # Replace "- **Label:** placeholder" with real value
        pattern = rf"(\*\*{re.escape(label)}:\*\*\s*){re.escape(placeholder)}"
        replacement = rf"\g<1>{value}"
        content = re.sub(pattern, replacement, content)

    profile_path.write_text(content, encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Alice init — write configs and copy memory templates")
    parser.add_argument("--data", required=True, help="JSON string with _user and skill-specific config")
    args = parser.parse_args()

    try:
        incoming = json.loads(args.data)
    except json.JSONDecodeError as e:
        print(f"ERROR: Invalid JSON in --data: {e}", file=sys.stderr)
        sys.exit(1)

    results = []

    # ── 1. Write / merge skill-personal.json ───────────────────────────────
    personal_path = ALICE_ROOT / "config" / "skill-personal.json"
    example_path  = ALICE_ROOT / "config" / "skill-personal.json.example"

    existing = load_json(personal_path)
    if not existing and example_path.exists():
        # Bootstrap from example so metadata keys (_readme, _usage) are preserved
        existing = load_json(example_path)

    merged = merge_personal(existing, incoming)
    write_json(personal_path, merged)
    results.append(f"✅ config/skill-personal.json written ({len(incoming)} section(s) merged)")

    # ── 2. Copy install-config.json if missing ──────────────────────────────
    install_config = ALICE_ROOT / "config" / "install-config.json"
    install_example = ALICE_ROOT / "config" / "install-config.json.example"
    if not install_config.exists() and install_example.exists():
        shutil.copy2(install_example, install_config)
        results.append("✅ config/install-config.json copied from example")
    elif not install_config.exists():
        results.append("⚠️  config/install-config.json.example not found — skipped")

    # ── 3. Copy missing memory files ────────────────────────────────────────
    memories_dir = ALICE_ROOT / "memories"
    for fname in MEMORY_FILES:
        dest = memories_dir / fname
        src  = memories_dir / f"{fname}.example"
        if dest.exists():
            results.append(f"— memories/{fname} already exists, skipped")
        elif src.exists():
            shutil.copy2(src, dest)
            results.append(f"✅ memories/{fname} copied from example")
        else:
            results.append(f"⚠️  memories/{fname}.example not found — skipped")

    # ── 4. Fill in identity fields in user_profile.md ───────────────────────
    user = incoming.get("_user", {})
    if user:
        profile_path = memories_dir / "user_profile.md"
        if profile_path.exists():
            fill_user_profile(profile_path, user)
            results.append("✅ memories/user_profile.md identity fields updated")

    # ── Summary ─────────────────────────────────────────────────────────────
    print("\nAlice init complete:\n")
    for line in results:
        print(f"  {line}")
    print()


if __name__ == "__main__":
    main()
