---
name: alice-git-sync
description: Merge the latest changes from main into your current branch via Alice — with plain-English guidance and safe auto-fixing of simple conflicts.
scope: automation
triggers:
  - "sync with main"
  - "merge main"
  - "update from main"
  - "pull from main"
  - "sync my branch"
  - "get latest changes"
  - "bring in changes from main"
  - "I'm behind main"
  - "update my branch"
---

# Skill: Git Sync (Merge main into your branch)

## When to Use

Use this skill when the user wants to bring the latest changes from `main` into their current branch. This is designed for non-developer team members who work on their own branch and need to stay up to date.

Do NOT use this skill if the user is on `main` — warn them and stop.

---

## Step 1 — Pre-flight Checks

Run all three checks before doing anything else. Stop if any fails.

### 1a — Confirm this is a git project

```bash
git rev-parse --is-inside-work-tree
```

- Returns `true` → continue
- Error → stop. Tell the user:
  > "This folder doesn't seem to be a git project. Make sure you're running this from inside your project folder and try again."

### 1b — Check which branch we're on

```bash
git branch --show-current
```

Store the result as `CURRENT_BRANCH`.

- If `CURRENT_BRANCH` is `main` or `master` → stop. Tell the user:
  > "You're currently on the `main` branch. This sync is meant to update your personal branch from main — not the other way around. Please switch to your own branch and try again. If you're not sure which branch to switch to, ask your developer."

- If `CURRENT_BRANCH` is empty (detached HEAD state) → stop. Tell the user:
  > "Your project is in an unusual state that I can't safely sync from. Please ask your developer to help before trying this again."

- Otherwise → continue. Tell the user:
  > "You're on branch **[CURRENT_BRANCH]**. I'll bring in the latest changes from main."

### 1c — Check for unsaved local changes

```bash
git status --short
```

- Output is empty → no unsaved changes, continue to Step 2
- Output has lines → warn the user. List the files. Ask in a **single message**:

  > "You have unsaved local changes in these files:
  > [list files from git status output]
  >
  > I recommend saving them before syncing — otherwise things could get complicated. What would you like to do?
  >
  > - Say **commit** to save your current work with a short note
  > - Say **stash** to set your changes aside temporarily (you can bring them back after)
  > - Say **continue anyway** to sync without saving first (not recommended)

  Handle each response:

  - **commit** → ask: "What's a short note describing your changes?" (one question, wait for answer) → run `git add -A && git commit -m "[their answer]"` → confirm: "Saved. Now syncing with main."
  - **stash** → run `git stash push -m "alice-git-sync stash before merge"` → confirm: "Changes set aside. I'll remind you to bring them back after the sync."  
    Set a flag: `STASHED=true`
  - **continue anyway** → set a note internally that the user chose to proceed with unsaved changes, then continue

---

## Step 2 — Fetch and Merge

### 2a — Fetch latest from the server

```bash
git fetch origin
```

- Success → continue
- Failure → stop. Tell the user:
  > "I couldn't reach the server to get the latest changes. Check your internet connection (or VPN if your team uses one) and try again."

### 2b — Merge main into your branch

```bash
git merge origin/main
```

If this fails with "couldn't find remote ref origin/main", try:
```bash
git merge origin/master
```

If both fail → stop. Tell the user:
> "I couldn't find the main branch on the server. The branch might have an unusual name. Please ask your developer what the main branch is called."

Capture the full output. Now handle the outcome in Step 3.

---

## Step 3 — Handle the Outcome

### Case A — Clean Merge (no conflicts)

Signal: merge output contains "Already up to date." or completes with a merge commit and no "CONFLICT" lines.

Tell the user:
> "✅ All done! Your branch is now up to date with the latest changes from main."

Then show what changed:

```bash
git diff HEAD~1 HEAD --name-status
```

Format the output in plain English:

> **What came in from main:**
> - Added: [list added files, or "nothing"]
> - Updated: [list modified files, or "nothing"]
> - Removed: [list deleted files, or "nothing"]
>
> *(If the output is empty: "Your branch was already up to date — no changes came in.")*

Then go to Step 4.

---

### Case B — Conflicts Detected

Signal: merge output contains "CONFLICT" or git exits with non-zero status.

Tell the user:
> "❌ Some files had conflicting changes when I tried to sync. That means both your branch and main changed the same part of a file. Let me take a look at each one."

Get the list of conflicted files:

```bash
git diff --name-only --diff-filter=U
```

For each conflicted file, run through the classification and resolution steps below.

---

#### Step 3B-i — Read the conflict

Read the file content. Look for conflict markers: `<<<<<<<`, `=======`, `>>>>>>>`.

The section between `<<<<<<<` and `=======` is what's on **your branch**.  
The section between `=======` and `>>>>>>>` is what's on **main**.

---

#### Step 3B-ii — Classify the conflict

Apply this table top-to-bottom. Stop at the first matching rule.

