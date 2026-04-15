---
name: chutes-agent-registration
status: beta
description: "[BETA STUB — not yet implemented] Chutes.ai agent-native onboarding. Use when an autonomous agent needs to self-register on Chutes without human signup, bootstrap its own account, and set up its first API key programmatically. Triggers on: chutes agent registration, agent signup, agent_registration, agent setup, programmatic chutes signup, hotkey agent register, autonomous chutes onboarding."
---

# chutes-agent-registration **[BETA — wave 2 stub]**

> **Status: BETA** — stub only. The endpoints are documented here so triggers do not leak back to `chutes-core` when a user asks about agent self-onboarding, but the signature flow, hotkey/coldkey handling, and setup walkthrough are wave 2 work.

## Scope (when filled in)

- Programmatic agent account creation via `/users/agent_registration` (returns payment address, requires signature).
- Status polling via `/users/agent_registration/{hotkey}` until the account is ready.
- One-time setup via `/users/{user_id}/agent_setup` to receive the initial configuration.
- Storing the returned API key and fingerprint in the shared credential manager under a dedicated profile (e.g. `--profile agent`).
- Guidance on when agent registration is the right on-ramp vs. a human-owned account with a delegated API key.

## Wave-3 live constraints discovered outside this stub (verified 2026-04-15)

- Human-owned account registration was not fully autonomous in practice.
- A one-time token from `https://rtok.chutes.ai/users/registration_token` was required.
- That token was behind Cloudflare/browser verification and may be IP-bound.
- The registering coldkey needed at least `0.25 TAO`.

Until this flow is better documented or changed upstream, assume agent bootstrap may still require a human to complete the verification/token handoff step.

## Endpoint map

| Area | Endpoint |
|---|---|
| Register agent | `POST /users/agent_registration` |
| Poll registration | `GET /users/agent_registration/{hotkey}` |
| Finalize setup | `POST /users/{user_id}/agent_setup` |
| Credential storage | `plugins/chutes-ai/skills/chutes-core/scripts/manage_credentials.py` |

## Status

Do not execute this skill yet. Human-signup onboarding continues to live in `chutes-core`.
