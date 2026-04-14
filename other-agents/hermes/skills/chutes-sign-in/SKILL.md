---
name: chutes-sign-in
description: "[BETA] Add Sign in with Chutes (OAuth 2.0 + OIDC + PKCE) to a Hermes user's application. Registers OAuth apps via /idp/apps, vendors chutesai/Sign-in-with-Chutes Next.js files, wires server-side token handling, and manages client-secret rotation. Triggers on: sign in with chutes, SIWC, OAuth app, /idp/apps, cid_, csc_, PKCE chutes, chutes login button, rotate oauth secret."
version: 0.1.0
author: Chutes Agent Toolkit
license: MIT
metadata:
  hermes:
    tags: [chutes, oauth, pkce, siwc, sign-in, beta]
    status: beta
---

# Chutes Sign-In for Hermes **[BETA]**

> **Status: BETA** — mirrors the Claude-plugin version at `plugins/chutes-ai/skills/chutes-sign-in/`. Shared scripts and references live there; this skill is a thin Hermes entry point. BETA until a live register → vendor → verify → rotate run is recorded.

## When to use this skill

A Hermes user wants to:

- Turn their Next.js App Router app into a Chutes OAuth relying party.
- Register a new OAuth app on Chutes and store its `cid_` / `csc_` safely.
- Vendor the upstream `chutesai/Sign-in-with-Chutes` Next.js package.
- Manage scopes (`openid profile chutes:invoke` default; `account:read` / `billing:read` opt-in).
- Rotate a client secret without leaking it.
- Understand PKCE, token introspection, and logout/revoke semantics.

If the user just wants to *call* Chutes inference as Hermes' model backend — without letting end-users sign in — that's the hub `chutes-ai` skill, not this one.

## Walkthrough (Hermes-facing)

The full walkthrough and scripts live at `plugins/chutes-ai/skills/chutes-sign-in/`. Hermes users run the same scripts from the repo root:

```bash
# 1. Register the OAuth app
python plugins/chutes-ai/skills/chutes-sign-in/scripts/register_oauth_app.py \
  --name "My Hermes App" \
  --homepage-url https://myapp.example.com \
  --redirect-uri http://localhost:3000/api/auth/chutes/callback \
  --scope openid --scope profile --scope chutes:invoke \
  --profile oauth.my-app

# 2. Vendor the upstream Next.js package into the target app
python plugins/chutes-ai/skills/chutes-sign-in/scripts/install_siwc.py \
  --target /path/to/next-app --profile oauth.my-app

# 3. Verify
python plugins/chutes-ai/skills/chutes-sign-in/scripts/verify_siwc.py \
  --target /path/to/next-app --profile oauth.my-app

# 4. Rotate (when needed)
python plugins/chutes-ai/skills/chutes-sign-in/scripts/rotate_secret.py \
  --profile oauth.my-app
```

Credentials flow through `plugins/chutes-ai/skills/chutes-ai/scripts/manage_credentials.py` — Hermes users share the keychain store with Claude users.

## Deep references (read in order when needed)

- `plugins/chutes-ai/skills/chutes-sign-in/SKILL.md` — full walkthrough
- `plugins/chutes-ai/skills/chutes-sign-in/references/oauth-flow.md` — PKCE + token lifecycle
- `plugins/chutes-ai/skills/chutes-sign-in/references/idp-endpoints.md` — `/idp/*` endpoint map
- `plugins/chutes-ai/skills/chutes-sign-in/references/scope-cookbook.md` — least-privilege recipes
- `plugins/chutes-ai/skills/chutes-sign-in/references/frameworks/nextjs.md` — the only shipped framework today
- `docs/sign-in-with-chutes.md` — repo-level overview (when published)

## Safety rules (same as the Claude skill)

- Never echo `csc_...` into conversation. Secrets route through `manage_credentials.py` via subprocess.
- Never auto-edit user source files. Vendor into a package dir, print the layout diff, let the user apply it.
- Never auto-redeploy on secret rotation. Print the reminder and stop.
- Pages Router / Express / FastAPI integrators stub out until upstream ships them.

## Related Hermes skills

- `chutes-ai` (Hermes hub) — prerequisite for API key + custom-provider setup.
- `chutes-mcp-portability` **[BETA]** — exposes `chutes_oauth_introspect` as an MCP tool Hermes itself can call.
