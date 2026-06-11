---
name: chutes-routing
description: "Chutes.ai model routing and pooling. Use this skill when the user wants to set up model failover, latency or throughput routing, TEE-only filters, inline model pools, or stable model aliases for Chutes. Also use when picking a pool for a specific intent (interactive-fast, cheap-background, private-reasoning, agent-coder, tee-chat). Triggers on: chutes routing, model pool, default:latency, default:throughput, TEE-only routing, failover, model alias, /model_aliases/, chutes routing recipe, build a pool, alias pack."
---

# chutes-routing

> **Status: read paths VERIFIED LIVE 2026-06-11** — `build_pool.py` dry-runs (interactive-fast, tee-chat, agent-coder) and `audit_pool.py --alias` exercised against live `/v1/models` + `GET /model_aliases/`. The alias **write** round-trip (`POST /model_aliases/` + `DELETE`) was last verified 2026-04-13 (read-only constraint this run). Originally fleshed out via `docs/chutes-maxi-wave-2.md` Track A.1.

> **Catalog note (2026-06-11):** the hosted LLM gateway is now **TEE-only** — `/v1/models` returns 13 models, every one with `confidential_compute: true` and a `-TEE` id suffix. `--tee-only` and the `private-reasoning` / `tee-chat` filters therefore currently match the entire catalog; they remain useful as future-proofing and as an explicit statement of intent, not as a discriminator. The non-TEE tier (Llama, Qwen2.5, GLM-4.x, etc.) is gone from the gateway.

## What this skill does

Turns a user intent like "I want the fastest interactive chat" into a concrete, cost-aware routing decision. Two lanes:

1. **Pool builder.** Given an intent, filter live `/v1/models` and produce either a comma-separated inline routing string or a stable alias pointing at a list of `chute_ids`.
2. **Pool auditor.** Given an existing routing string or alias, re-check each member against live data and warn about staleness (model removed, price jumped, feature dropped, TEE flag changed).

Why this matters: Chutes ships new checkpoints weekly. Hardcoded model ids rot. A good pool expressed as an alias survives that churn — you repoint the alias, callers don't change code.

## Intents → recipes

| Intent | Filter | Rank by | Routing suffix |
|---|---|---|---|
| `interactive-fast` | text I/O, small context OK | cheapest first | `:latency` |
| `interactive-rich` | `'reasoning' in supported_features`, decent context | quality blend | `:latency` |
| `cheap-background` | text I/O, any `tools` capable | cheapest first | `:throughput` or none |
| `private-reasoning` | `confidential_compute=true` + `'reasoning' in supported_features` | cheapest first | `:latency` |
| `tee-chat` | `confidential_compute=true` + text modality | cheapest first | `:latency` |
| `agent-coder` | `'tools' in supported_features`, long context | quality over cost | none |

Full details in `references/alias-packs.md`.

## Walkthrough

### Step 1 — pick an intent

Ask the user what they're optimizing for. The intents above are a curated shortlist; for open-ended cases, ask which axes matter most (cost, latency, throughput, privacy, context length, tool calling, reasoning).

### Step 2 — build the pool

```bash
python <skill-scripts-dir>/build_pool.py --intent interactive-fast --size 4
```

Default output (live run, 2026-06-11):

```
=== interactive-fast (4 models) ===
  1. Qwen/Qwen3-32B-TEE  TEE  prompt=$ 0.104  completion=$ 0.416  ctx=40960  [json_mode,tools,structured_outputs,reasoning]
  2. google/gemma-4-31B-turbo-TEE  TEE  prompt=$  0.15  completion=$  0.42  ctx=131072  [json_mode,tools,structured_outputs,reasoning]
  3. MiniMaxAI/MiniMax-M2.5-TEE  TEE  prompt=$  0.15  completion=$   1.2  ctx=196608  [json_mode,tools,structured_outputs,reasoning]
  4. Qwen/Qwen3-235B-A22B-Thinking-2507-TEE  TEE  prompt=$0.2989  completion=$1.1957  ctx=262144  [json_mode,structured_outputs,tools,reasoning]

Inline routing string:
  Qwen/Qwen3-32B-TEE,google/gemma-4-31B-turbo-TEE,MiniMaxAI/MiniMax-M2.5-TEE,Qwen/Qwen3-235B-A22B-Thinking-2507-TEE:latency
```

Flags:

- `--intent <name>` — one of the table above, or `custom` to combine `--filter` + `--sort`.
- `--size N` — number of models in the pool (default: 4).
- `--max-prompt-cost <usd>` — cap per 1M prompt tokens.
- `--require-feature <feature>` — repeatable (`tools`, `json_mode`, `reasoning`, `structured_outputs`).
- `--tee-only` — shorthand for `--require-confidential-compute`.
- `--alias <name>` — also `POST /model_aliases/` to pin the pool under a stable handle.
- `--dry-run` — build and print without writing to Chutes.

