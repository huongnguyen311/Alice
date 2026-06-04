"""
Alice — Google Auth MCP (auth-only, project-scoped).

A tiny stdio MCP server whose ONLY job is to connect/refresh Google via the
easy-auth gateway. It NEVER calls the Sheets/Docs API — that stays in the Python
skill (skills/Google-Sheet/skill.md). This MCP exists purely to make "connect my
Google" a one-click action from inside Claude, with no copy-paste.

Tools:
  - google_auth_status()                 → is Google connected / expired / needs reconnect
  - connect_google()                     → one-click consent (localhost auto-capture)
  - finish_google_connect(callback_json) → paste fallback if the gateway can't do localhost

Auth flow (one-click):
  1. start a local http server on 127.0.0.1:<ephemeral>
  2. POST /auth/start with redirect_uri=http://127.0.0.1:<port>/callback
  3. open the Google consent page in the browser
  4. gateway 302s the token back to the local server → capture → write token file

Reuses setup/gateway_tokens.py for all token I/O — does not reimplement it.
See setup/google-gateway-INTEGRATION.md for the gateway protocol.
"""

import importlib.util
import json
import subprocess
import sys
import threading
import time
import webbrowser
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

# --- dependency guard (CLAUDE.md venv rule) --------------------------------
for _pkg, _spec in (("mcp", "mcp.server.fastmcp"), ("requests", "requests")):
    if importlib.util.find_spec(_spec) is None:
        subprocess.run([sys.executable, "-m", "pip", "install",
                        "mcp[cli]" if _pkg == "mcp" else _pkg], check=True)

import requests  # noqa: E402
from mcp.server.fastmcp import FastMCP  # noqa: E402

# Import the shared token helpers (setup/ is a sibling of mcp/).
ALICE_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ALICE_ROOT / "setup"))
import gateway_tokens as gt  # noqa: E402

mcp = FastMCP("google-auth")

CONSENT_TIMEOUT_SECONDS = 180


# ---------------------------------------------------------------------------
# Local redirect-capture server
# ---------------------------------------------------------------------------
class _CallbackHandler(BaseHTTPRequestHandler):
    # Set on the server instance before serving.
    captured: dict = None  # type: ignore

    def do_GET(self):  # noqa: N802
        parsed = urlparse(self.path)
        if not parsed.path.rstrip("/").endswith("callback"):
            self.send_response(404)
            self.end_headers()
            return
        params = parse_qs(parsed.query)
        self.server.captured = params  # type: ignore[attr-defined]
        # Success needs an access_token (refresh_token may be absent on re-consent);
        # an `error` param means the gateway reported a failure.
        ok = "access_token" in params and "error" not in params
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.end_headers()
        msg = (
            "<h2>✅ Google connected</h2><p>You can close this tab and return to Claude.</p>"
            if ok else
            "<h2>⚠️ Connection failed</h2><p>No token received. Return to Claude and retry.</p>"
        )
        self.wfile.write(f"<html><body style='font-family:sans-serif'>{msg}</body></html>"
                         .encode("utf-8"))

    def log_message(self, *args):  # silence stderr logging (corrupts stdio MCP)
        pass


# ---------------------------------------------------------------------------
# Tools
# ---------------------------------------------------------------------------
@mcp.tool()
def google_auth_status() -> str:
    """Report whether Alice's Google (Sheets/Docs) connection is live.

    Checks the stored token, and whether the gateway still accepts it. Read-only.
    """
    if not gt.PY_TOKEN.exists():
        return json.dumps({
            "connected": False,
            "reason": "no_token",
            "action": "Run connect_google to link your Google account.",
        })
    try:
        token = json.loads(gt.PY_TOKEN.read_text(encoding="utf-8"))
        scopes = token.get("scopes", [])
        # refresh_via_gateway is a no-op when valid; raises if the gateway rejects.
        refreshed = gt.refresh_via_gateway()
        return json.dumps({
            "connected": True,
            "scopes": scopes,
            "expiry": token.get("expiry"),
            "refreshed_now": refreshed,
        })
    except gt.ReauthorizeRequired:
        return json.dumps({
            "connected": False,
            "reason": "reauthorize",
            "action": "Connection lost/revoked. Run connect_google to reconnect.",
        })
    except FileNotFoundError as e:
        return json.dumps({"connected": False, "reason": "config", "action": str(e)})
    except Exception as e:  # noqa: BLE001
        return json.dumps({"connected": False, "reason": "error", "detail": str(e)})


