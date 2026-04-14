---
name: chutes-platform-ops
status: beta
description: "[BETA STUB — not yet implemented] Chutes.ai platform operator flows: OAuth app CRUD, client-secret rotation, token introspection/revocation, authorization management, model alias CRUD. Use when the user asks to rotate a secret, introspect or revoke a Chutes OAuth token, manage authorizations, or audit OAuth apps. Triggers on: chutes oauth app, rotate client secret, token introspect, token revoke, authorizations, regenerate-secret, /idp/apps, /idp/token."
---

# chutes-platform-ops **[BETA — wave 2 stub]**

> **Status: BETA** — stub only. Client-secret rotation during SIWC setup is covered by `chutes-sign-in`'s `rotate_secret.py`. Broader operator flows (token introspection, revocation, bulk auth audits) live here but are not yet implemented.

## Scope (when filled in)

- OAuth app lifecycle: create, update, delete, regenerate secret, list authorizations.
- Token hygiene: introspect, revoke, bulk cleanup of dormant tokens.
- Model alias CRUD as a platform concern (team conventions, alias packs).
- App sharing / admin workflows, chute share/unshare/make_public audits.

## Endpoint map

| Area | Endpoint |
|---|---|
| OAuth apps | `GET/POST/PATCH/DELETE /idp/apps`, `POST /idp/apps/{id}/regenerate-secret` |
| OAuth scopes | `GET /idp/scopes` |
| Authorizations | `GET /idp/authorizations`, `DELETE /idp/authorizations/{app_id}` |
| Token lifecycle | `POST /idp/token/introspect`, `POST /idp/token/revoke` |
| Userinfo | `GET /idp/userinfo` |
| Model aliases | `GET/POST/DELETE /model_aliases/` |
| Chute sharing | `POST /chutes/share`, `POST /chutes/unshare`, `POST /chutes/make_public` |

## Status

Do not execute this skill yet. For SIWC-specific secret rotation, use `chutes-sign-in` → `rotate_secret.py`.