### Step 3 — pick a routing strategy

The output inline string is pure failover by default. Append one of the strategy suffixes to route per request:

- `:latency` — Chutes picks the lowest-TTFT member right now.
- `:throughput` — Chutes picks the highest-TPS member right now.
- `:premium` — (if documented on your account) prefer premium chutes.

The `default` / `default:latency` / `default:throughput` / inline-list forms are now documented in Chutes' own agent-facing doc at `https://chutes.ai/llms.txt`. The `chat/completions` endpoint itself is live-verified (2026-06-11, direct model id + Bearer, HTTP 200 — notably **without** the `x-chutes-chosen-model` / `x-chutes-strategy` / `x-chutes-fallback-count` extras); routing-string/alias calls were not exercised and stay unverified. See `references/routing-strings-spec.md` for the full grammar.

### Step 4 — audit an existing pool periodically

```bash
python <skill-scripts-dir>/audit_pool.py --routing-string "m1,m2,m3,m4"
# or
python <skill-scripts-dir>/audit_pool.py --alias interactive-fast
```

Checks each member against live `/v1/models`:

- Still exists? (warn if a model disappeared)
- Price delta? (warn if `prompt + completion` cost moved > 20% from the baseline you captured)
- Still has the feature set you selected on? (warn if `tools` got dropped, for instance)
- TEE flag unchanged? (surface if a confidential-compute model flipped)

Not a daemon — a one-shot script. Run it before a release or whenever spend looks wrong.

### Step 5 — pin a stable alias (recommended)

Aliases point at **chute_ids**, not model ids. `build_pool.py --alias <name>` resolves each model id to its `chute_id` and posts `{alias, chute_ids: [...]}` to `/model_aliases/`. Callers then just use `model="<alias>"`.

To delete a stale alias: `python <skill-scripts-dir>/audit_pool.py --alias <name> --delete`.

## Endpoint map

| Purpose | Method | Path |
|---|---|---|
| Live models (source of truth) | GET | `https://llm.chutes.ai/v1/models` |
| List aliases | GET | `/model_aliases/` — returns `[{alias, chute_ids: [uuid, ...], created_at, updated_at}]` (verified 2026-06-11) |
| Create alias | POST | `/model_aliases/` body `{alias, chute_ids: [uuid, ...]}` |
| Delete alias | DELETE | `/model_aliases/{alias}` |
| Per-chute performance (optional) | GET | `/chutes/miner_means/{chute_id}` (200 verified 2026-06-11) |
| Platform pricing (TAO rate, GPU rates) | GET | `/pricing` |
| User discounts | GET | `/users/me/discounts` |
| User price overrides | GET | `/users/me/price_overrides` |

**Wave-2 finding:** `GET /pricing` returns `{tao_usd, compute_unit_estimate, gpu_price_estimates}` — it is **platform-level** pricing, not per-model token pricing. Per-model pricing lives on each model object at `pricing.{prompt, completion, input_cache_read}`. Do not confuse the two.

**Wave-2 finding:** `/v1/models` does **not** expose `average_ttft` / `average_tps` fields. Live latency/throughput ranking is server-side via the `:latency` / `:throughput` routing strategy suffixes; client-side ranking uses cost. For per-chute metrics, `GET /chutes/miner_means/{chute_id}` is the deep-dive endpoint.

## Scripts in this skill

| Script | Purpose | Status |
|---|---|---|
| `scripts/build_pool.py` | Intent → filter + rank + print routing string; optional alias pin | Read path VERIFIED (2026-06-11); alias write path last verified 2026-04-13 |
| `scripts/audit_pool.py` | Re-check an existing routing string or alias against live data | Audit path VERIFIED (2026-06-11); `--delete` path last verified 2026-04-13 |

## Safety rules

- **Always use live `/v1/models`** as the source of truth. Static model snapshots in `references/known-models.md` are convenience; they go stale.
- **Never create an alias without the user explicitly naming it.** Aliases mutate team routing policy. No auto-naming.
- **Never `--delete` an alias without a `--yes` flag** and a prompt. Deletes are hard to reverse (the alias string is forgotten; pools that were using it get errors).
- **Cost filters are advisory, not hard caps.** `--max-prompt-cost` filters the candidate set; it does not enforce per-request billing caps. That's `chutes-usage-and-billing`'s job.

## Related skills

- `chutes-ai` (hub) — account + API key prerequisite.
- `chutes-deploy` **[BETA]** — `alias_deploy.py` is the single-chute pin path; `build_pool.py --alias` here is the multi-chute pool path. Either works.
- `chutes-mcp-portability` — `chutes_list_aliases` (verified) exposes the live alias state as an MCP tool.
- `chutes-usage-and-billing` (stub) — cost discipline complements routing.
- `chutes-platform-ops` (stub) — fleet-level alias CRUD + audits.
