---
name: chutes-routing
description: "Chutes.ai model routing and pooling. Use this skill when the user wants to set up model failover, latency or throughput routing, TEE-only filters, inline model pools, or stable model aliases for Chutes. Also use when picking a pool for a specific intent (interactive-fast, cheap-background, private-reasoning, agent-coder, tee-chat). Triggers on: chutes routing, model pool, default:latency, default:throughput, TEE-only routing, failover, model alias, /model_aliases/, chutes routing recipe, build a pool, alias pack."
---

# chutes-routing

> **Status: VERIFIED LIVE 2026-04-13** via `docs/chutes-maxi-wave-2.md` Track A.1 — `build_pool.py` dry-runs exercised against live `/v1/models`; one alias round-trip via `POST /model_aliases/` + `DELETE`. Fleshed out from the wave-1 stub.

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

Default output:

```
=== interactive-fast (4 models) ===
  1. <model_id>  prompt=$0.08/1M  completion=$0.24/1M  ctx=131072
  2. <model_id>  prompt=$0.11/1M  completion=$0.33/1M  ctx=65536
  ...

Inline routing string (append :latency or :throughput as needed):
  <m1>,<m2>,<m3>,<m4>

Example usage:
  response = client.chat.completions.create(
      model="<m1>,<m2>,<m3>,<m4>:latency",
      messages=[...],
  )
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

See `references/routing-strings-spec.md` for the full grammar.

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
| List aliases | GET | `/model_aliases/` |
| Create alias | POST | `/model_aliases/` body `{alias, chute_ids: [uuid, ...]}` |
| Delete alias | DELETE | `/model_aliases/{alias}` |
| Per-chute performance (optional) | GET | `/chutes/miner_means/{chute_id}` |
| Platform pricing (TAO rate, GPU rates) | GET | `/pricing` |
| User discounts | GET | `/users/me/discounts` |
| User price overrides | GET | `/users/me/price_overrides` |

**Wave-2 finding:** `GET /pricing` returns `{tao_usd, compute_unit_estimate, gpu_price_estimates}` — it is **platform-level** pricing, not per-model token pricing. Per-model pricing lives on each model object at `pricing.{prompt, completion, input_cache_read}`. Do not confuse the two.

**Wave-2 finding:** `/v1/models` does **not** expose `average_ttft` / `average_tps` fields. Live latency/throughput ranking is server-side via the `:latency` / `:throughput` routing strategy suffixes; client-side ranking uses cost. For per-chute metrics, `GET /chutes/miner_means/{chute_id}` is the deep-dive endpoint.

## Scripts in this skill

| Script | Purpose | Status |
|---|---|---|
| `scripts/build_pool.py` | Intent → filter + rank + print routing string; optional alias pin | VERIFIED (2026-04-13) |
| `scripts/audit_pool.py` | Re-check an existing routing string or alias against live data | VERIFIED (2026-04-13) |

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
