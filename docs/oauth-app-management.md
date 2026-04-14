# OAuth App Management on Chutes

> **Status: BETA** — applies to the `/idp/apps` surface area. Verify endpoint paths against `https://api.chutes.ai/openapi.json` before production use.

## Lifecycle

```
    POST /idp/apps           ──► create, receive client_id + client_secret (ONCE)
    GET  /idp/apps/{id}      ──► inspect
    PATCH /idp/apps/{id}     ──► update metadata, redirect URIs, scopes
    POST /idp/apps/{id}/
         regenerate-secret   ──► rotate
    DELETE /idp/apps/{id}    ──► delete
```

## Creating an app

```
POST /idp/apps
Authorization: Bearer cpk_...
Content-Type: application/json

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

Response returns `app_id`, `client_id` (`cid_...`), `client_secret` (`csc_...`). **The secret is returned only once.**

Store both immediately via the credential manager:

```bash
python plugins/chutes-ai/skills/chutes-ai/scripts/manage_credentials.py \
  set-profile --profile oauth.my-app --client-id cid_... --client-secret csc_...
```

Or better: use `register_oauth_app.py` which wraps the POST + keychain write in one step so the secret never touches transcript.

## Updating metadata

```
PATCH /idp/apps/{app_id}
{
  "name": "Renamed App",
  "redirect_uris": [...],
  "homepage_url": "..."
}
```

Scope changes may require user re-consent on next login. Plan rollouts with this in mind.

## Rotating the client secret

```
POST /idp/apps/{app_id}/regenerate-secret
```

Response contains the new `client_secret`. The old secret is **invalidated immediately**. Every running service that had the old value loaded will start failing OAuth token exchanges until you update its config.

Safe rotation procedure:

1. Announce the rotation window internally.
2. Run `rotate_secret.py --profile oauth.my-app`. The script rotates the secret, writes the new value to the keychain, and prints a redeploy checklist.
3. Update env vars on every deployment (Vercel, Docker, bare metal) and redeploy.
4. Verify each service is healthy via `POST /idp/token/introspect` with a live access token.
5. Do **not** skip the redeploy step. The script does not auto-redeploy on purpose — blast radius is too large.

## Authorizations

```
GET /idp/authorizations
```

Lists every user who has granted your app a token. Useful for audits ("who is using our app").

```
DELETE /idp/authorizations/{app_id}
```

Revokes all active grants against a specific app. Users will see a fresh consent screen next time. Use this when you discover a compromised app or when you've materially changed scopes.

## Deletion

```
DELETE /idp/apps/{app_id}
```

Hard delete. Any outstanding access tokens become invalid. Does not delete the credentials from the keychain — clean up manually with `manage_credentials.py delete --profile oauth.my-app`.

## Security checklist

- [ ] `client_secret` is stored in the OS keychain, never in a plaintext file or `.env` in a git repo.
- [ ] `.env.local` (or equivalent) is in `.gitignore`.
- [ ] Rotation procedure is documented for your team — rotating is only useful if someone actually knows how to do it.
- [ ] Redirect URIs are pinned to exact URLs, not wildcard patterns.
- [ ] Scope list is minimal. `account:read` / `billing:read` are opt-in, not defaults.
- [ ] On logout, the app calls `POST /idp/token/revoke` for the refresh token.
- [ ] Authorizations audit runs periodically (`GET /idp/authorizations`).

## Related

- `docs/sign-in-with-chutes.md`
- `docs/oauth-scope-cookbook.md`
- `plugins/chutes-ai/skills/chutes-sign-in/references/idp-endpoints.md`
- `plugins/chutes-ai/skills/chutes-sign-in/scripts/rotate_secret.py`
