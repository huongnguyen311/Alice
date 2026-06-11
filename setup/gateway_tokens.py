"""
Shared token helpers for the Google Docs/Sheets easy-auth gateway.

The gateway is a *token broker* only — it mints/refreshes the Google OAuth
access_token + refresh_token. The actual Sheets/Docs API calls are made by the
Python Google Sheets skill (google-api-python-client), which reads
credentials/google_token.json. This module writes that file from a gateway
response and refreshes it through the gateway (the only place that holds
Google's client_secret).

See setup/google-gateway-INTEGRATION.md for the gateway protocol.

Used by:
  - setup/google_gateway_auth.py   (one-time consent → write_tokens)
  - skills/Google-Sheet/skill.md   (pre-flight refresh_via_gateway)
"""

import importlib.util
import json
import sys
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path

# --- dependency guard (CLAUDE.md rule) -------------------------------------
if importlib.util.find_spec("requests") is None:
    import subprocess

    subprocess.run([sys.executable, "-m", "pip", "install", "requests"], check=True)

import requests  # noqa: E402

BASE_DIR = Path(__file__).resolve().parent.parent
CREDENTIALS_DIR = BASE_DIR / "credentials"
GATEWAY_CONFIG = CREDENTIALS_DIR / "gateway-config.json"
PY_TOKEN = CREDENTIALS_DIR / "google_token.json"      # consumed by the Python skill

# Sentinel that makes google-auth NOT attempt a direct Google refresh.
# The gateway withholds Google's client_secret, so the google-auth library can
# never refresh on its own — refresh MUST go through refresh_via_gateway().
_GATEWAY_SENTINEL = "GATEWAY_BROKERED__refresh_via_gateway"


class ReauthorizeRequired(Exception):
    """Raised when the gateway says the connection is lost and consent must be redone.

    Maps to the gateway's `action: "reauthorize"` (403 token_disposed /
    401 refresh_token_expired). The stored refresh_token is dead — drop it and
    re-run setup/google_gateway_auth.py.
    """


class TransientRefreshError(RuntimeError):
    """Raised when /refresh fails transiently and retries are exhausted.

    Maps to the gateway's `action: "retry"` (502 refresh_failed / 429
    rate_limited). The refresh_token is **still valid** — keep it and try later.
    """


# How many times to retry an `action: "retry"` response before giving up.
_RETRY_ATTEMPTS = 3
# Base seconds for exponential backoff (1s, 2s, 4s, ...).
_RETRY_BACKOFF_BASE = 1.0


def load_gateway_config() -> dict:
    if not GATEWAY_CONFIG.exists():
        raise FileNotFoundError(
            f"Missing {GATEWAY_CONFIG}.\n"
            f"Copy the template:  cp {GATEWAY_CONFIG}.example {GATEWAY_CONFIG}\n"
            f"then fill in base_url / client_id / client_secret from the gateway operator."
        )
    cfg = json.loads(GATEWAY_CONFIG.read_text(encoding="utf-8"))
    missing = [k for k in ("base_url", "client_id", "client_secret") if not cfg.get(k)]
    if missing:
        raise ValueError(f"{GATEWAY_CONFIG} is missing values: {', '.join(missing)}")
    if "<" in cfg["base_url"] or "<" in cfg["client_id"]:
        raise ValueError(
            f"{GATEWAY_CONFIG} still contains placeholder <...> values — fill in real gate credentials."
        )
    return cfg


def _parse_expires_at(expires_at: str) -> datetime:
    """ISO-8601 (e.g. 2026-06-03T12:34:56.000Z) → aware UTC datetime."""
    return datetime.fromisoformat(expires_at.replace("Z", "+00:00")).astimezone(timezone.utc)


def write_python_token(blob: dict) -> None:
    """Write credentials/google_token.json in the google-auth Credentials shape.

    client_id / client_secret / token_uri are sentinels so google-auth never
    tries to refresh directly against Google (it can't — no client_secret).
    """
    expiry_iso = _parse_expires_at(blob["expires_at"]).replace(tzinfo=None).isoformat()
    token = {
        "token": blob["access_token"],
        "refresh_token": blob["refresh_token"],
        "token_uri": "https://oauth2.googleapis.com/token",
        "client_id": _GATEWAY_SENTINEL,
        "client_secret": _GATEWAY_SENTINEL,
        "scopes": blob.get("scopes", []),
        "universe_domain": "googleapis.com",
        "expiry": expiry_iso,
    }
    CREDENTIALS_DIR.mkdir(exist_ok=True)
    PY_TOKEN.write_text(json.dumps(token, indent=2) + "\n", encoding="utf-8")


def write_tokens(blob: dict) -> None:
    """Write the Python google-auth token file from a gateway response blob."""
    write_python_token(blob)


def build_blob_from_params(params: dict) -> dict:
    """Normalize gateway localhost-redirect query params into a token blob.

    The localhost-redirect callback delivers the token as query params, where
    repeated/list values may arrive as 1-element lists (urllib.parse.parse_qs)
    and `scopes` may be a space- or comma-joined string. Produces the same blob
    shape that write_python_token()/refresh_via_gateway() expect.

    Per the gateway protocol, `refresh_token` is only returned on **first**
    consent; on re-consent it may be absent. In that case we reuse the stored
    refresh_token (the gateway keeps the same one — see /refresh contract).
    """
    def one(v):
        return v[0] if isinstance(v, (list, tuple)) else v

    access_token = one(params.get("access_token"))
    refresh_token = one(params.get("refresh_token"))
    expires_at = one(params.get("expires_at"))

    raw_scopes = params.get("scopes") or params.get("scope") or []
    if isinstance(raw_scopes, (list, tuple)) and len(raw_scopes) == 1:
        raw_scopes = raw_scopes[0]
    if isinstance(raw_scopes, str):
        scopes = raw_scopes.replace(",", " ").split()
    else:
        scopes = list(raw_scopes)

    # refresh_token is only sent on first consent; fall back to the stored one.
    if not refresh_token:
        try:
            refresh_token = _stored_refresh_token()
        except FileNotFoundError:
            pass  # leave empty → reported as missing below

    missing = [k for k, v in
               (("access_token", access_token), ("expires_at", expires_at),
                ("refresh_token", refresh_token)) if not v]
    if missing:
        raise ValueError(
            f"Callback params missing: {', '.join(missing)}"
            + (" (no refresh_token in callback and none stored — first consent must "
               "return one)" if "refresh_token" in missing else "")
        )

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "expires_at": expires_at,
        "scopes": scopes,
    }


