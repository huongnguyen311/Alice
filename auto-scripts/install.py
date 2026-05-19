#!/usr/bin/env python3
"""
Install Alice skills as personal global Claude Code skills at ~/.claude/skills/.

Config: auto-scripts/install-config.json (gitignored, copy from install-config.json.example)

Install behaviour:
  - Every skill is installed as a copy (not a symlink) so each installed
    SKILL.md carries Alice marker keys in its frontmatter.
  - {ALICE_ROOT} and personal tokens are substituted at install time —
    the installed copy contains the resolved absolute paths and identity.
  - After token substitution, three marker lines are injected into the
    frontmatter of every installed SKILL.md:
        x-alice-managed: true
        x-alice-source: <this Alice repo's absolute path>
        x-alice-installed-at: <ISO 8601 timestamp>
    These keys are ignored by Claude Code's skill loader but allow tooling
    (and humans) to identify and clean up Alice-managed installs.
  - Editing a source skill no longer reflects immediately in ~/.claude/skills/
    — re-run install.py to update.

Cleanup:
  Pass 1 (manifest-based): removes dirs that were in the previous manifest
    but are no longer in the current config.
  Pass 2 (marker-based):   scans ~/.claude/skills/ for dirs whose SKILL.md
    has x-alice-managed=true AND x-alice-source matching this Alice install,
    but whose name is no longer in the current config. Catches orphans that
    survived a missing/stale manifest.

Cross-platform:
  - pathlib for all paths — no hardcoded usernames or directories
  - copy-only install path works identically on Mac, Linux, and Windows

Run directly: python auto-scripts/install.py
Or via Alice: say "install alice skills"
"""

import json
import os
import platform
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ALICE_ROOT = Path(__file__).parent.parent.resolve()
CLAUDE_SKILLS = Path.home() / ".claude" / "skills"
MANIFEST_PATH = ALICE_ROOT / "data" / "install-manifest.json"
CONFIG_PATH = ALICE_ROOT / "config" / "install-config.json"
CONFIG_EXAMPLE_PATH = ALICE_ROOT / "config" / "install-config.json.example"
PERSONAL_PATH = ALICE_ROOT / "config" / "skill-personal.json"
PERSONAL_EXAMPLE_PATH = ALICE_ROOT / "config" / "skill-personal.json.example"


def ensure_venv() -> None:
    """Create .venv at ALICE_ROOT if it doesn't exist, then re-exec inside it."""
    # Windows: Scripts/python.exe; Unix: bin/python
    if platform.system() == "Windows":
        venv_python = ALICE_ROOT / ".venv" / "Scripts" / "python.exe"
    else:
        venv_python = ALICE_ROOT / ".venv" / "bin" / "python"
    if not venv_python.exists():
        print(f"Creating venv at {ALICE_ROOT / '.venv'} ...")
        subprocess.run([sys.executable, "-m", "venv", str(ALICE_ROOT / ".venv")], check=True)
        print("Venv created.\n")
    # Re-exec with venv Python if we're not already inside it
    if Path(sys.executable).resolve() != venv_python.resolve():
        if platform.system() == "Windows":
            # os.execv doesn't work reliably on Windows — use subprocess + exit
            result = subprocess.run([str(venv_python)] + sys.argv)
            sys.exit(result.returncode)
        else:
            os.execv(str(venv_python), [str(venv_python)] + sys.argv)


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _load_config() -> dict:
    """Load install-config.json. Falls back to example if missing. Returns full config dict."""
    path = CONFIG_PATH if CONFIG_PATH.exists() else CONFIG_EXAMPLE_PATH
    if not path.exists():
        print("ERROR: No install-config.json or install-config.json.example found.")
        print(f"Expected at: {CONFIG_PATH}")
        raise SystemExit(1)
    if path == CONFIG_EXAMPLE_PATH:
        print(f"Note: install-config.json not found — using example config ({CONFIG_EXAMPLE_PATH.name})")
        print(f"      Copy it to install-config.json to personalise: cp {CONFIG_EXAMPLE_PATH} {CONFIG_PATH}\n")
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def _skills_from_config(config: dict) -> list[dict]:
    """Extract enabled skill entries from config."""
    return [
        s for s in config.get("skills", [])
        if not s.get("name", "").startswith("_") and s.get("enabled", True)
    ]


