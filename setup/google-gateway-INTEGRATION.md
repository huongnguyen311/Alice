# Integration Guide — Docs/Sheets OAuth Gateway

Reference for the **easy-auth gateway** that Alice's Google Sheets setup talks to.
This is the protocol spec; for Alice's setup steps see `setup/google-sheets-setup.md`.

## What this gateway is

A **token broker** for Google **Docs + Sheets**. Alice never touches the Google
OAuth `client_secret` — the gateway holds it server-side. Alice is given a
**gate credential**: a `clientId` + `clientSecret` pair (minted by the gateway operator
via `scripts/gen-gate-secret.mjs`). Both are stored in `credentials/gateway-config.json`.

- A `clientId` is a **group** — many users can authorize under the same `clientId`.
- Each user OAuths **once** and Alice keeps their `refresh_token`.
- Scopes: `documents` + `spreadsheets` only. **No Drive write.**

Base URL (from the operator after deploy):
`https://us-central1-<PROJECT_ID>.cloudfunctions.net/gateway`

## Flow

### 1. Start consent — `POST /auth/start`

```bash
curl -X POST https://.../gateway/auth/start \
  -H 'Content-Type: application/json' \
  -d '{"clientId":"<your-clientId>","clientSecret":"<your-clientSecret>"}'
```

Response:
```json
{ "authUrl": "https://accounts.google.com/o/oauth2/v2/auth?...", "state": "..." }
```

Open `authUrl` in the user's browser.

#### Optional: localhost redirect (one-click capture)

To enable a zero-paste desktop flow, the caller may pass a `redirect_uri`:

```json
{ "clientId": "...", "clientSecret": "...", "redirect_uri": "http://127.0.0.1:54321/callback" }
```

**Gateway requirements for this to work:**
1. **Allowlist** `redirect_uri` to `http://localhost:*` and `http://127.0.0.1:*` only —
   never honor arbitrary external redirects (open-redirect / token-exfil risk).
2. Carry the `redirect_uri` through OAuth `state`.
3. On `/auth/callback`, after exchanging the code, **302-redirect** to that localhost URL
   with the token as **query params**: `?access_token=...&refresh_token=...&expires_at=...&scopes=...`
   (space- or comma-joined `scopes` both accepted by the client).
4. Register `http://localhost` and `http://127.0.0.1` as authorized redirect URIs on the
   Google Cloud OAuth client.

Alice's `mcp__google-auth__connect_google` tool starts a one-shot local server on
`127.0.0.1:<ephemeral>` and reads the token from that 302. If the gateway does **not**
support this, the gateway's hosted callback page should still render the JSON blob so the
user can paste it via `finish_google_connect`.

### 2. User consents — `GET /auth/callback`

Google redirects to the gateway's callback. The callback page displays a JSON blob:

```json
{
  "access_token": "ya29....",
  "refresh_token": "1//0g...",
  "expires_at": "2026-06-03T12:34:56.000Z",
  "scopes": ["https://www.googleapis.com/auth/documents",
             "https://www.googleapis.com/auth/spreadsheets"]
}
```

**Store the `refresh_token` durably and secretly.** This is the once-only step — the
gateway also registers this token in its server-side whitelist at this moment.

> #### ⚠️ Load-bearing: the gateway MUST send `prompt=consent` on `/auth/start`
>
> The gateway's Google auth URL sets `access_type=offline` **and** `prompt=consent`.
> Both are required and must not be removed.
>
> Google only re-issues a `refresh_token` when `prompt=consent` forces a fresh consent
> screen. Without it, Google withholds the `refresh_token` on any authorization *after*
> the user's first one. That breaks the **delete-token-and-reconnect** recovery path: if a
> user deletes their stored `credentials/google_token.json` and reconnects, the callback
> arrives with an `access_token` but **no `refresh_token`**, and there is no stored one to
> fall back on — the user is locked out until the operator clears Google's grant.
>
> With `prompt=consent` (current config), every reconnect returns a fresh `refresh_token`,
> so delete-and-reconnect always recovers cleanly. **Do not drop `prompt=consent` for a
> smoother UX** without restoring the refresh_token another way.
>
> Client-side, `build_blob_from_params` / `finish_google_connect` reuse the *stored*
> refresh_token when a re-consent callback omits one — but that only helps if a stored
> token still exists. It cannot rescue the delete-and-reconnect case; only `prompt=consent`
> can. See `setup/gateway_tokens.py` and `mcp/google_auth_mcp.py`.

### 3. Refresh when the access token expires — `POST /refresh`

```bash
curl -X POST https://.../gateway/refresh \
  -H 'Content-Type: application/json' \
  -d '{"clientId":"<your-clientId>","clientSecret":"<your-clientSecret>","refresh_token":"1//0g..."}'
```

Response:
```json
{ "access_token": "ya29....", "expires_at": "...", "scopes": [...] }
```

> `/refresh` never returns a new `refresh_token` — keep the one from step 2.

### 4. Call Google directly

Use `access_token` as a Bearer token against the Google Docs/Sheets REST APIs
(in Alice this is done by the Python `google-api-python-client` in
`skills/Google-Sheet/skill.md`).

## Error handling

| Status | Body | Meaning | What to do |
|---|---|---|---|
| `403` | `{ "error": "token_disposed", "action": "reauthorize" }` | Admin removed this token from the whitelist (revoked), or it isn't whitelisted | Discard the stored `refresh_token`, restart from `/auth/start` |
| `401` | `{ "error": "refresh_failed", "action": "reauthorize" }` | Google rejected the refresh (expired/revoked upstream) | Restart from `/auth/start` |
| `401` | `{ "error": "unauthorized" }` | Bad/disabled gate credential (`clientId`/`clientSecret`) | Fix the gate config; contact the operator |
| `429` | `{ "error": "rate_limited" }` | Too many requests for this `clientId` | Back off and retry |
| `400` | `{ "error": "missing_refresh_token" }` | You didn't send `refresh_token` | Fix the request |

**Rule of thumb:** any response carrying `"action": "reauthorize"` means *connection lost* —
re-run `setup/google_gateway_auth.py`.

## Constraints

- You **cannot** refresh directly with Google — Alice doesn't have the Google
  `client_secret`. Always go through `POST /refresh`
  (`setup/gateway_tokens.py::refresh_via_gateway`).
- There is **no `/revoke` endpoint**. Disposing a token is handled by the gateway operator
  (deleting a Firestore record). Alice only needs to react to `reauthorize`.
- The only endpoints are: `POST /auth/start`, `GET /auth/callback`, `POST /refresh`.

## Where this lives in Alice

| Concern | File |
|---|---|
| Gate credential + base URL | `credentials/gateway-config.json` (gitignored; template `.example`) |
| One-time consent | `setup/google_gateway_auth.py` |
| Token write + `/refresh` | `setup/gateway_tokens.py` |
| Stored user token | `credentials/google_token.json` (google-auth shape) |
| API calls | `skills/Google-Sheet/skill.md` (Python, with pre-flight refresh) |
