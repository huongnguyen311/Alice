"""
Gmail — Mark All Unread Messages as Read

Uses the Google Gmail API to find all unread messages and batch-remove
the UNREAD label. Processes in batches of 1000 (API limit).

Prerequisites:
    python setup/google_auth_setup.py   # run once to generate token

Usage:
    python auto-scripts/gmail_mark_all_read.py
"""

import csv
import os
from datetime import datetime
from pathlib import Path

from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build

BASE_DIR = Path(__file__).parent.parent
TOKEN_FILE = BASE_DIR / "credentials" / "google_token.json"
LOGS_CSV = BASE_DIR / "data" / "logs.csv"

SCOPES = ["https://www.googleapis.com/auth/gmail.modify"]


def get_credentials():
    if not TOKEN_FILE.exists():
        raise FileNotFoundError(
            f"Token not found at {TOKEN_FILE}.\n"
            "Run: python setup/google_auth_setup.py"
        )
    creds = Credentials.from_authorized_user_file(str(TOKEN_FILE), SCOPES)
    if creds.expired and creds.refresh_token:
        creds.refresh(Request())
        TOKEN_FILE.write_text(creds.to_json())
    return creds


def mark_all_read(service):
    total = 0
    page_token = None

    while True:
        # Fetch up to 500 unread message IDs at a time
        kwargs = {"userId": "me", "q": "is:unread", "maxResults": 500}
        if page_token:
            kwargs["pageToken"] = page_token

        result = service.users().messages().list(**kwargs).execute()
        messages = result.get("messages", [])

        if not messages:
            break

        ids = [m["id"] for m in messages]

        # Batch-remove UNREAD label
        service.users().messages().batchModify(
            userId="me",
            body={"ids": ids, "removeLabelIds": ["UNREAD"]},
        ).execute()

        total += len(ids)
        print(f"  Marked {total} messages as read so far...")

        page_token = result.get("nextPageToken")
        if not page_token:
            break

    return total


def log_run(status, summary):
    LOGS_CSV.parent.mkdir(exist_ok=True)
    file_exists = LOGS_CSV.exists()
    with open(LOGS_CSV, "a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow(["timestamp", "script", "status", "summary"])
        writer.writerow([datetime.now().isoformat(), "gmail_mark_all_read", status, summary])


def main():
    print("Connecting to Gmail...")
    creds = get_credentials()
    service = build("gmail", "v1", credentials=creds)

    print("Searching for unread messages...")
    total = mark_all_read(service)

    summary = f"Marked {total} messages as read"
    print(f"Done: {summary}")
    log_run("success", summary)


if __name__ == "__main__":
    main()