def _load_previous_manifest() -> list[dict]:
    """Return the skills list from the previous manifest, or [] if none exists."""
    if not MANIFEST_PATH.exists():
        return []
    try:
        with open(MANIFEST_PATH, encoding="utf-8") as f:
            return json.load(f).get("skills", [])
    except (json.JSONDecodeError, OSError):
        return []


def _safely_remove_skill_dir(name: str, skill_dir: Path) -> dict:
    """
    Remove a single ~/.claude/skills/<name>/ dir with strict safety:
      - Skip if dir doesn't exist (ALREADY_GONE)
      - Skip if dir is outside CLAUDE_SKILLS (defends against tampered input)
      - Skip if dir contains anything other than SKILL.md (preserves manual files)
    Returns a result dict suitable for joining into the caller's results list.
    """
    if not skill_dir.exists():
        return {"name": name, "status": "ALREADY_GONE"}

    try:
        skill_dir.resolve().relative_to(CLAUDE_SKILLS.resolve())
    except ValueError:
        return {"name": name, "status": "SKIPPED",
                "reason": f"dir outside {CLAUDE_SKILLS}: {skill_dir}"}

    entries = list(skill_dir.iterdir())
    unexpected = [p.name for p in entries if p.name != "SKILL.md"]
    if unexpected:
        return {"name": name, "status": "SKIPPED",
                "reason": f"contains unexpected files: {', '.join(unexpected)}"}

    try:
        skill_md = skill_dir / "SKILL.md"
        if skill_md.exists() or skill_md.is_symlink():
            skill_md.unlink()
        skill_dir.rmdir()
        return {"name": name, "status": "PRUNED", "dir": str(skill_dir)}
    except OSError as e:
        return {"name": name, "status": "ERROR", "reason": str(e)}


def _prune_orphans(previous: list[dict], current_names: set[str]) -> list[dict]:
    """
    Pass 1 — manifest-based prune.
    Remove ~/.claude/skills/<name>/ for skills in the previous manifest but no
    longer in the current config (deleted entries or enabled:false flips).
    """
    results = []
    for entry in previous:
        name = entry.get("name")
        if not name or name in current_names:
            continue
        skill_dir = Path(entry.get("dir") or (CLAUDE_SKILLS / name))
        results.append(_safely_remove_skill_dir(name, skill_dir))
    return results


def _prune_unmarked_orphans(current_names: set[str], alice_root: Path) -> list[dict]:
    """
    Pass 2 — marker-based filesystem scan.
    Walk ~/.claude/skills/ and prune dirs whose SKILL.md has x-alice-managed=true
    AND x-alice-source matches this alice_root, but whose name is no longer in
    the current config.

    Catches orphans that survived a missing/stale manifest. Will NOT touch:
      - dirs without the marker (could be anything)
      - dirs marked by a different Alice install (different x-alice-source)
      - dirs whose name is still in the current config
      - dirs containing files other than SKILL.md (manual content)
    """
    if not CLAUDE_SKILLS.exists():
        return []

    alice_root_str = str(alice_root)
    results = []
    seen_names = set()
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
        marker_name = marker.get("name") or child.name
        if marker_name in current_names:
            continue
        if marker_name in seen_names:
            continue  # belt and braces — never report the same name twice
        seen_names.add(marker_name)

        results.append(_safely_remove_skill_dir(marker_name, child))
    return results


def _load_personal() -> dict:
    """
    Load skill-personal.json for personal token substitution.
    Falls back to the example file with a notice if missing.
    Returns the raw dict (keyed by skill name).
    """
    path = PERSONAL_PATH if PERSONAL_PATH.exists() else PERSONAL_EXAMPLE_PATH
    if not path.exists():
        return {}
    if path == PERSONAL_EXAMPLE_PATH:
        print(f"Note: config/skill-personal.json not found — personal tokens will use example values")
        print(f"      Copy and fill in: cp {PERSONAL_EXAMPLE_PATH} {PERSONAL_PATH}\n")
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    # Strip comment-only metadata keys; preserve _user (functional identity data)
    METADATA_KEYS = {"_readme", "_usage"}
    return {k: v for k, v in data.items() if k not in METADATA_KEYS}