| Condition | Classification |
|---|---|
| File is a binary file (image, PDF, compiled asset, etc.) | **Escalate** |
| File path contains `credentials/` | **Escalate** |
| File name is `.env`, or matches `*.env`, `*.secret`, `*.key`, `*.pem` | **Escalate** |
| File path is `config/skill-personal.json` | **Escalate** |
| File path contains any of: `auth`, `login`, `permission`, `payment`, `billing`, `migration`, `schema` | **Escalate** |
| Both sides modify the same function, method, or logic block (overlapping, not just nearby) | **Escalate** |
| Alice is unsure what either side's change means or does | **Escalate** |
| Both sides add different lines with **no shared lines** in the conflict zone (purely additive) | **Safe: keep both sides** |
| Entire conflict zone is inside a comment block or documentation string | **Safe: keep main's version** |
| Conflict is a non-functional value only — a label, display name, version number, or description string — with no logic impact | **Safe: keep main's version** |

**Default rule: when in doubt, escalate. Never guess on logic changes.**

---

#### Step 3B-iii — Apply safe fixes

For each file classified as **safe**:

1. Remove the conflict markers.
2. For "keep both sides": include all lines from both the your-branch section and the main section.
3. For "keep main's version": use the lines from the `=======` → `>>>>>>>` section only.
4. Write the resolved content back to the file.
5. Run `git add <filename>` to mark it resolved.

Record what you did for the report.

---

#### Step 3B-iv — Report results

After processing all conflicted files, present the full report:

```
## Sync Results for [CURRENT_BRANCH]

**Auto-fixed** ✅
| File | What I did |
|---|---|
| [filename] | [plain English description, e.g. "Kept changes from both sides — each added different items"] |

**Needs your developer's help** ❌
| File | Why |
|---|---|
| [filename] | [plain English reason, e.g. "Touches login code — too risky to change automatically"] |
```

If all conflicts were auto-fixed (no escalations), skip the ❌ section.
If all conflicts need escalation (nothing auto-fixed), skip the ✅ section.

Then add **next steps**:

**If there are escalated files:**

> **What to do next:**
> 1. Copy this message and send it to your developer:
>    > "I tried to sync my branch **[CURRENT_BRANCH]** with main and need help resolving conflicts in: [list escalated files]. Can you take a look?"
> 2. Once they've fixed the files, come back and say **finish sync** and I'll complete it.
> 3. Or if you'd rather cancel the whole sync and go back to before, say **cancel sync**.

**If all conflicts were auto-fixed:**

> "All conflicts were fixed automatically. Say **finish sync** to complete the merge."

---

#### Step 3B-v — Handle follow-up commands

- User says **finish sync** → run `git merge --continue` (or `git commit --no-edit` if needed) → confirm: "✅ Sync complete!" → go to Step 4
- User says **cancel sync** → run `git merge --abort` → confirm: "Sync cancelled. Your branch is back to exactly how it was before."
- Merge already in progress when skill loads (detect via presence of `MERGE_HEAD` file in `.git/`) → tell the user:
  > "It looks like a previous sync didn't finish. Say **cancel sync** to undo it and start fresh, or tell me what happened and I'll help you figure out the next step."

---

## Step 4 — Stash Reminder

If `STASHED=true` (user stashed changes in Step 1c) and the merge is complete, remind the user:

> "Your changes that I set aside earlier are ready to bring back. Say **unstash** to restore them."

If the user says **unstash**:

```bash
git stash pop
```

- Success → confirm: "Your changes are back. All done!"
- Produces new conflicts → tell the user:
  > "Bringing your changes back created a new conflict in: [files]. This means those files were changed in both your stashed work and in main. Please ask your developer to help review: [files]."

---

## Language Rules

- Never use raw git terms in explanations without translating them:
  - "commit" → "save your work"
  - "stash" → "set your changes aside temporarily"
  - "merge" → "sync" or "bring in changes from main"
  - "origin" → "the server" or "the remote"
  - "HEAD" → omit or say "your current state"
  - Exception: code blocks shown to the user for developer handoff may use real git commands
- Always batch all clarifying questions into a single message — never ask one field at a time
- ✅ for success, ❌ for failures or items needing attention
- Keep confirmations short and one-line where possible

---

## Edge Cases

| Situation | Handling |
|---|---|
| `origin/main` not found, `origin/master` also not found | Stop + tell user to ask developer for main branch name |
| Binary file conflict | Always escalate — cannot be safely merged as text |
| All conflicts escalated, nothing auto-fixed | Show only the ❌ section + escalation message |
| All conflicts auto-fixed, nothing escalated | Show only the ✅ section + "finish sync" prompt |
| Merge already in progress on entry | Detect `MERGE_HEAD` in `.git/` → offer cancel or explain |
| Detached HEAD state | Detected in Step 1b → stop + ask user to get developer help |
| `git stash pop` causes new conflicts after sync | Escalate those files to developer separately |