def _stored_refresh_token() -> str:
    """Read the refresh_token from the Python token file."""
    if PY_TOKEN.exists():
        rt = json.loads(PY_TOKEN.read_text(encoding="utf-8")).get("refresh_token")
        if rt:
            return rt
    raise FileNotFoundError(
        "No stored refresh_token found. Run: setup/google_gateway_auth.py first."
    )


def _is_expired() -> bool:
    """True if the token is missing or its expiry has passed (60s skew)."""
    if not PY_TOKEN.exists():
        return True
    expiry = json.loads(PY_TOKEN.read_text(encoding="utf-8")).get("expiry")
    if not expiry:
        return True
    # Stored expiry is naive UTC ISO (google-auth convention).
    expiry_dt = datetime.fromisoformat(expiry).replace(tzinfo=timezone.utc)
    return datetime.now(timezone.utc) >= (expiry_dt - timedelta(seconds=60))


def _post_refresh_once(cfg: dict, refresh_token: str) -> bool:
    """One POST /refresh round-trip. Re-writes the token file on success.

    Returns True on success. Branches on the gateway's `action` field
    (see google-gateway-INTEGRATION.md error table):
      - action "reauthorize" (403 token_disposed / 401 refresh_token_expired)
        → ReauthorizeRequired: the refresh_token is dead, drop it and re-consent.
      - action "retry" (502 refresh_failed / 429 rate_limited)
        → TransientRefreshError: the refresh_token is still valid, retry later.
      - anything else (e.g. 401 unauthorized gate credential) → RuntimeError.
    """
    resp = requests.post(
        f"{cfg['base_url'].rstrip('/')}/refresh",
        json={
            "clientId": cfg["client_id"],
            "clientSecret": cfg["client_secret"],
            "refresh_token": refresh_token,
        },
        timeout=30,
    )

    if resp.status_code == 200:
        data = resp.json()
        # /refresh never returns a new refresh_token — keep the one we have.
        blob = {
            "access_token": data["access_token"],
            "refresh_token": refresh_token,
            "expires_at": data["expires_at"],
            "scopes": data.get("scopes", []),
        }
        write_tokens(blob)
        return True

    # Map the gateway error table (see google-gateway-INTEGRATION.md).
    try:
        err = resp.json()
    except ValueError:
        err = {}
    action = err.get("action")
    code = err.get("error", f"http_{resp.status_code}")
    message = err.get("message", "")

    if action == "reauthorize":
        # refresh_token_expired (e.g. Testing-mode 7-day expiry) or token_disposed.
        raise ReauthorizeRequired(
            f"Gateway connection lost ({code}). Drop the stored token and re-run: "
            f"setup/google_gateway_auth.py" + (f" — {message}" if message else "")
        )
    if action == "retry":
        # Transient: refresh_token is still valid. Caller backs off and retries.
        raise TransientRefreshError(
            f"Gateway /refresh transient failure ({code})"
            + (f": {message}" if message else "")
        )
    if resp.status_code == 401 and code == "unauthorized":
        raise RuntimeError(
            "Bad/disabled gate credential — check credentials/gateway-config.json or contact the operator."
        )
    raise RuntimeError(f"Gateway /refresh failed ({resp.status_code}): {code}")


def refresh_via_gateway(force: bool = False) -> bool:
    """Exchange the stored refresh_token for a fresh access_token via POST /refresh,
    then re-write the token file.

    Returns True if a refresh happened, False if the token was still valid.

    Branches on the gateway's `action` field per the integration contract:
      - `reauthorize` → ReauthorizeRequired (refresh_token dead, re-consent).
      - `retry` → backs off (exponential) and retries up to _RETRY_ATTEMPTS,
        keeping the refresh_token; raises TransientRefreshError if all fail.
    """
    if not force and not _is_expired():
        return False

    cfg = load_gateway_config()
    refresh_token = _stored_refresh_token()

    last_exc = None
    for attempt in range(_RETRY_ATTEMPTS):
        try:
            return _post_refresh_once(cfg, refresh_token)
        except TransientRefreshError as exc:
            last_exc = exc
            if attempt < _RETRY_ATTEMPTS - 1:
                time.sleep(_RETRY_BACKOFF_BASE * (2 ** attempt))
    # Retries exhausted — surface the transient error; refresh_token stays valid.
    raise last_exc


if __name__ == "__main__":
    # CLI: `python setup/gateway_tokens.py` → refresh if needed.
    try:
        changed = refresh_via_gateway(force="--force" in sys.argv)
        print("Refreshed tokens." if changed else "Token still valid — no refresh needed.")
    except ReauthorizeRequired as e:
        print(f"[reauthorize] {e}")
        sys.exit(2)
    except TransientRefreshError as e:
        print(f"[retry] {e}")
        sys.exit(3)