def _build_contacts_table(contacts: list[dict]) -> str:
    """Render the contacts list as a Markdown table for insertion into skill files."""
    lines = ["| Name | Email |", "|---|---|"]
    for c in contacts:
        name = c.get("name", "")
        email = c.get("email", "")
        note = c.get("note", "")
        display = f"{name} ({note})" if note else name
        lines.append(f"| {display} | {email} |")
    return "\n".join(lines)


def _apply_tokens(content: str, skill_name: str, personal: dict) -> str:
    """
    Substitute all tokens in skill file content:
      {ALICE_ROOT}               → resolved absolute Alice root path
      {USER_NAME}                → user's full name (from _user section)
      {USER_EMAIL}               → user's email address
      {USER_TIMEZONE}            → user's timezone (e.g. Asia/Ho_Chi_Minh)
      {USER_ROLE}                → user's job role/title
      {USER_ORG}                 → user's organization/company
      {USER_LOCATION}            → user's city/country
      {USER_LANGUAGE}            → user's preferred language code
      {CONTACTS}                 → Markdown contacts table from skill-personal.json
      {TIMEZONE}                 → timezone string (deprecated — use {USER_TIMEZONE})
      {MEETING_DURATION_HOURS}   → default meeting duration
      {ADD_GOOGLE_MEET_FOR_EXTERNAL} → true/false string
    """
    content = content.replace("{ALICE_ROOT}", str(ALICE_ROOT))

    # Global user identity tokens — applied to all skills
    user = personal.get("_user", {})
    if user:
        content = content.replace("{USER_NAME}",     user.get("name",         ""))
        content = content.replace("{USER_EMAIL}",    user.get("email",        ""))
        content = content.replace("{USER_TIMEZONE}", user.get("timezone",     "UTC"))
        content = content.replace("{USER_ROLE}",     user.get("role",         ""))
        content = content.replace("{USER_ORG}",      user.get("organization", ""))
        content = content.replace("{USER_LOCATION}", user.get("location",     ""))
        content = content.replace("{USER_LANGUAGE}", user.get("language",     "en"))

    skill_personal = personal.get(skill_name, {})
    if skill_personal:
        contacts = skill_personal.get("contacts", [])
        if contacts:
            content = content.replace("{CONTACTS}", _build_contacts_table(contacts))

        timezone = skill_personal.get("timezone", "UTC")
        content = content.replace("{TIMEZONE}", timezone)

        duration = str(skill_personal.get("default_duration_hours", 1))
        content = content.replace("{MEETING_DURATION_HOURS}", duration)

        add_meet = str(skill_personal.get("add_google_meet_for_external", True)).lower()
        content = content.replace("{ADD_GOOGLE_MEET_FOR_EXTERNAL}", add_meet)

    return content


ALICE_MARKER_KEYS = ("x-alice-managed", "x-alice-source", "x-alice-installed-at")


def _inject_alice_markers(content: str, alice_root: Path, installed_at: str) -> str:
    """
    Add x-alice-managed / x-alice-source / x-alice-installed-at to the
    installed SKILL.md's frontmatter, right before the closing `---`.

    If the source somehow already contained any of these keys, the existing
    lines are stripped first so the install-time values always win.
    """
    if not content.startswith("---\n"):
        # No frontmatter — prepend a minimal one with just the markers.
        marker_block = "---\n" + _marker_lines(alice_root, installed_at) + "---\n"
        return marker_block + content

    end_idx = content.find("\n---", 4)
    if end_idx == -1:
        # Malformed frontmatter — give up and return content unchanged rather
        # than corrupt the file.
        return content

    head = content[: end_idx + 1]   # includes everything up to (and incl.) the \n before closing ---
    tail = content[end_idx + 1 :]   # starts with '---' line and continues with body

    # Strip any pre-existing marker lines from the frontmatter
    head_lines = head.splitlines(keepends=True)
    head_lines = [
        line for line in head_lines
        if not any(line.lstrip().startswith(f"{k}:") for k in ALICE_MARKER_KEYS)
    ]
    head = "".join(head_lines)
    if not head.endswith("\n"):
        head += "\n"

    return head + _marker_lines(alice_root, installed_at) + tail


