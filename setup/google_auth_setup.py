"""
Google OAuth Setup — generates credentials/google_token.json
Run once before using any Gmail, Calendar, or Google Sheets Python scripts.

Prerequisites:
1. Go to Google Cloud Console → APIs & Services → Credentials
2. Create an OAuth 2.0 Client ID (Desktop app)
3. Download the JSON and save it as: credentials/google_credentials.json
4. Enable Gmail API, Google Calendar API, and Google Sheets API in your project

Usage:
    python setup/google_auth_setup.py
"""

import os
from pathlib import Path

from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
import pickle

SCOPES = [
    "https://www.googleapis.com/auth/gmail.modify",
    "https://www.googleapis.com/auth/calendar",
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive.readonly",
]

BASE_DIR = Path(__file__).parent.parent
CREDENTIALS_FILE = BASE_DIR / "credentials" / "google_credentials.json"
TOKEN_FILE = BASE_DIR / "credentials" / "google_token.json"


def main():
    if not CREDENTIALS_FILE.exists():
        print(f"ERROR: Missing credentials file at {CREDENTIALS_FILE}")
        print("Download it from Google Cloud Console → APIs & Services → Credentials")
        return

    creds = None
    if TOKEN_FILE.exists():
        creds = Credentials.from_authorized_user_file(str(TOKEN_FILE), SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(str(CREDENTIALS_FILE), SCOPES)
            creds = flow.run_local_server(port=0)

        TOKEN_FILE.parent.mkdir(exist_ok=True)
        TOKEN_FILE.write_text(creds.to_json())
        print(f"Token saved to {TOKEN_FILE}")
    else:
        print(f"Token already valid at {TOKEN_FILE}")


if __name__ == "__main__":
    main()
