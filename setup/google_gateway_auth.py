"""
Google Docs/Sheets auth via the easy-auth gateway (token broker).

One-time consent flow. Replaces the old desktop-OAuth path for Sheets — you no
longer need a Google client_secret on this machine. The gateway holds it
server-side; you only hold a gate credential (clientId/clientSecret) and the
resulting refresh_token.

Writes the token file used by the Python Google Sheets skill:
  - credentials/google_token.json  → google-api-python-client

Prerequisites:
  1. cp credentials/gateway-config.json.example credentials/gateway-config.json
  2. Fill in base_url / client_id / client_secret (from the gateway operator)

Usage:
    python setup/google_gateway_auth.py

NOTE: Gmail/Calendar Python scripts still use setup/google_auth_setup.py and
credentials/google_token.json's *desktop* flow — this script is Sheets/Docs only.
See setup/google-gateway-INTEGRATION.md for the gateway protocol.
"""

import importlib.util
import json
import subprocess
import sys
import webbrowser
from pathlib import Path

if importlib.util.find_spec("requests") is None:
    subprocess.run([sys.executable, "-m", "pip", "install", "requests"], check=True)

import requests  # noqa: E402

sys.path.insert(0, str(Path(__file__).resolve().parent))
from gateway_tokens import load_gateway_config, write_tokens, PY_TOKEN  # noqa: E402


def _open_browser(url: str) -> None:
    try:
        if not webbrowser.open(url):
            raise RuntimeError("no browser")
    except Exception:
        # Fall back to the macOS `open` command if webbrowser can't launch one.
        try:
            subprocess.run(["open", url], check=False)
        except Exception:
            pass


def main() -> int:
    try:
        cfg = load_gateway_config()
    except (FileNotFoundError, ValueError) as e:
        print(f"ERROR: {e}")
        return 1

    base = cfg["base_url"].rstrip("/")

    # 1. Start consent.
    print("Starting consent with the gateway...")
    resp = requests.post(
        f"{base}/auth/start",
        json={"clientId": cfg["client_id"], "clientSecret": cfg["client_secret"]},
        timeout=30,
    )
    if resp.status_code != 200:
        print(f"ERROR: /auth/start failed ({resp.status_code}): {resp.text}")
        return 1

    auth_url = resp.json().get("authUrl")
    if not auth_url:
        print(f"ERROR: gateway did not return an authUrl: {resp.text}")
        return 1

    # 2. Open in browser.
    print("\nOpening the Google consent page in your browser:\n")
    print(f"  {auth_url}\n")
    _open_browser(auth_url)

    # 3. Collect the callback JSON blob (the callback page displays it).
    print("After you approve, the gateway callback page shows a JSON blob containing")
    print("your access_token / refresh_token. Copy the ENTIRE JSON and paste it below.")
    print("End the paste with an empty line (press Enter twice):\n")

    lines = []
    while True:
        try:
            line = input()
        except EOFError:
            break
        if line.strip() == "" and lines:
            break
        if line.strip():
            lines.append(line)

    raw = "\n".join(lines).strip()
    if not raw:
        print("ERROR: no JSON pasted.")
        return 1

    try:
        blob = json.loads(raw)
    except json.JSONDecodeError as e:
        print(f"ERROR: could not parse pasted JSON: {e}")
        return 1

    missing = [k for k in ("access_token", "refresh_token", "expires_at") if k not in blob]
    if missing:
        print(f"ERROR: pasted JSON is missing fields: {', '.join(missing)}")
        return 1
    blob.setdefault("scopes", [])

    # 4. Write the token file.
    write_tokens(blob)
    print("\nDone. Token written:")
    print(f"  {PY_TOKEN}   (Python Sheets skill)")
    print("\nThe refresh_token is stored durably. Future refreshes go through the")
    print("gateway automatically (setup/gateway_tokens.py refresh_via_gateway).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
