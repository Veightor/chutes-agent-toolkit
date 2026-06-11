# `/idp/*` Endpoint Reference

> **Status: BETA** — path inventory re-verified against the live `https://api.chutes.ai/openapi.json` on 2026-06-11 (all paths below exist; `GET /idp/scopes`, `GET /idp/apps`, and `GET /.well-known/openid-configuration` exercised live with read-only GETs). Mutating flows (create/rotate/delete app) were last exercised end-to-end 2026-04-13. Verify request/response shapes against the openapi spec for your account before shipping.

All endpoints are served from `https://api.chutes.ai` and require `Authorization: Bearer cpk_...` (the user's API key, not a client secret) for management operations. Token introspection/revocation accepts either the management bearer or an app client secret depending on the endpoint — when in doubt, use the management bearer.

## OIDC discovery

```
GET /.well-known/openid-configuration
```

Public, no auth (verified live 2026-06-11). Key contents: `issuer: https://api.chutes.ai`; `authorization_endpoint: /idp/authorize`; `token_endpoint: /idp/token`; `userinfo_endpoint: /idp/userinfo`; `introspection_endpoint: /idp/token/introspect`; `revocation_endpoint: /idp/token/revoke`; `grant_types_supported: ["authorization_code", "refresh_token"]`; `response_types_supported: ["code"]`; `code_challenge_methods_supported: ["plain", "S256"]` (always use S256); `token_endpoint_auth_methods_supported: ["client_secret_post", "client_secret_basic", "none"]` (so public clients without a secret are supported); `claims_supported: ["sub", "username", "created_at"]`; `service_documentation: https://docs.chutes.ai/oauth`.

## Apps

### Create an OAuth app
```
POST /idp/apps
Content-Type: application/json
Authorization: Bearer cpk_...

{
  "name": "My App",
  "description": "What it does",
  "homepage_url": "https://myapp.example.com",
  "redirect_uris": [
    "http://localhost:3000/api/auth/chutes/callback",
    "https://myapp.example.com/api/auth/chutes/callback"
  ],
  "scopes": ["openid", "profile", "chutes:invoke"]
}
```

Response:
```json
{
  "app_id": "app_...",
  "client_id": "cid_...",
  "client_secret": "csc_...",   // shown once
  "name": "...",
  "homepage_url": "...",
  "redirect_uris": [...],
  "scopes": [...]
}
```

The `client_secret` is returned **only in this response**. Store it in the keychain immediately.

### List apps
```
GET /idp/apps
```

**Semantics changed since the April snapshot (verified live 2026-06-11):** by default this returns apps owned by the current user **plus public apps and apps shared with you** — not just your own. Response is a paginated envelope `{ "total": N, "page": 0, "limit": 25, "items": [...] }`. Query params: `include_public` (set `false` to exclude public apps), `include_shared` (set `false` to exclude shared apps), `search` (filter by name/description), `page`, `limit`, `user_id`. For a "my apps only" audit, pass `include_public=false&include_shared=false`.

### Read one app
```
GET /idp/apps/{app_id}
```

### Update metadata
```
PATCH /idp/apps/{app_id}
{ "name": "...", "redirect_uris": [...], ... }
```
Note: scope changes may require user re-consent on next login.

### Delete an app
```
DELETE /idp/apps/{app_id}
```

### Regenerate the client secret
```
POST /idp/apps/{app_id}/regenerate-secret
```
Response contains a new `client_secret`. The old secret is invalidated immediately — plan for a short outage window on any service that had the old value loaded.

### Share an app with another user **(new since April snapshot)**
```
POST   /idp/apps/{app_id}/share            # share with another user (JSON body, OAuthAppShareArgs)
GET    /idp/apps/{app_id}/shares           # list users the app is shared with
DELETE /idp/apps/{app_id}/share/{user_id}  # unshare
```
Paths verified present in openapi.json 2026-06-11; sharing semantics beyond the openapi summaries are unverified as of 2026-06-11.

## Scopes

### List all available scopes
```
GET /idp/scopes
```
Returns every scope the IdP will honor and a short description for each. Use this to build the scope cookbook dynamically if you want.

Live response 2026-06-11 (verified): `admin`, `profile`, `profile:read`, `balance`, `balance:read`, `billing:read`, `quota`, `quota:read`, `usage`, `usage:read`, `account:read`, `account:write`, `secrets:read`, `secrets:write`, `chutes:read`, `chutes:write`, `chutes:delete`, `chutes:invoke`, `images:read`, `images:write`, `images:delete`, `invocations:read`.

Notes:

- `openid` does **not** appear in `/idp/scopes` or in `scopes_supported` in the discovery document, even though the platform OAuth docs describe it as the required base scope. The upstream SIWC package sends it; whether the IdP requires, accepts, or ignores it at `/idp/authorize` is unverified as of 2026-06-11.
- The platform docs also describe a per-chute delegation scope `chutes:invoke:{chute_id}` (limit a token to invoking one specific chute). It is parameterized, so it does not appear in the static `/idp/scopes` list (unverified as of 2026-06-11).

## Authorizations

### List authorizations granted to your apps
```
GET /idp/authorizations
```
Pagination + filtering. Useful for audits ("who is using our app").

### Revoke an authorization for a specific app
```
DELETE /idp/authorizations/{app_id}
```
Removes all active grants against that app. The user has to re-consent next time.

## Tokens

### Introspect
```
POST /idp/token/introspect
Content-Type: application/x-www-form-urlencoded

token=<access_token>
```
The openapi spec declares `application/x-www-form-urlencoded` as the **only** accepted content type (verified 2026-06-11) — a JSON body will not work. Response (RFC 7662):
```json
{
  "active": true,
  "scope": "openid profile chutes:invoke",
  "client_id": "cid_...",
  "username": "alice",
  "exp": 1234567890,
  "sub": "user-uuid"
}
```

### Revoke
```
POST /idp/token/revoke
token=<access_token_or_refresh_token>
```
Returns `{ "revoked": true }` on success. Use this on logout and on detected credential leaks.

## Userinfo

### OpenID userinfo
```
GET /idp/userinfo
Authorization: Bearer <access_token>
```
Returns OIDC claims filtered by the scopes the token was issued with. The discovery document advertises `claims_supported: ["sub", "username", "created_at"]` (verified 2026-06-11) — do **not** assume `name`, `preferred_username`, or `email` are present. This endpoint takes an OAuth access token, not a `cpk_` API key — platform docs state it rejects `cpk_` keys (unverified as of 2026-06-11).

## PKCE authorization flow

Chutes implements standard OAuth 2.0 Authorization Code + PKCE. The upstream `chutesai/Sign-in-with-Chutes` Next.js package handles the full client-side dance. If you are implementing from scratch, the endpoints are:

```
# 1. Browser redirect
GET /idp/authorize?
  response_type=code
  &client_id=cid_...
  &redirect_uri=<URL>
  &scope=openid+profile+chutes:invoke
  &code_challenge=<base64url(SHA256(verifier))>
  &code_challenge_method=S256
  &state=<csrf>

# 2. Exchange code for tokens
POST /idp/token
  grant_type=authorization_code
  code=<code>
  redirect_uri=<URL>
  client_id=cid_...
  client_secret=csc_...
  code_verifier=<original>
```

`GET /idp/authorize` accepts exactly these query params per the openapi spec (verified 2026-06-11): `response_type`, `client_id`, `redirect_uri`, `scope`, `state`, `code_challenge`, `code_challenge_method`. PKCE `plain` is technically supported alongside `S256` — always use `S256`. Platform docs state the code verifier must be 43-128 chars and access tokens last ~1 hour with refresh tokens supported (unverified as of 2026-06-11).

The vendored Next.js routes (`/api/auth/chutes/login`, `/api/auth/chutes/callback`) implement this for you. Don't reimplement unless you're building a native mobile client or a non-Next.js server.

## Other `/idp/*` endpoints (paths verified in openapi.json 2026-06-11)

| Method | Path | Purpose (from openapi summaries) |
|---|---|---|
| GET | `/idp/authorize/consent` | Render the authorization consent page |
| POST | `/idp/authorize/consent` | Handle consent form submission |
| POST | `/idp/login` | Handle IdP login form submission |
| GET | `/idp/cli_login` | CLI login via Bittensor hotkey signature |
| GET | `/idp/cli_login/nonce` | Nonce for the CLI hotkey login |

These back the hosted login/consent UI and the `chutes` CLI's browser-based `login`; relying parties normally never call them directly.
