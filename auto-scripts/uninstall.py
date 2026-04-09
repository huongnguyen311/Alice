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
GLOBAL_CLAUDE_JSON = Path.home() / ".claude.json"


def remove_global_mcps() -> None:
    """
    Remove MCP servers from ~/.claude.json that were added by install.py.

    Only removes an entry if its name AND config exactly match what is currently
    in Alice's .mcp.json — so unrelated global MCPs (same name, different config)
    are never touched.
    """
    mcp_source = ALICE_ROOT / ".mcp.json"
    if not mcp_source.exists():
        print("  [SKIPPED]  .mcp.json not found — nothing to remove from ~/.claude.json")
        return

    alice_mcps = json.loads(mcp_source.read_text(encoding="utf-8")).get("mcpServers", {})
    if not alice_mcps:
        print("  [SKIPPED]  No MCP servers defined in .mcp.json")
        return

    if not GLOBAL_CLAUDE_JSON.exists():
        print("  [SKIPPED]  ~/.claude.json not found")
        return

    claude_json = json.loads(GLOBAL_CLAUDE_JSON.read_text(encoding="utf-8"))
    existing = claude_json.get("mcpServers", {})

    removed, skipped = [], []
    for name, cfg in alice_mcps.items():
        if name not in existing:
            continue
        if existing[name] == cfg:
            del existing[name]
            removed.append(name)
        else:
            # Config differs — may belong to another project; leave it
            skipped.append(name)

    if removed or skipped:
        claude_json["mcpServers"] = existing
        GLOBAL_CLAUDE_JSON.write_text(json.dumps(claude_json, indent=2) + "\n", encoding="utf-8")

    for name in removed:
        print(f"  [OK]       MCP '{name}' removed from ~/.claude.json")
    for name in skipped:
        print(f"  [SKIPPED]  MCP '{name}' config differs — not removed (may belong to another project)")
    if not removed and not skipped:
        print("  [OK]       No Alice MCPs found in ~/.claude.json (already clean)")


def main():
    if not MANIFEST_PATH.exists():
        print("No install manifest found at data/install-manifest.json.")
        print("Nothing to uninstall. If you installed skills manually, remove them from ~/.claude/skills/ by hand.")
        sys.exit(0)

    with open(MANIFEST_PATH, encoding="utf-8") as f:
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

    # Remove Alice's MCP servers from ~/.claude.json
    print("\nGlobal MCP cleanup —")
    remove_global_mcps()

    # Delete the manifest
    MANIFEST_PATH.unlink()
    print(f"\nManifest deleted: {MANIFEST_PATH}")
    print("Alice's skill source files in skills/ are untouched.")


if __name__ == "__main__":
    main()
