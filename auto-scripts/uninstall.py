#!/usr/bin/env python3
"""
Uninstall Alice skills from ~/.claude/skills/.

Primary path: reads data/install-manifest.json to know exactly what to remove.
Only removes files that Alice installed — never touches real files not recorded
in the manifest.

Fallback path: if the manifest is missing, scans ~/.claude/skills/ for SKILL.md
files with x-alice-managed=true AND x-alice-source matching THIS Alice install
(baked into the marker at install time). Catches the case where the manifest
was deleted but the installs are still on disk.

Run directly: python auto-scripts/uninstall.py
Or via Alice: say "uninstall alice skills"
"""

import json
import os
import subprocess
import sys
from pathlib import Path

ALICE_ROOT = Path(__file__).parent.parent.resolve()
CLAUDE_SKILLS = Path.home() / ".claude" / "skills"


def ensure_venv() -> None:
    """Create .venv at ALICE_ROOT if it doesn't exist, then re-exec inside it."""
    venv_python = ALICE_ROOT / ".venv" / "bin" / "python"
    if not venv_python.exists():
        print(f"Creating venv at {ALICE_ROOT / '.venv'} ...")
        subprocess.run([sys.executable, "-m", "venv", str(ALICE_ROOT / ".venv")], check=True)
        print("Venv created.\n")
    if Path(sys.executable).resolve() != venv_python.resolve():
        os.execv(str(venv_python), [str(venv_python)] + sys.argv)
MANIFEST_PATH = ALICE_ROOT / "data" / "install-manifest.json"
GLOBAL_CLAUDE_JSON = Path.home() / ".claude.json"


def _read_skill_marker(skill_md_path: Path) -> dict | None:
    """
    Read the frontmatter of an installed SKILL.md and extract Alice marker info.
    Returns None if the file is missing, has no frontmatter, or is unmarked.
    Mirrors the parser in install.py — duplicated here so uninstall.py stays
    standalone (no shared module).
    """
    try:
        content = skill_md_path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return None
    if not content.startswith("---\n"):
        return None
    end_idx = content.find("\n---", 4)
    if end_idx == -1:
        return None

    frontmatter = content[4 : end_idx + 1]
    result = {}
    for line in frontmatter.splitlines():
        stripped = line.strip()
        if ":" not in stripped:
            continue
        key, _, value = stripped.partition(":")
        key = key.strip()
        value = value.strip()
        if key == "name":
            result["name"] = value
        elif key == "x-alice-managed":
            result["x-alice-managed"] = value.lower() == "true"
        elif key == "x-alice-source":
            result["x-alice-source"] = value

    if not result.get("x-alice-managed"):
        return None
    return result


def _discover_marked_skills() -> list[dict]:
    """
    Scan ~/.claude/skills/ for skill directories whose SKILL.md has
    x-alice-managed=true AND x-alice-source matching THIS Alice install.
    Returns a list of {name, link, dir} dicts shaped like manifest entries.
    """
    if not CLAUDE_SKILLS.exists():
        return []
    alice_root_str = str(ALICE_ROOT)
    found = []
    for child in CLAUDE_SKILLS.iterdir():
        if not child.is_dir():
            continue
        skill_md = child / "SKILL.md"
        if not skill_md.exists():
            continue
        marker = _read_skill_marker(skill_md)
        if not marker:
            continue
        if marker.get("x-alice-source") != alice_root_str:
            continue
        found.append({
            "name": marker.get("name") or child.name,
            "link": str(skill_md),
            "dir": str(child),
            "method": "copy",  # all marker-bearing installs are copies post-v2
        })
    return found


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
    ensure_venv()

    manifest_missing = not MANIFEST_PATH.exists()
    if manifest_missing:
        print("No install manifest found at data/install-manifest.json.")
        print(f"Falling back to marker scan of {CLAUDE_SKILLS}/ ...")
        skills = _discover_marked_skills()
        if not skills:
            print("No Alice-marked skills found on disk. Nothing to uninstall.")
            sys.exit(0)
        print(f"Found {len(skills)} marked skill(s) belonging to this Alice install ({ALICE_ROOT}).\n")
    else:
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

    # Delete the manifest (only if it existed at the start of this run)
    if MANIFEST_PATH.exists():
        MANIFEST_PATH.unlink()
        print(f"\nManifest deleted: {MANIFEST_PATH}")
    elif manifest_missing:
        print(f"\n(No manifest existed; uninstall driven by marker scan.)")
    print("Alice's skill source files in skills/ are untouched.")


if __name__ == "__main__":
    main()
