#!/usr/bin/env python3
"""
Install Alice skills as personal global Claude Code skills at ~/.claude/skills/.

Config: auto-scripts/install-config.json (gitignored, copy from install-config.json.example)

Skill types:
  mcp    — pure MCP skill, installed as symlink (or copy on Windows)
  python — skill uses {ALICE_ROOT} tokens; install substitutes the resolved
            absolute path and writes a copy so it works from any project CWD

Both types use the same source skill file — no duplicate sections, no fences.
The only difference is that python skills get {ALICE_ROOT} substituted at
install time and are stored as copies (not symlinks) so the resolved paths
are baked into the installed file.

Cross-platform:
  - pathlib for all paths — no hardcoded usernames or directories
  - mcp: Mac/Linux symlinks; Windows falls back to copy
  - python: always a copy (symlink would leave {ALICE_ROOT} unresolved)

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


def _install_skill(skill: dict, personal: dict) -> dict:
    """Install one skill. Returns a result dict with status, method, and type."""
    name = skill["name"]
    skill_type = skill.get("type", "mcp")
    source_orig = ALICE_ROOT / "skills" / skill["file"]
    skill_dir = CLAUDE_SKILLS / name
    dest = skill_dir / "SKILL.md"

    if not source_orig.exists():
        return {"status": "ERROR", "reason": f"Source file not found: {source_orig}"}

    # Determine if this skill needs token substitution (personal data or ALICE_ROOT)
    raw = source_orig.read_text(encoding="utf-8")
    USER_TOKENS = ("USER_NAME", "USER_EMAIL", "USER_TIMEZONE", "USER_ROLE", "USER_ORG", "USER_LOCATION", "USER_LANGUAGE")
    SKILL_TOKENS = ("CONTACTS", "TIMEZONE", "MEETING_DURATION_HOURS", "ADD_GOOGLE_MEET_FOR_EXTERNAL")
    needs_substitution = (
        "{ALICE_ROOT}" in raw
        or any(f"{{{t}}}" in raw for t in USER_TOKENS + SKILL_TOKENS)
    )

    # Skills with tokens must be installed as copies (tokens baked in at install time).
    # Pure MCP skills with no tokens can be symlinked.
    install_as_copy = (skill_type == "python") or needs_substitution

    # Idempotency checks
    if install_as_copy:
        # Always re-generate copies to pick up config changes
        if dest.exists() or dest.is_symlink():
            dest.unlink()
    else:
        # Symlink: check if already correctly linked
        if dest.is_symlink():
            if dest.resolve() == source_orig.resolve():
                return {"status": "ALREADY_INSTALLED", "method": "symlink", "dest": str(dest)}
            dest.unlink()  # wrong target — re-link
        elif dest.exists():
            return {
                "status": "SKIPPED",
                "reason": "SKILL.md exists as a real file (not a symlink) — remove manually to reinstall",
            }

    skill_dir.mkdir(parents=True, exist_ok=True)

    if install_as_copy:
        # Apply all token substitutions ({ALICE_ROOT} + personal tokens), write as copy
        resolved = _apply_tokens(raw, name, personal)
        dest.write_text(resolved, encoding="utf-8")
        method = "copy"
    else:
        # No tokens — symlink preferred, copy fallback (Windows without Dev Mode)
        method = "symlink"
        try:
            dest.symlink_to(source_orig)
        except (OSError, NotImplementedError):
            shutil.copy2(source_orig, dest)
            method = "copy"

    if not dest.exists():
        return {
            "status": "ERROR",
            "reason": "File does not exist after install (broken symlink or copy failed)",
        }

    return {"status": "OK", "method": method, "dest": str(dest)}



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

    print(f"Alice install — target: {CLAUDE_SKILLS}")
    print(f"Config:        {CONFIG_PATH if CONFIG_PATH.exists() else CONFIG_EXAMPLE_PATH}")
    print(f"Personal:      {PERSONAL_PATH if PERSONAL_PATH.exists() else str(PERSONAL_EXAMPLE_PATH) + ' (example)'}\n")

    CLAUDE_SKILLS.mkdir(parents=True, exist_ok=True)
    MANIFEST_PATH.parent.mkdir(parents=True, exist_ok=True)

    now = _now()
    manifest_skills = []

    for skill in skills:
        result = _install_skill(skill, personal)
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
