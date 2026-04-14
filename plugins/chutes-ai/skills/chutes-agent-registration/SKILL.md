---
name: chutes-agent-registration
status: beta
description: "Chutes.ai agent-native onboarding. Use this skill when an autonomous agent needs to self-register on Chutes without a human signup, bootstrap its own Chutes account, and set up its first API key programmatically via a Bittensor hotkey signature. Triggers on: chutes agent registration, agent signup, agent_registration, agent setup, programmatic chutes signup, hotkey agent register, autonomous chutes onboarding, bittensor agent account."
---

# chutes-agent-registration **[BETA]**

> **Status: BETA (dry-run verified only)** — unlike the other wave-2 skills, this skill is **not** live-POST verified because creating a real agent account touches the Bittensor network (on-chain implications beyond "spending a few cents"). `GET /users/agent_registration/{hotkey}` is read-only and was exercised against a sentinel address in wave 2. `POST /users/agent_registration` is exercised in dry-run only (body shape is known). Graduates out of BETA the first time a real agent account is created by someone who actually intends to use it — until then, BETA is the right label.

## What this skill does

Chutes exposes an **agent-native on-ramp**: an autonomous agent can register its own Chutes account via a Bittensor hotkey signature, without a human completing the signup flow. The resulting account has:

- A fingerprint (same primary credential as human accounts).
- An API key (`cpk_...`) for inference calls.
- A balance that can be topped up via the returned payment address.

Useful when: you're building multi-tenant agent infrastructure where each agent instance manages its own Chutes credentials, or when you want an agent to self-provision without calling a human.

Not useful when: a single API key shared across agents is enough, or when the user already has a human-owned Chutes account to delegate from.

## Prerequisites

- A **Bittensor hotkey + coldkey pair** under your control. The hotkey signs the registration message; the coldkey is the onchain owner.
- Ability to sign a canonical message with the hotkey (via `bittensor-cli`, the Python `bittensor` package, or a raw `substrate-interface` flow).
- Enough TAO on the coldkey to cover any onchain registration fees (Chutes-side; check current rates via `/fmv` + `/pricing`).

## Walkthrough

### Step 0 — decide this is actually the right onramp

Ask: "Would a plain `cpk_` key on a human-owned account work?" If yes, use `chutes-ai` to create a human account and delegate. Agent registration is for genuinely autonomous, multi-tenant, or long-lived agent infrastructure. It is **not** a shortcut to skip the human signup form.

### Step 1 — prepare the signature

The `POST /users/agent_registration` endpoint expects a JSON body with exactly three fields:

```json
{
  "hotkey": "<ss58_hotkey>",
  "coldkey": "<ss58_coldkey>",
  "signature": "<hex_or_base64_signature>"
}
```

The exact canonical message the signature commits to is **not documented in this skill** and varies between Chutes releases — check the latest `chutesai/chutes-api` source for `agent_registration` before signing. Typical shape: `sr25519` signature over a concatenation of the hotkey, coldkey, and a timestamp, but **verify against current code**.

### Step 2 — dry run

```bash
python <skill-scripts-dir>/register_agent.py \
  --hotkey <ss58_hotkey> \
  --coldkey <ss58_coldkey> \
  --signature <sig> \
  --profile agent.myagent \
  --dry-run
```

Prints the exact POST body, confirms the three required fields are present, and exits without touching the network. Default behavior is dry-run.

### Step 3 — live registration (destructive — requires explicit consent)

```bash
python <skill-scripts-dir>/register_agent.py \
  --hotkey <ss58_hotkey> \
  --coldkey <ss58_coldkey> \
  --signature <sig> \
  --profile agent.myagent \
  --yes --i-know-bittensor
```

Both `--yes` and `--i-know-bittensor` are required — the second flag is a tripwire that makes the user acknowledge the onchain implications.

The script:

1. `POST /users/agent_registration` with the body.
2. Polls `GET /users/agent_registration/{hotkey}` every N seconds until the status is `ready` (or the registration errors out).
3. `POST /users/{user_id}/agent_setup` to finalize setup and receive the initial config (API key, fingerprint).
4. Stores the resulting secrets in the keychain under `--profile agent.myagent` (or whatever you passed). Never prints secret values — only redacted previews.

