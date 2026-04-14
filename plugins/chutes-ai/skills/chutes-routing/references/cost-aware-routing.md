# Cost-Aware Routing

> How to make routing decisions that respect the per-model cost structure + any account-specific discounts or overrides.

## The data

Three endpoints feed cost awareness:

| Source | What it gives you | Update cadence |
|---|---|---|
| `GET /v1/models` — `pricing.{prompt,completion,input_cache_read}` | Per-model USD-per-million-token rates | Changes when Chutes repriced or a new checkpoint lands |
| `GET /users/me/discounts` | Active percentage discounts, scope, expiry | Rare — negotiated / promotional |
| `GET /users/me/price_overrides` | Custom per-model overrides for this account | Rare — negotiated |

Live probe (wave-2 A.1): on the test account `GET /pricing` returned platform-level data (TAO/USD rate, GPU hourly rates) — **not** per-model token pricing. Do not confuse the two. Per-model pricing lives on the model object inside `/v1/models`.

## Effective price formula

```
effective_prompt_cost_per_1M = pricing.prompt
                               * (1 - discount_pct_applicable / 100)
                               * override_multiplier_if_any

# For a single request:
request_cost_usd = (prompt_tokens / 1_000_000) * effective_prompt_cost_per_1M
                 + (completion_tokens / 1_000_000) * effective_completion_cost_per_1M
```

If `pricing.input_cache_read` is lower than `pricing.prompt`, Chutes auto-applies the cache rate to cached prompt prefixes. You don't opt in — the router does it.

## Cost-aware pool selection

`build_pool.py` ranks candidates by `pricing.prompt + pricing.completion` ascending by default. To enforce a ceiling:

```bash
python build_pool.py \
  --intent cheap-background \
  --max-prompt-cost 0.30 \
  --require-feature tools
```

This drops any model whose `pricing.prompt > 0.30` USD per 1M tokens before ranking. Combine with `--require-feature` to keep the capability you need.

## Handling mixed-cost pools

A failover pool with a cheap first member and an expensive tail is fine **if** the cheap member is usually available. If the cheap one is saturated 50% of the time, you end up paying tail-member rates unpredictably. Two options:

1. **Rank by cost, trust `:latency` anyway.** Live TTFT ranking may pick a more expensive member, but the cheap one is still in the pool and will win when free.
2. **Cap the pool cost.** Drop expensive members entirely via `--max-prompt-cost`. Risks: if the cheap ones are all down, you get 5xx instead of fallback to an expensive-but-working option.

Rule of thumb: cap by cost for cost-sensitive use cases; leave the pool mixed for reliability-sensitive ones.

## Discount interaction

Wave-2 live probe showed `/users/me/discounts` returned `[]` on the test account (no active discounts). Scripts handle empty gracefully. When discounts exist, they look roughly like:

```json
[
  {
    "name": "research-endpoint",
    "pct": 25,
    "scope": "research-endpoint",
    "expires_at": "..."
  }
]
```

The `scope` field is important. `"research-endpoint"` means the 25% Harvard research endpoint discount — it applies only when you route through `https://research-data-opt-in-proxy.chutes.ai/v1`, not the main endpoint. `audit_pool.py` surfaces active discounts but does not fold them into the raw price display; apply them yourself with the formula above.

## Price overrides

`/users/me/price_overrides` is for negotiated per-model rates. Empty on most accounts. When present, overrides win over the base `pricing.*` fields. Shape (inferred):

```json
[
  {"model": "deepseek-ai/DeepSeek-V3-0324", "prompt": 0.05, "completion": 0.15}
]
```

Power users who have negotiated overrides should set `--apply-overrides` on `build_pool.py` to compute pool rankings from the effective (overridden) prices rather than the base ones.

## Watch-outs

- **Cache-hit pricing is invisible pre-request.** You see `pricing.input_cache_read`, but whether a given prompt will hit the cache is not knowable from the routing layer. Assume worst case (`pricing.prompt`) when budgeting.
- **TEE chutes cost 2-5× non-TEE.** Don't blindly mix them into a cost-ranked pool unless you actually want TEE semantics — the cheap non-TEE member will dominate, and you lose the privacy property on most requests.
- **Pool cost rankings rot.** Chutes reprices models; a pool that was cheap last quarter may not be today. `audit_pool.py` catches this if you run it monthly.
- **Cost != bill.** Pool construction caps per-token costs at selection time; it does **not** enforce a per-day spend cap. Hard spend limits are `chutes-usage-and-billing`'s job.
