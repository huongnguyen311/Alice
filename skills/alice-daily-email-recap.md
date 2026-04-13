---
name: alice-daily-email-recap
description: Run Alice's daily email recap script to fetch and summarise today's Gmail inbox emails
scope: email
triggers:
  - "email recap"
  - "inbox summary"
  - "daily digest"
  - "what emails"
  - "show me emails"
  - "unread emails"
script: "{ALICE_ROOT}/auto-scripts/daily_email_recap.py"
---

# Skill: Daily Email Recap

## What This Does

Fetches today's Gmail inbox via the Google API, formats a summary (unread first), saves output to `{ALICE_ROOT}/data/outputs/email_recap_YYYYMMDD.txt`, and logs the run.

Gmail account: `{USER_EMAIL}` (timezone: `{USER_TIMEZONE}`)

Runs automatically at 08:32 daily via the system scheduler — this skill is for on-demand runs or checking output from another project.

---

## Execution Steps

1. **Run the script:**
   ```
   python {ALICE_ROOT}/auto-scripts/daily_email_recap.py
   ```

2. **Read and display the output:**
   ```
   {ALICE_ROOT}/data/outputs/email_recap_YYYYMMDD.txt
   ```
   Replace `YYYYMMDD` with today's date.

---

## Script Behaviour

1. **Once-per-day guard** — checks `{ALICE_ROOT}/data/email_recap_log.csv`. If today already has a `success` entry, skips the fetch and returns the cached output file.
2. **Fetch inbox** — Gmail API, `in:inbox`, maxResults 50.
3. **Format recap** — unread emails first, then read. Each entry: From, Subject, 200-char preview.
4. **Save output** — `{ALICE_ROOT}/data/outputs/email_recap_YYYYMMDD.txt`
5. **Log run** — appends to `{ALICE_ROOT}/data/email_recap_log.csv` and `{ALICE_ROOT}/data/logs.csv`

---

## Output Format

```
## Daily Email Recap — [DD MMM YYYY] | [N] emails ([N] unread)

---
**1. [UNREAD] From:** Name <email>
**Subject:** subject line
**Preview:** first 200 chars of email body

---
**2. From:** Name <email>
...
```

---

## Files

| File | Purpose |
|---|---|
| `{ALICE_ROOT}/auto-scripts/daily_email_recap.py` | The script |
| `{ALICE_ROOT}/data/outputs/email_recap_YYYYMMDD.txt` | Daily output |
| `{ALICE_ROOT}/data/email_recap_log.csv` | Run log (once-per-day guard) |
| `{ALICE_ROOT}/credentials/google_token.json` | Auth token (auto-refreshes) |

---

## Scheduling Setup

To schedule this script to run automatically every day, see the platform-specific setup guides:

- **Windows:** `setup/SETUP-WINDOWS.md` — Windows Task Scheduler section
- **Mac/Linux:** `setup/SETUP-MAC.md` — cron / launchd section