@mcp.tool()
def connect_google() -> str:
    """Connect Alice to Google (Sheets/Docs) with one click — no copy-paste.

    Opens the Google consent page in the browser; after you click Allow the token
    is captured automatically and saved. Uses the easy-auth gateway.
    """
    try:
        cfg = gt.load_gateway_config()
    except (FileNotFoundError, ValueError) as e:
        return json.dumps({"ok": False, "error": "config", "detail": str(e)})

    base = cfg["base_url"].rstrip("/")
    server = HTTPServer(("127.0.0.1", 0), _CallbackHandler)
    server.captured = None  # type: ignore[attr-defined]
    port = server.server_address[1]
    redirect_uri = f"http://127.0.0.1:{port}/callback"

    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        resp = requests.post(
            f"{base}/auth/start",
            json={
                "clientId": cfg["client_id"],
                "clientSecret": cfg["client_secret"],
                "redirect_uri": redirect_uri,
            },
            timeout=30,
        )
        if resp.status_code != 200:
            return json.dumps({"ok": False, "error": "auth_start",
                               "status": resp.status_code, "detail": resp.text[:300]})
        start_body = resp.json()
        auth_url = start_body.get("authUrl")
        expected_state = start_body.get("state")
        if not auth_url:
            return json.dumps({"ok": False, "error": "no_auth_url",
                               "detail": "Gateway did not return authUrl."})

        webbrowser.open(auth_url)

        deadline = time.time() + CONSENT_TIMEOUT_SECONDS
        while time.time() < deadline:
            if server.captured is not None:  # type: ignore[attr-defined]
                break
            time.sleep(0.4)

        captured = server.captured  # type: ignore[attr-defined]
        if not captured:
            return json.dumps({
                "ok": False, "error": "timeout",
                "auth_url": auth_url,
                "detail": ("No response within the time limit. If the gateway does not "
                           "support a localhost redirect yet, use finish_google_connect "
                           "with the JSON shown on the callback page."),
            })

        def _one(v):
            return v[0] if isinstance(v, (list, tuple)) else v

        # Gateway reported a failure via the redirect.
        if "error" in captured:
            return json.dumps({"ok": False, "error": "gateway_error",
                               "detail": _one(captured.get("error"))})

        # CSRF guard: the returned state must match the one from /auth/start.
        returned_state = _one(captured.get("state"))
        if expected_state and returned_state != expected_state:
            return json.dumps({"ok": False, "error": "state_mismatch",
                               "detail": "Returned state did not match /auth/start."})

        blob = gt.build_blob_from_params(captured)
        gt.write_python_token(blob)
        return json.dumps({
            "ok": True,
            "scopes": blob["scopes"],
            "expires_at": blob["expires_at"],
            "message": "Google connected. You can close the browser tab.",
        })
    except Exception as e:  # noqa: BLE001
        return json.dumps({"ok": False, "error": "exception", "detail": str(e)})
    finally:
        server.shutdown()
        server.server_close()


@mcp.tool()
def finish_google_connect(callback_json: str) -> str:
    """Paste fallback: finish connecting by pasting the JSON blob from the gateway
    callback page. Only needed if the one-click localhost capture isn't available.

    callback_json: the full JSON shown on the gateway's callback page
                   (access_token, refresh_token, expires_at, scopes).
    """
    try:
        blob = json.loads(callback_json)
    except json.JSONDecodeError as e:
        return json.dumps({"ok": False, "error": "bad_json", "detail": str(e)})
    # refresh_token is only present on first consent; reuse the stored one otherwise.
    if not blob.get("refresh_token"):
        try:
            blob["refresh_token"] = gt._stored_refresh_token()
        except FileNotFoundError:
            pass
    missing = [k for k in ("access_token", "refresh_token", "expires_at") if not blob.get(k)]
    if missing:
        return json.dumps({"ok": False, "error": "missing_fields", "fields": missing})
    blob.setdefault("scopes", [])
    try:
        gt.write_python_token(blob)
    except Exception as e:  # noqa: BLE001
        return json.dumps({"ok": False, "error": "write_failed", "detail": str(e)})
    return json.dumps({"ok": True, "scopes": blob["scopes"],
                       "expires_at": blob["expires_at"], "message": "Google connected."})


if __name__ == "__main__":
    mcp.run()