### Step 4 — check status without registering

```bash
python <skill-scripts-dir>/agent_status.py --hotkey <ss58_hotkey>
```

Read-only. `GET /users/agent_registration/{hotkey}`. Prints:

```
status: not_registered      (404 from Chutes — no agent matches this hotkey)
```

or once the hotkey is registered:

```
status: registered
user_id: <uuid>
payment_address: <ss58>
...
```

### Step 5 — top up and use

Once the agent profile is saved:

- Fund the account by sending TAO to the `payment_address` returned from setup.
- Use the stored `api_key` via `manage_credentials.py get --profile agent.myagent --field api_key`.
- All other skills (`chutes-ai`, `chutes-routing`, `chutes-usage-and-billing`, etc.) accept a `CHUTES_PROFILE` env var or `--profile` flag to scope against the agent profile.

## Endpoint map

| Action | Method | Path |
|---|---|---|
| Register an agent | POST | `/users/agent_registration` body `{hotkey, coldkey, signature}` |
| Poll registration status | GET | `/users/agent_registration/{hotkey}` — returns 404 until registered |
| Finalize setup (one-time) | POST | `/users/{user_id}/agent_setup` |
| User info after setup | GET | `/users/{user_id}` or `/users/me` |

**Wave-2 finding:** `POST /users/agent_registration` with an empty body returns 422 with the required-field list: `hotkey`, `coldkey`, `signature`. That's the full required set for the body. Other fields may be optional.

**Wave-2 finding:** `GET /users/agent_registration/{hotkey}` returns HTTP 404 `{"detail":"No agent registration found for this hotkey."}` when the hotkey is not registered. Probed against a sentinel SS58 during verification; confirms the endpoint and error shape.

## Scripts in this skill

| Script | Purpose | Status |
|---|---|---|
| `scripts/register_agent.py` | Dry-run / live POST /users/agent_registration + poll + setup | **[BETA]** dry-run only; live POST not exercised |
| `scripts/agent_status.py` | Read-only `GET /users/agent_registration/{hotkey}` | VERIFIED (2026-04-13) |

## Safety rules

- **Never run `register_agent.py` without `--dry-run` by default.** Both `--yes` AND `--i-know-bittensor` are required for a live POST — the second flag is a deliberate tripwire.
- **Never print or log any signature value.** Signatures are sensitive (they are committed-to-hotkey proofs). Treat them like secrets.
- **Never auto-generate a signature.** This skill does not embed Bittensor signing; users bring their own signature via `--signature` or `--signature-file`. Auto-signing would require shipping wallet material, which is out of scope.
- **Never store hotkey / coldkey private keys in this repo's credential manager.** Only the *returned* API key + fingerprint land in the keychain. The wallet itself is the user's responsibility.
- **Always document the canonical message format being signed.** If Chutes changes it between releases, old scripts will silently fail with 422s that look like "bad signature." Check the upstream API source first.

## Why this stays BETA after wave 2

The other four wave-2 skills graduate with "exercised live" runs. This one does not because the action it performs (create a real agent account tied to a Bittensor wallet) is not reversible cheaply — it creates onchain state, potentially spends TAO, and binds a hotkey. An automated verification pass that creates a throwaway agent account is the wrong shape: the throwaway is real, the onchain state is real, and cleanup is not a `DELETE` call.

Graduation gate: the **first intentional human-initiated agent registration** that references this script's output will graduate it. Until then, treat BETA as "the endpoints are documented and the dry-run path works, but the live path is your responsibility."

## Related skills

- `chutes-ai` (hub) — human-signup onramp. Use this by default unless you really need agent-native registration.
- `chutes-routing`, `chutes-usage-and-billing`, `chutes-platform-ops` — all accept `CHUTES_PROFILE` / `--profile` so they work against agent profiles once set up.
- `chutes-sign-in` — a completely different concept. SIWC is for **users** signing into your app with their Chutes identity. Agent registration is for **agents** owning their own Chutes identity.
