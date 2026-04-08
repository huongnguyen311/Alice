"""
Daily Email Recap — fetches today's inbox emails and saves a formatted recap.

Output: data/outputs/email_recap_YYYYMMDD.txt
Log:    data/email_recap_log.csv

Usage:
    python auto-scripts/daily_email_recap.py
"""

import csv
import os
from datetime import datetime, timezone
from pathlib import Path

from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build

BASE_DIR = Path(__file__).parent.parent
TOKEN_FILE = BASE_DIR / "credentials" / "google_token.json"
OUTPUTS_DIR = BASE_DIR / "data" / "outputs"
LOGS_CSV = BASE_DIR / "data" / "logs.csv"
RECAP_LOG = BASE_DIR / "data" / "email_recap_log.csv"

SCOPES = ["https://www.googleapis.com/auth/gmail.modify"]


def get_service():
    creds = Credentials.from_authorized_user_file(str(TOKEN_FILE), SCOPES)
    if creds.expired and creds.refresh_token:
        creds.refresh(Request())
        TOKEN_FILE.write_text(creds.to_json())
    return build("gmail", "v1", credentials=creds)


def already_ran_today():
    if not RECAP_LOG.exists():
        return False
    today = datetime.now().strftime("%Y-%m-%d")
    with open(RECAP_LOG, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            if row.get("date") == today and row.get("status") == "success":
                return True
    return False


def fetch_emails(service, max_results=50):
    result = service.users().messages().list(
        userId="me", q="in:inbox", maxResults=max_results
    ).execute()
    messages = result.get("messages", [])

    emails = []
    for m in messages:
        msg = service.users().messages().get(
            userId="me", messageId=m["id"], format="metadata",
            metadataHeaders=["From", "Subject", "Date"]
        ).execute()

        headers = {h["name"]: h["value"] for h in msg["payload"]["headers"]}
        snippet = msg.get("snippet", "").replace("&#39;", "'").replace("&amp;", "&").replace("&lt;", "<").replace("&gt;", ">")
        labels = msg.get("labelIds", [])

        emails.append({
            "id": m["id"],
            "from": headers.get("From", "Unknown"),
            "subject": headers.get("Subject", "(no subject)"),
            "date": headers.get("Date", ""),
            "snippet": snippet,
            "unread": "UNREAD" in labels,
        })

    return emails


def build_recap(emails, date_str):
    unread = [e for e in emails if e["unread"]]
    read = [e for e in emails if not e["unread"]]

    lines = [
        f"## Daily Email Recap — {date_str} | {len(emails)} emails ({len(unread)} unread)",
        "",
    ]

    all_sorted = unread + read
    for i, e in enumerate(all_sorted, 1):
        unread_tag = "[UNREAD] " if e["unread"] else ""
        lines.append(f"---")
        lines.append(f"**{i}. {unread_tag}From:** {e['from']}")
        lines.append(f"**Subject:** {e['subject']}")
        lines.append(f"**Preview:** {e['snippet'][:200]}")
        lines.append("")

    return "\n".join(lines)


def log_recap(email_count, status):
    RECAP_LOG.parent.mkdir(exist_ok=True)
    file_exists = RECAP_LOG.exists()
    with open(RECAP_LOG, "a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow(["date", "timestamp", "email_count", "status"])
        writer.writerow([datetime.now().strftime("%Y-%m-%d"), datetime.now().isoformat(), email_count, status])


def log_run(status, summary):
    LOGS_CSV.parent.mkdir(exist_ok=True)
    file_exists = LOGS_CSV.exists()
    with open(LOGS_CSV, "a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow(["timestamp", "script", "status", "summary"])
        writer.writerow([datetime.now().isoformat(), "daily_email_recap", status, summary])


def main():
    if already_ran_today():
        print("Already ran today — skipping.")
        return

    print("Connecting to Gmail...")
    service = get_service()

    print("Fetching inbox emails...")
    emails = fetch_emails(service, max_results=50)

    date_str = datetime.now().strftime("%d %b %Y")
    recap = build_recap(emails, date_str)

    OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)
    filename = f"email_recap_{datetime.now().strftime('%Y%m%d')}.txt"
    output_path = OUTPUTS_DIR / filename
    output_path.write_text(recap, encoding="utf-8")

    summary = f"{len(emails)} emails ({sum(1 for e in emails if e['unread'])} unread) → {output_path}"
    print(f"Done: {summary}")
    print(recap)

    log_recap(len(emails), "success")
    log_run("success", summary)


if __name__ == "__main__":
    main()
