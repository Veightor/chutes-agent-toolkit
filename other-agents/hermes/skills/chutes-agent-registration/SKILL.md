---
name: chutes-agent-registration
description: "[BETA] Chutes.ai autonomous agent registration from Hermes: check registration status, prepare a Bittensor-backed agent account registration, and surface on-chain/coldkey prerequisites. Triggers on: chutes agent registration, register chutes agent, autonomous agent chutes, bittensor agent, coldkey, agent status."
version: 0.2.0
author: Chutes Agent Toolkit
license: MIT
metadata:
  hermes:
    tags: [chutes, agent-registration, bittensor, beta, hermes]
    status: beta
---

# Chutes Agent Registration for Hermes **[BETA]**

> Status: BETA. Dry-run verified; creating a real Bittensor-backed agent account has on-chain implications and requires explicit human intent. Full skill lives at `plugins/chutes-ai/skills/chutes-agent-registration/`.

## When to use this skill

Use when a Hermes user wants to:
- Check whether a Chutes account is already registered as an autonomous agent.
- Understand coldkey, hotkey, funding, and on-chain prerequisites.
- Prepare a dry-run registration payload before the user intentionally registers.

Do not use this for normal API-key setup or inference; use `chutes-ai` for that.

## Hermes-facing workflow

Run from the repo root:

```bash
python plugins/chutes-ai/skills/chutes-agent-registration/scripts/agent_status.py
python plugins/chutes-ai/skills/chutes-agent-registration/scripts/register_agent.py --dry-run
```

Only perform a non-dry-run registration after the user explicitly confirms the on-chain implications, funding requirements, and target account.

## Deep references

- `plugins/chutes-ai/skills/chutes-agent-registration/SKILL.md`
- `docs/api-reference.md`
- `docs/credential-store.md`

## Safety rules

- Default to dry-run.
- Never paste `cpk_`, coldkey, hotkey, seed phrase, mnemonic, or registration token values into chat.
- Do not automate funding, wallet creation, or irreversible on-chain operations.
