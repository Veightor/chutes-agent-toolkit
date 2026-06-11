---
name: chutes-routing
description: "Chutes.ai model routing and pooling for Hermes users: build live model pools, latency/throughput routing strings, TEE-only filters, and stable aliases. Triggers on: chutes routing, model pool, default:latency, default:throughput, TEE-only routing, failover, model alias, /model_aliases/, build a pool, alias pack."
version: 0.2.0
author: Chutes Agent Toolkit
license: MIT
metadata:
  hermes:
    tags: [chutes, routing, aliases, tee, latency, throughput, hermes]
    status: verified-live
---

# Chutes Routing for Hermes

> Status: VERIFIED LIVE 2026-04-13. This is the Hermes entry point for the full skill at `plugins/chutes-ai/skills/chutes-routing/`. Scripts and references stay single-sourced in the plugin tree.

## When to use this skill

Use when a Hermes user wants to:
- Pick the best Chutes model pool for an intent such as `interactive-fast`, `agent-coder`, `private-reasoning`, or `tee-chat`.
- Generate inline routing strings using `:latency` or `:throughput`.
- Create or audit stable Chutes aliases backed by `chute_ids`.
- Re-check a routing pool against live `/v1/models` so stale static model choices do not rot.

## Hermes-facing workflow

Run from the repo root:

```bash
python plugins/chutes-ai/skills/chutes-routing/scripts/build_pool.py \
  --intent interactive-fast --size 4 --dry-run

python plugins/chutes-ai/skills/chutes-routing/scripts/audit_pool.py \
  --routing-string "modelA,modelB,modelC:latency"
```

For a named alias, require the user to choose the alias string explicitly:

```bash
python plugins/chutes-ai/skills/chutes-routing/scripts/build_pool.py \
  --intent private-reasoning --size 4 --tee-only --alias tee-chat
```

## Deep references

- `plugins/chutes-ai/skills/chutes-routing/SKILL.md`
- `plugins/chutes-ai/skills/chutes-routing/references/alias-packs.md`
- `plugins/chutes-ai/skills/chutes-routing/references/routing-strings-spec.md`
- `plugins/chutes-ai/skills/chutes-routing/references/tee-only-routing.md`
- `plugins/chutes-ai/skills/chutes-routing/references/cost-aware-routing.md`

## Safety rules

- Always use `https://llm.chutes.ai/v1/models` as the live source of truth.
- Do not create or delete aliases without explicit user intent; aliases mutate routing policy.
- Cost filters are advisory, not hard caps. For spend controls, load `chutes-usage-and-billing`.
