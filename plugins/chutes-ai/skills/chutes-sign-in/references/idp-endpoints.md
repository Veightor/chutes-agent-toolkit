# `/idp/*` Endpoint Reference

> **Status: BETA** — scraped from the public API surface + the Hermes proposal audit. Verify against `https://api.chutes.ai/openapi.json` for your account before shipping.

All endpoints are served from `https://api.chutes.ai` and require `Authorization: Bearer cpk_...` (the user's API key, not a client secret) for management operations. Token introspection/revocation accepts either the management bearer or an app client secret depending on the endpoint — when in doubt, use the management bearer.

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

### List your apps
```
GET /idp/apps
```

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

## Scopes

### List all available scopes
```
GET /idp/scopes
```
Returns every scope the IdP will honor and a short description for each. Use this to build the scope cookbook dynamically if you want.

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
Response (RFC 7662):
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
Returns the standard OIDC claims (`sub`, `name`, `preferred_username`, `email`) filtered by the scopes the token was issued with.

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

The vendored Next.js routes (`/api/auth/chutes/login`, `/api/auth/chutes/callback`) implement this for you. Don't reimplement unless you're building a native mobile client or a non-Next.js server.