def _marker_lines(alice_root: Path, installed_at: str) -> str:
    """Return the three marker lines (trailing newline included) as a single string."""
    return (
        f"x-alice-managed: true\n"
        f"x-alice-source: {alice_root}\n"
        f"x-alice-installed-at: {installed_at}\n"
    )


def _read_skill_marker(skill_md_path: Path) -> dict | None:
    """
    Read the frontmatter of an installed SKILL.md and extract Alice marker
    info plus the skill name. Returns None if the file doesn't exist, has
    no frontmatter, or is missing the x-alice-managed marker.

    Returned dict shape: {"name": str, "x-alice-source": str, "x-alice-managed": bool}
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


def _install_skill(skill: dict, personal: dict, installed_at: str) -> dict:
    """Install one skill as a copy with Alice markers baked into the frontmatter.

    All installs are copies (no symlinks) so every installed SKILL.md carries
    the x-alice-* markers — making the install identifiable and orphan-detectable
    regardless of manifest state.
    """
    name = skill["name"]
    source_orig = ALICE_ROOT / "skills" / skill["file"]
    skill_dir = CLAUDE_SKILLS / name
    dest = skill_dir / "SKILL.md"

    if not source_orig.exists():
        return {"status": "ERROR", "reason": f"Source file not found: {source_orig}"}

    raw = source_orig.read_text(encoding="utf-8")

    # Remove any prior install (copy or symlink) — we always re-generate
    if dest.exists() or dest.is_symlink():
        dest.unlink()

    skill_dir.mkdir(parents=True, exist_ok=True)

    # Apply token substitutions then inject Alice marker keys before the
    # closing --- of the frontmatter.
    resolved = _apply_tokens(raw, name, personal)
    resolved = _inject_alice_markers(resolved, ALICE_ROOT, installed_at)
    dest.write_text(resolved, encoding="utf-8")

    if not dest.exists():
        return {
            "status": "ERROR",
            "reason": "File does not exist after install (write failed)",
        }

    return {"status": "OK", "method": "copy", "dest": str(dest)}



GLOBAL_CLAUDE_JSON = Path.home() / ".claude.json"


def sync_global_mcp() -> None:
    """Merge Alice's .mcp.json servers into ~/.claude.json as global MCPs."""
    mcp_source = ALICE_ROOT / ".mcp.json"
    if not mcp_source.exists():
        print("  [SKIPPED]          .mcp.json not found — skipping global MCP sync")
        return

    alice_mcps = json.loads(mcp_source.read_text(encoding="utf-8")).get("mcpServers", {})
    if not alice_mcps:
        print("  [SKIPPED]          No MCP servers in .mcp.json")
        return

    # Load existing ~/.claude.json (may have many other keys — preserve them all)
    claude_json = json.loads(GLOBAL_CLAUDE_JSON.read_text(encoding="utf-8")) if GLOBAL_CLAUDE_JSON.exists() else {}
    existing = claude_json.get("mcpServers", {})

    added, updated = [], []
    for name, cfg in alice_mcps.items():
        if name not in existing:
            added.append(name)
        elif existing[name] != cfg:
            updated.append(name)
        existing[name] = cfg

    claude_json["mcpServers"] = existing
    GLOBAL_CLAUDE_JSON.write_text(json.dumps(claude_json, indent=2) + "\n", encoding="utf-8")

    for name in added:
        print(f"  [OK]               MCP '{name}' added to ~/.claude.json (global)")
    for name in updated:
        print(f"  [OK]               MCP '{name}' updated in ~/.claude.json (global)")
    if not added and not updated:
        print(f"  [OK]               Global MCP already up to date")


