#!/usr/bin/env python3
"""
Uninstall Alice skills from ~/.claude/skills/.

Reads data/install-manifest.json to know exactly what to remove.
Only removes symlinks or copies that Alice installed — never touches real files
not recorded in the manifest.

Run directly: python auto-scripts/uninstall.py
Or via Alice: say "uninstall alice skills"
"""

import json
import os
import sys
from pathlib import Path

ALICE_ROOT = Path(__file__).parent.parent.resolve()
MANIFEST_PATH = ALICE_ROOT / "data" / "install-manifest.json"


def main():
    if not MANIFEST_PATH.exists():
        print("No install manifest found at data/install-manifest.json.")
        print("Nothing to uninstall. If you installed skills manually, remove them from ~/.claude/skills/ by hand.")
        sys.exit(0)

    with open(MANIFEST_PATH) as f:
        try:
            manifest = json.load(f)
        except json.JSONDecodeError as e:
            print(f"Manifest is corrupt: {e}")
            print(f"Inspect manually: {MANIFEST_PATH}")
            sys.exit(1)

    skills = manifest.get("skills", [])
    if not skills:
        print("Manifest contains no skills. Deleting empty manifest.")
        MANIFEST_PATH.unlink()
        sys.exit(0)

    print(f"Alice uninstall — removing {len(skills)} skill(s) from {manifest.get('skills_dir', '~/.claude/skills')}\n")

    for skill in skills:
        name = skill["name"]
        link_path = Path(skill["link"])
        dir_path = Path(skill["dir"])
        method = skill.get("method", "symlink")

        print(f"  {name}", end="")

        # Remove the SKILL.md file (symlink or copy)
        if link_path.is_symlink():
            os.unlink(link_path)
            print(f"  — removed symlink", end="")
        elif link_path.exists():
            if method == "copy":
                os.remove(link_path)
                print(f"  — removed copy", end="")
            else:
                # Exists as a real file but manifest says symlink — skip, warn
                print(f"  — SKIPPED (real file, not a symlink — remove {link_path} manually)", end="")
                print()
                continue
        else:
            print(f"  — already gone (skipped)", end="")

        # Remove the parent directory if now empty
        if dir_path.is_dir():
            remaining = list(dir_path.iterdir())
            if not remaining:
                dir_path.rmdir()
                print(f"  — dir removed", end="")
            else:
                print(f"  — dir kept (still has: {[f.name for f in remaining]})", end="")

        print()

    # Delete the manifest
    MANIFEST_PATH.unlink()
    print(f"\nManifest deleted: {MANIFEST_PATH}")
    print("Alice's skill source files in skills/ are untouched.")


if __name__ == "__main__":
    main()
