# Sign in with Chutes — OAuth 2.0 + OIDC + PKCE Flow

> **Status: BETA** reference. The upstream `chutesai/Sign-in-with-Chutes` Next.js package implements this; this doc exists so agents can explain what's happening when they wire it up.

## The flow

```
   Browser           Your App             Chutes IdP            Chutes API
     │                  │                     │                     │
     │  click SignIn    │                     │                     │
     │─────────────────▶│                     │                     │
     │                  │  gen code_verifier  │                     │
     │                  │  gen challenge      │                     │
     │  302 /idp/authorize?...code_challenge  │                     │
     │◀─────────────────│                     │                     │
     │  GET /idp/authorize?...                │                     │
     │───────────────────────────────────────▶│                     │
     │                                        │                     │
     │       user authenticates + consent     │                     │
     │◀───────────────────────────────────────│                     │
     │                                        │                     │
     │  302 /api/auth/chutes/callback?code=…  │                     │
     │───────────────────────────────────────▶│                     │
     │                  │  GET callback?code  │                     │
     │                  │◀────────────────────│                     │
     │                  │  POST /idp/token    │                     │
     │                  │    grant=auth_code  │                     │
     │                  │    +code_verifier   │                     │
     │                  │────────────────────▶│                     │
     │                  │  access+id+refresh  │                     │
     │                  │◀────────────────────│                     │
     │                  │  set session cookie │                     │
     │  302 home        │                     │                     │
     │◀─────────────────│                     │                     │
     │                  │                     │                     │
     │  later: inference                      │                     │
     │                  │  POST /v1/chat/completions                │
     │                  │  Authorization: Bearer <access>           │
     │                  │──────────────────────────────────────────▶│
     │                  │  response           │                     │
     │                  │◀──────────────────────────────────────────│
```

## Token types

- **Access token** — short-lived (minutes), used as `Authorization: Bearer <token>` against `llm.chutes.ai` and `api.chutes.ai`. Scoped to the scopes the user consented to.
- **ID token** — JWT containing OIDC claims. Your app uses this to establish session identity but **should not** forward it as a bearer to Chutes APIs.
- **Refresh token** — long-lived, used to mint new access tokens without re-prompting the user. Server-side only — never ship to the browser.

The upstream Next.js package handles all three in a server-side session so the browser never sees the refresh token.

## Why PKCE matters

PKCE (Proof Key for Code Exchange) stops an attacker who intercepts the authorization code from exchanging it. The `code_verifier` is a high-entropy random string generated per login and never leaves your server; the `code_challenge` in the redirect URL is just its hash. Chutes requires PKCE for all public and confidential clients.

## Where secrets live

| Secret | Location |
|---|---|
| `csc_...` (client secret) | OS keychain, read at app boot |
| Access token | Server-side session store (encrypted cookie, Redis, etc.) |
| Refresh token | Same server-side store — never in browser |
| `code_verifier` | Short-lived server session, bound to the `state` param |

The vendored Next.js routes in SIWC follow this model — don't reinvent it.

## Handling logout

Logout should:

1. Clear the server session.
2. `POST /idp/token/revoke` with the refresh token (and optionally the access token). This is what the upstream `/api/auth/chutes/logout` route does.
3. Redirect the user home.

Missing step 2 means the token remains usable until expiry if the session store leaks. Do not skip it.

## Handling token expiry

When an access token is about to expire, use the refresh token to get a new one server-side. If the refresh fails (user revoked consent, secret was rotated, etc.), fall back to re-running the login flow. The upstream `serverAuth.ts` helper handles this transparently — call `getServerAccessToken()` and it does the right thing.
