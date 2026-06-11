---
name: chutes-platform-ops
description: "Chutes.ai platform operations for Hermes users: OAuth app fleet audits, bulk secret rotation dry-runs, alias CRUD/audits, token introspection and revocation guidance. Triggers on: chutes platform ops, oauth fleet, audit stale apps, rotate all secrets, alias crud, revoke token, introspect token, /idp/apps, /model_aliases/."
version: 0.2.0
author: Chutes Agent Toolkit
license: MIT
metadata:
  hermes:
    tags: [chutes, ops, oauth, aliases, tokens, hermes]
    status: mixed
---

# Chutes Platform Ops for Hermes

> Status: MIXED. `list_apps.py`, `audit_stale_apps.py`, `rotate_all.py --dry-run`, and `alias_crud.py` were verified live on 2026-04-13. `introspect_token.py` and `revoke_token.py` remain BETA until run against a real OAuth access token. Full skill lives at `plugins/chutes-ai/skills/chutes-platform-ops/`.

## When to use this skill

Use when a Hermes user wants to:
- List or audit Chutes OAuth apps they own.
- Find stale redirect URIs, overbroad scopes, or old client secrets.
- Dry-run bulk client-secret rotation.
- Inspect or manage model aliases at the platform-ops layer.
- Introspect or revoke OAuth tokens from a completed Sign in with Chutes flow.

## Hermes-facing workflow

Run from the repo root:

```bash
python plugins/chutes-ai/skills/chutes-platform-ops/scripts/list_apps.py
python plugins/chutes-ai/skills/chutes-platform-ops/scripts/audit_stale_apps.py
python plugins/chutes-ai/skills/chutes-platform-ops/scripts/rotate_all.py --dry-run
python plugins/chutes-ai/skills/chutes-platform-ops/scripts/alias_crud.py list
```

Token-specific scripts require a real OAuth access token and stay BETA:

```bash
python plugins/chutes-ai/skills/chutes-platform-ops/scripts/introspect_token.py --token <oauth-access-token>
python plugins/chutes-ai/skills/chutes-platform-ops/scripts/revoke_token.py --token <oauth-access-token>
```

## Deep references

- `plugins/chutes-ai/skills/chutes-platform-ops/SKILL.md`
- `plugins/chutes-ai/skills/chutes-sign-in/SKILL.md`
- `plugins/chutes-ai/skills/chutes-routing/SKILL.md`

## Safety rules

- Do not rotate production app secrets without an explicit rollout plan.
- Never print `csc_`, OAuth access tokens, or `cpk_` values.
- Alias mutation and token revocation are real side effects; require explicit confirmation.
