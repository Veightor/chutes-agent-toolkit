# Sign in with Chutes — Express **[STUB — upstream pending]**

> **Status: STUB.** The upstream `chutesai/Sign-in-with-Chutes` repository does not yet ship an Express adapter. This skill refuses to run the installer against Express projects until upstream lands.

## What to tell the user

- The Next.js adapter is the only one shipped today.
- If they need Express right now, they can implement the flow manually using `references/oauth-flow.md` as the spec and `references/idp-endpoints.md` for the endpoint list.
- Track the upstream repo for an Express package. When it lands, this stub becomes a full walkthrough.

## Minimal manual implementation

If the user insists on implementing today, the shape is:

1. `GET /auth/chutes/login` — generate `code_verifier` + `code_challenge`, store both in a server session keyed by `state`, redirect to `GET https://api.chutes.ai/idp/authorize` with the challenge.
2. `GET /auth/chutes/callback?code&state` — look up the session by `state`, `POST https://api.chutes.ai/idp/token` with `grant_type=authorization_code`, `code`, `code_verifier`, `client_id`, `client_secret`, `redirect_uri`. Store the resulting access / refresh tokens in the server session.
3. `GET /auth/chutes/session` — return user info from the session.
4. `POST /auth/chutes/logout` — `POST /idp/token/revoke` and clear the session.

Use any production-grade session store (not in-memory) and read `client_id` / `client_secret` from the keychain via `manage_credentials.py`.

Do not roll your own PKCE unless you have to — the upstream Next.js implementation is the reference.
