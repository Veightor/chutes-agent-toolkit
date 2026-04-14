# Sign in with Chutes — Overview

> **Status: BETA** — this doc reflects the BETA state of the `chutes-sign-in` skill. It graduates only alongside a verified end-to-end run.

## What it is

"Sign in with Chutes" turns Chutes.ai into an OAuth 2.0 + OpenID Connect identity provider. Instead of embedding a single shared `cpk_...` API key in your app, you let users sign in with their own Chutes accounts and make AI calls **on their own behalf** — with their quota, their billing, and their model access.

This reframes Chutes from "an LLM API" into "a developer platform with an identity layer."

## When to use OAuth vs API keys

| Scenario | Pick |
|---|---|
| Internal tool, single service account | **API key** |
| CI/CD, headless job | **API key** (via `CHUTES_API_KEY` env var) |
| Agent your team owns end-to-end | **API key** |
| Consumer-facing app where *users* bring their own Chutes account | **OAuth (SIWC)** |
| Multi-tenant SaaS billing inference back to each tenant | **OAuth (SIWC)** |
| Anywhere the user needs to see their own Chutes balance / quotas | **OAuth (SIWC)** |

If you're not sure, start with an API key. Moving to OAuth is a larger lift than the other direction.

## High-level flow

1. Register an OAuth app on Chutes via `POST /idp/apps`. You get a `client_id` (`cid_...`) and a `client_secret` (`csc_...`) — the secret is returned **once** and must be stored immediately.
2. Your app's `/api/auth/chutes/login` route redirects the user to Chutes' authorization endpoint with PKCE parameters.
3. The user consents. Chutes redirects back with an authorization code.
4. Your `/api/auth/chutes/callback` route exchanges the code for access / id / refresh tokens server-side.
5. Your app stores the session (encrypted cookie, Redis, etc.). The access token goes in `Authorization: Bearer ...` when your server calls `https://llm.chutes.ai/v1/...` on the user's behalf.
6. The `useChutesSession` hook exposes `user`, `signIn`, `signOut` to the client.

Full PKCE flow diagram: `plugins/chutes-ai/skills/chutes-sign-in/references/oauth-flow.md`.

## Key endpoints

| Endpoint | Purpose |
|---|---|
| `POST /idp/apps` | Create an OAuth app |
| `GET /idp/apps` / `GET /idp/apps/{id}` | List / read app |
| `PATCH /idp/apps/{id}` | Update metadata (redirect URIs, scopes, …) |
| `POST /idp/apps/{id}/regenerate-secret` | Rotate the client secret |
| `DELETE /idp/apps/{id}` | Delete the app |
| `GET /idp/scopes` | List available OAuth scopes |
| `GET /idp/authorizations` / `DELETE /idp/authorizations/{id}` | Inspect / revoke authorizations |
| `POST /idp/token/introspect` | RFC 7662 token introspection |
| `POST /idp/token/revoke` | Revoke a token |
| `GET /idp/userinfo` | Standard OIDC userinfo |
| `POST /idp/authorize` / `POST /idp/token` | The OAuth + PKCE dance itself |

## Scopes

Default: `openid profile chutes:invoke`. Opt-in: `account:read`, `billing:read`. Least-privilege recipes: `plugins/chutes-ai/skills/chutes-sign-in/references/scope-cookbook.md`.

## Supported frameworks

| Framework | Status | Path |
|---|---|---|
| Next.js App Router | ✅ shipped upstream | `docs/frameworks/nextjs-sign-in-with-chutes.md` |
| Next.js Pages Router | 🚧 upstream pending | installer stubs |
| Express / Node | 🚧 upstream pending | installer stubs |
| FastAPI / Python | 🚧 upstream pending | installer stubs |

Until upstream ships the other adapters, the `install_siwc.py` script refuses to vendor anything except Next.js App Router files, and points users at `plugins/chutes-ai/skills/chutes-sign-in/references/oauth-flow.md` + `idp-endpoints.md` for manual implementation.

## Related

- `plugins/chutes-ai/skills/chutes-sign-in/SKILL.md` — full walkthrough
- `docs/oauth-app-management.md` — operator flows (rotate, revoke, audit)
- `docs/oauth-scope-cookbook.md` — scope recipes
- `docs/frameworks/nextjs-sign-in-with-chutes.md` — Next.js walkthrough
- Upstream: https://github.com/chutesai/Sign-in-with-Chutes