def main():
    ensure_venv()
    config = _load_config()
    skills = _skills_from_config(config)
    personal = _load_personal()
    previous_manifest_skills = _load_previous_manifest()

    print(f"Alice install — target: {CLAUDE_SKILLS}")
    print(f"Config:        {CONFIG_PATH if CONFIG_PATH.exists() else CONFIG_EXAMPLE_PATH}")
    print(f"Personal:      {PERSONAL_PATH if PERSONAL_PATH.exists() else str(PERSONAL_EXAMPLE_PATH) + ' (example)'}\n")

    CLAUDE_SKILLS.mkdir(parents=True, exist_ok=True)
    MANIFEST_PATH.parent.mkdir(parents=True, exist_ok=True)

    now = _now()
    manifest_skills = []

    for skill in skills:
        result = _install_skill(skill, personal, now)
        status = result["status"]

        display_status = "WARN" if (skill.get("warning") and status in ("OK", "ALREADY_INSTALLED")) else status
        label = f"[{display_status}]".ljust(18)

        print(f"  {label} {skill['name']}", end="")
        if skill.get("mcp_required"):
            print(f"  (mcp: {skill['mcp_required']})", end="")
        if skill.get("type") == "python":
            print(f"  (python — paths rewritten to absolute)", end="")
        if skill.get("warning") and display_status == "WARN":
            print(f"\n               ^ {skill['warning']}", end="")
        if status in ("SKIPPED", "ERROR"):
            print(f"\n               ! {result.get('reason', '')}", end="")
        print()

        manifest_skills.append({
            "name": skill["name"],
            "file": skill["file"],
            "type": skill.get("type", "mcp"),
            "source": str(ALICE_ROOT / "skills" / skill["file"]),
            "link": str(CLAUDE_SKILLS / skill["name"] / "SKILL.md"),
            "dir": str(CLAUDE_SKILLS / skill["name"]),
            "method": result.get("method", "none"),
            "mcp_required": skill.get("mcp_required"),
            "warning": skill.get("warning"),
            "installed_at": now,
        })

    current_names = {s["name"] for s in skills}
    prune_results = _prune_orphans(previous_manifest_skills, current_names)
    if prune_results:
        print("\nPruning orphans (removed/disabled in config) —")
        for r in prune_results:
            label = f"[{r['status']}]".ljust(18)
            print(f"  {label} {r['name']}", end="")
            if r.get("reason"):
                print(f"  — {r['reason']}", end="")
            print()

    # Pass 2 — marker-based scan catches orphans not in the manifest (stale or
    # deleted manifest, previous interrupted run, etc.) but only those marked
    # as installed by THIS Alice install.
    pruned_pass1_names = {r["name"] for r in prune_results if r.get("status") == "PRUNED"}
    orphan_results = _prune_unmarked_orphans(current_names, ALICE_ROOT)
    # Hide entries already reported by Pass 1 — Pass 2 will also see them mid-flight
    # if the directory hasn't been removed yet on disk (it has been, but defend anyway).
    orphan_results = [r for r in orphan_results if r["name"] not in pruned_pass1_names]
    if orphan_results:
        print("\nScanning for untracked Alice-installed orphans —")
        for r in orphan_results:
            label = "[ORPHAN-PRUNED]" if r["status"] == "PRUNED" else f"[{r['status']}]"
            label = label.ljust(18)
            print(f"  {label} {r['name']}", end="")
            if r.get("reason"):
                print(f"  — {r['reason']}", end="")
            print()

    manifest = {
        "installed_at": now,
        "alice_root": str(ALICE_ROOT),
        "skills_dir": str(CLAUDE_SKILLS),
        "platform": platform.system().lower(),
        "config": str(CONFIG_PATH if CONFIG_PATH.exists() else CONFIG_EXAMPLE_PATH),
        "skills": manifest_skills,
    }

    with open(MANIFEST_PATH, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)

    print("\nGlobal MCP sync —")
    sync_global_mcp()

    print(f"\nManifest written: {MANIFEST_PATH}")
    print(f"\nNote: These skills are now available in every project on this machine.")
    print(f"      Personal skills have HIGHER priority than project-level skills.")
    print(f"      To customise installs:      edit config/install-config.json")
    print(f"      To update personal data:    edit config/skill-personal.json")
    print(f"      To remove:                  python auto-scripts/uninstall.py")


if __name__ == "__main__":
    main()
