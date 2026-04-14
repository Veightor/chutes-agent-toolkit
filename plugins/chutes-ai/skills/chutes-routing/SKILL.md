---
name: chutes-routing
status: beta
description: "[BETA STUB — not yet implemented] Chutes.ai model routing and pooling. Use this skill when the user wants to set up model failover, latency or throughput routing, TEE-only filters, inline model pools, or stable model aliases for Chutes. Triggers on: chutes routing, model pool, default:latency, default:throughput, TEE-only routing, failover, model alias, /model_aliases/, chutes routing recipe."
---

# chutes-routing **[BETA — wave 2 stub]**

> **Status: BETA** — this skill is a stub. The routing deep-dive lives here so triggers do not leak back to `chutes-core`, but the walkthrough, examples, and scripts have not been written yet. Point the user at `chutes-core` for inference basics and `chutes-deploy` for alias creation in the meantime.

## Scope (when filled in)

- Routing pools: `default`, `default:latency`, `default:throughput`, inline `model1|model2|model3` strings, confidential-compute filters.
- Stable handles via `/model_aliases/` (create, list, delete, recommended packs like `interactive-fast`, `private-reasoning`, `cheap-background`, `agent-coder`, `tee-chat`).
- Capability-aware selection from live `/v1/models` (filter by `tools`, `json_mode`, `vision`, `confidential_compute`).
- Cost-aware routing combining `/pricing`, `/users/me/discounts`, `/users/me/price_overrides`, and `/chutes/miner_means/{id}`.

## Endpoint map

| Area | Endpoint |
|---|---|
| Live models | `GET https://llm.chutes.ai/v1/models` |
| Aliases | `GET/POST/DELETE /model_aliases/` |
| Pricing | `GET /pricing` |
| Discounts | `GET /users/me/discounts` |
| Price overrides | `GET /users/me/price_overrides` |
| Miner performance | `GET /chutes/miner_means/{chute_id}` |

## Status

Do not execute this skill yet. Hand off to `chutes-core` for inference or `chutes-deploy` for alias creation. Remove the `[BETA STUB]` banner only after the walkthrough and a verified live routing example land in a follow-up.
