# Chutes Routing Strings — Spec

> What the inference router actually accepts as the `model` parameter on `POST https://llm.chutes.ai/v1/chat/completions`. Behavior confirmed via live models, routing string suffixes confirmed via Chutes' dashboard UI.

## Grammar (summary)

```
model_parameter := alias
                 | model_id
                 | model_id_list
                 | model_id_list ":" strategy
                 | alias ":" strategy

alias           := "default"
                 | "<team-alias-name>"          (e.g. "interactive-fast")

model_id        := "<owner>/<name>[-<variant>]" (e.g. "Qwen/Qwen3-32B-TEE")

model_id_list   := model_id ("," model_id)+    (minimum 2 entries)

strategy        := "latency"
                 | "throughput"
                 | "premium"                    (account-dependent)
```

## Rules

1. **Single `model_id`** bypasses routing entirely. Chutes picks the best instance of that one model and calls it.
2. **`alias`** resolves server-side to the stored `chute_ids` list. Failover is implicit.
3. **`model_id_list`** is comma-separated, no spaces, minimum 2 entries. Chutes tries them in order (sequential failover) by default.
4. **Strategy suffixes** (`:latency`, `:throughput`, `:premium`) apply only to `model_id_list` or `alias` — not to a single `model_id`. They re-rank the pool per request.
5. **`default`** is a reserved alias. Every Chutes account has (or can create) one. It points at a user-configured pool via the dashboard.

## Strategy semantics

- **No suffix (failover).** Try members left-to-right. If the first is busy or errors, move to the next. First 2xx wins. Tail-latency dominated by the slowest healthy member.
- **`:latency`.** Chutes re-ranks the pool by live TTFT right now. Pick the fastest first. Failover follows the re-ranking.
- **`:throughput`.** Re-rank by live TPS (tokens-per-second sustained). Pick the highest first.
- **`:premium`.** When present, prefer premium-flagged instances in the pool. Semantics account-dependent; treat as "please" not "must."

## Failover edge cases

- If **every** member in a `model_id_list` 4xx's for a non-retryable reason (bad request body, invalid model id, auth failure), the call fails — failover only triggers on 5xx / rate-limit / unavailable.
- **Context length mismatch** is not retryable: if your prompt is 100k and a pool member has `context_length=32768`, it'll 4xx and the router moves on — so long pools tolerate mixed-context-length members, you just lose the undersized one for that request.
- **Feature mismatch** (`tools` / `structured_outputs` requested against a model that doesn't advertise it) is NOT a routing retry — Chutes may silently ignore the feature, or it may 4xx. Build pools with homogeneous feature support when calling with tools.

## Examples

```python
# 1. Single model, no routing
model="deepseek-ai/DeepSeek-V3-0324"

# 2. Saved alias (preferred for production)
model="interactive-fast"

# 3. Inline failover
model="zai-org/GLM-5-Turbo,Qwen/Qwen3-32B-TEE,deepseek-ai/DeepSeek-V3-0324"

# 4. Inline with latency ranking
model="zai-org/GLM-5-Turbo,Qwen/Qwen3-32B-TEE,deepseek-ai/DeepSeek-V3-0324:latency"

# 5. Alias with throughput ranking
model="cheap-background:throughput"
```

## Inline vs alias — which to pick

| Use alias when | Use inline string when |
|---|---|
| Multiple call sites point at the same pool | One-off ad-hoc call |
| You want to repoint without code deploys | You don't care about churn |
| Pool members change frequently | Pool is stable for the lifetime of this request |
| Auditability matters | Quick experimentation |

Default to aliases. The only reason to use inline strings is speed of iteration.

## What the server returns

Chutes adds non-standard OpenAI response fields when routing kicks in. Common extras:

- `x-chutes-chosen-model` — which member of the pool served the request.
- `x-chutes-strategy` — which strategy resolved.
- `x-chutes-fallback-count` — how many members were tried before success.

These may appear as headers or inside the response body depending on endpoint. Treat them as observability, not as something to depend on in production logic.
