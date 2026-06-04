# Google Sheets Setup — Easy-Auth Gateway

This guide sets up Alice's Google **Sheets/Docs** access via the **easy-auth gateway**
(a token broker). You no longer need a Google `client_secret` on this machine — the
gateway holds it server-side. You only need a **gate credential** (`clientId` +
`clientSecret`) and you consent **once** to mint a `refresh_token`.

> **Scope:** This is the Sheets/Docs path only. Gmail & Calendar Python scripts still
> use the older desktop-OAuth flow (`setup/google_auth_setup.py` →
> `credentials/google_token.json`) — that is **not** part of this gateway migration.
> **Note:** the Sheets path also writes `credentials/google_token.json`; if you use both
> Gmail/Calendar Python *and* Sheets, run whichever setup last to own that file, or keep
> the gateway one (it carries `spreadsheets` + `drive.readonly`; Gmail/Calendar need their
> own scopes — see "Coexistence" below).

> **No MCP:** Google Sheets in Alice runs entirely through the Python skill
> (`skills/Google-Sheet/skill.md`). The old `mcp-google-sheets` MCP has been removed.

---

## Easiest: connect from Claude (one click)

Inside the Alice project, just say:

> **"connect my google"**

This runs the project-scoped `google-auth` MCP (`skills/alice-google-connect.md`):
it opens the Google consent page, you click **Allow**, and the token is captured and
saved automatically — **no copy-paste**. Prerequisite: `credentials/gateway-config.json`
must exist (step 2 below). Everything after this section is the **manual fallback**.

> One-click auto-capture needs the gateway to honor a `localhost` redirect_uri
> (see `setup/google-gateway-INTEGRATION.md`). If it doesn't yet, the connect flow
> falls back to a single paste.

---

## How it works

```
credentials/
├── gateway-config.json        ← gate credential (base_url + clientId + clientSecret) — gitignored
└── google_token.json          ← minted/refreshed token (access + refresh) — gitignored
```

The gateway exposes three endpoints (full spec: `setup/google-gateway-INTEGRATION.md`):
`POST /auth/start`, `GET /auth/callback`, `POST /refresh`. Alice never sees Google's
`client_secret`, so the token **cannot self-refresh** — refresh always routes through the
gateway (handled automatically by `setup/gateway_tokens.py`).

---

## Setup Steps

### 1. Get a gate credential

Ask the gateway **operator** for:
- `base_url` (e.g. `https://us-central1-<PROJECT_ID>.cloudfunctions.net/gateway`)
- `clientId`
- `clientSecret`

(The operator mints these via `scripts/gen-gate-secret.mjs`.)

### 2. Create the gateway config

```bash
cp credentials/gateway-config.json.example credentials/gateway-config.json
```

Edit `credentials/gateway-config.json` and fill in `base_url`, `client_id`, `client_secret`.
This file is gitignored (`credentials/*`) — never commit it.

### 3. Install dependencies

```bash
{ALICE_ROOT}/.venv/bin/pip install \
  google-auth \
  google-auth-httplib2 \
  google-api-python-client \
  requests
```

### 4. Run the gateway consent flow

```bash
{ALICE_ROOT}/.venv/bin/python {ALICE_ROOT}/setup/google_gateway_auth.py
```

This will:
- Call `POST /auth/start` and open the Google consent page in your browser
- After you approve, the gateway **callback page shows a JSON blob** (`access_token`,
  `refresh_token`, `expires_at`, `scopes`)
- **Copy the entire JSON** and paste it back into the terminal (end with an empty line)
- The script writes `credentials/google_token.json`

### 5. Verify

```bash
ls {ALICE_ROOT}/credentials/google_token.json
```

Then run Alice's connection check:

> "check connections" or "check google sheet connection"

Or test a real call:

> "list my google sheets"

---

## Token Refresh

- **Automatic:** Every Sheets CRUD snippet runs a **pre-flight refresh** before calling
  Google — `setup/gateway_tokens.py::refresh_via_gateway()`. It only hits the network when
  the token is near expiry, then re-writes `google_token.json`.
- **Manual check:**
  ```bash
  {ALICE_ROOT}/.venv/bin/python {ALICE_ROOT}/setup/gateway_tokens.py        # refresh if expired
  {ALICE_ROOT}/.venv/bin/python {ALICE_ROOT}/setup/gateway_tokens.py --force  # force refresh
  ```
- **Re-consent (connection lost):** If the gateway returns `"action": "reauthorize"`
  (token revoked/disposed upstream), the refresh prints an instruction to re-run:
  ```bash
  {ALICE_ROOT}/.venv/bin/python {ALICE_ROOT}/setup/google_gateway_auth.py
  ```

---

## Troubleshooting

| Error | Cause | Fix |
|---|---|---|
| `Missing credentials/gateway-config.json` | Config not created | Run step 2 (`cp ... .example`) and fill values |
| `... still contains placeholder <...> values` | Config not filled in | Replace `<...>` with real gate creds |
| `[reauthorize] Gateway connection lost` | `refresh_token` revoked/disposed | Re-run `setup/google_gateway_auth.py` |
| `Bad/disabled gate credential` (401 `unauthorized`) | Wrong/disabled `clientId`/`clientSecret` | Verify with the operator; fix `gateway-config.json` |
| `Gateway rate-limited (429)` | Too many requests for this `clientId` | Back off and retry shortly |
| `could not parse pasted JSON` | Incomplete paste of the callback blob | Re-run and paste the **entire** JSON block |
| `ModuleNotFoundError: requests` | Deps not installed | Run step 3 with the venv Python |

---

## Coexistence with Gmail/Calendar Python

Gmail/Calendar Python scripts share `credentials/google_token.json` but need
`gmail.modify` + `calendar` scopes, which the gateway does **not** grant (Sheets/Docs only).
If you rely on both:
- Keep them in separate token files, **or**
- Re-run whichever setup you primarily use; the Sheets gateway token covers
  `spreadsheets` + `drive.readonly` only.

This migration intentionally left the Gmail/Calendar flow untouched
(`setup/google_auth_setup.py`).

---

## Related Files

| File | Purpose |
|---|---|
| `credentials/gateway-config.json` | Gate credential (base_url + clientId + clientSecret) |
| `setup/google_gateway_auth.py` | One-time gateway consent → writes the token |
| `setup/gateway_tokens.py` | Token writer + `/refresh` helper (pre-flight refresh) |
| `setup/google-gateway-INTEGRATION.md` | Full gateway protocol reference |
| `credentials/google_token.json` | Minted access + refresh token (gitignored) |
| `skills/Google-Sheet/skill.md` | Google Sheets CRUD skill (Python) |
