# Alias Packs — Opinionated Routing Recipes

> Source of truth for recommended alias names. Live `/v1/models` is the source of truth for the actual members; these are intent definitions, not pinned model lists.

> **Catalog snapshot 2026-06-11:** the gateway serves exactly **13 models, all TEE** (`confidential_compute: true`, `-TEE` id suffix). Every model advertises `json_mode`, `tools`, `structured_outputs`, and `reasoning`, so feature filters currently don't discriminate — cost, context length, and modality do. The concrete picks below were generated from live data on that date; always regenerate with `build_pool.py` rather than copying them blindly.

## Why packs

Aliases are the operational primitive that matters most on Chutes. A "pack" is a curated set of aliases that encode a team's routing policy. Pick a pack on day one, point your code at the aliases, and survive model churn with one-line repoints.

## The five intents

Each intent below is defined as **filter + rank + recommended routing strategy**. `build_pool.py --intent <name>` produces a concrete pool from live data.

### 1. `interactive-fast`
- **Filter:** `input_modalities` contains `text`. No `confidential_compute` requirement.
- **Rank:** cheapest first (`pricing.prompt + pricing.completion` ascending).
- **Strategy suffix:** `:latency` — Chutes re-picks per request based on live TTFT.
- **Size:** 3-4 members. Smaller pools win on consistency.
- **Use when:** chat UIs, autocomplete, interactive tools where the user is waiting.
- **Live pick (2026-06-11, `build_pool.py` output):** `Qwen/Qwen3-32B-TEE` ($0.104/$0.416, 41k ctx), `google/gemma-4-31B-turbo-TEE` ($0.15/$0.42, 131k ctx, vision), `MiniMaxAI/MiniMax-M2.5-TEE` ($0.15/$1.20, 196k ctx), `Qwen/Qwen3-235B-A22B-Thinking-2507-TEE` ($0.2989/$1.1957, 262k ctx). Absolute cheapest on platform: `unsloth/Mistral-Nemo-Instruct-2407-TEE` ($0.0245/$0.0978) — note its `/v1/models` entry has **null** `input_modalities`/`supported_features`/`context_length` (verified 2026-06-11), so modality/feature filters exclude it; add it manually if you want it. Same caveat applies to `nvidia/NVIDIA-Nemotron-3-Ultra-550B-A55B-TEE`.

### 2. `interactive-rich`
- **Filter:** `'reasoning' in supported_features` AND `context_length >= 32768`.
- **Rank:** blend cost and reasoning capability — current implementation: cost ascending with a 20% penalty for models lacking `reasoning`.
- **Strategy suffix:** `:latency`.
- **Size:** 2-3 members. Quality matters more than diversity.
- **Use when:** chat UIs where answer quality matters more than cost.
- **Live pick (2026-06-11):** all 13 gateway models advertise `reasoning`, so cost/quantization decide. Frontier-leaning manual picks: `zai-org/GLM-5.1-TEE` ($1.20/$4.00, 202k ctx), `moonshotai/Kimi-K2.6-TEE` ($0.74/$3.50, 262k ctx, text+image+video); budget reasoning: `Qwen/Qwen3-235B-A22B-Thinking-2507-TEE` ($0.2989/$1.1957, 262k ctx, bf16).

### 3. `cheap-background`
- **Filter:** text I/O. `'tools' in supported_features` optional.
- **Rank:** cheapest first, full stop.
- **Strategy suffix:** `:throughput` (or none — a single cheapest choice is fine).
- **Size:** 1-2 members. Background jobs tolerate single-model failures; retry wins over pool diversity.
- **Use when:** summarization, tagging, classification, batch ETL.
- **Live pick (2026-06-11):** `unsloth/Mistral-Nemo-Instruct-2407-TEE` ($0.0245/$0.0978 — by far the cheapest, but see the null-metadata caveat above) or `Qwen/Qwen3-32B-TEE` ($0.104/$0.416) when you need the advertised `tools`/`json_mode` feature set.

### 4. `private-reasoning` / `tee-chat`
- **Filter:** `confidential_compute=true`. Add `'reasoning' in supported_features` for `private-reasoning`; add `text` modality for `tee-chat`.
- **Rank:** cheapest first among TEE models.
- **Strategy suffix:** `:latency`.
- **Size:** 3-4 TEE members.
- **Use when:** sensitive prompts, regulated data, anything where you'd want to explain to an auditor *why* you chose the model.
- **Catalog note (2026-06-11):** the entire hosted gateway is now TEE (13/13 models `confidential_compute: true`), so these intents currently match everything — keep using them anyway: they document intent and stay correct if a non-TEE tier ever returns.
- **Live pick (2026-06-11, `build_pool.py --intent tee-chat` output):** `Qwen/Qwen3-32B-TEE`, `google/gemma-4-31B-turbo-TEE`, `MiniMaxAI/MiniMax-M2.5-TEE`, `Qwen/Qwen3-235B-A22B-Thinking-2507-TEE`.
- **Note:** the `chutes-tee` skill adds attestation verification on top of TEE flag filtering. Flag alone is not cryptographic proof.

### 5. `agent-coder`
- **Filter:** `'tools' in supported_features` AND `context_length >= 65536`.
- **Rank:** quality-leaning — cost ascending with a 30% penalty for quantizations below bf16.
- **Strategy suffix:** none (failover-only; latency matters less for long agent loops than reliability).
- **Size:** 2-3 members.
- **Use when:** code agents, tool-calling loops, anything where a malformed tool response breaks the run.
- **Live pick (2026-06-11):** quality-first manual picks: `moonshotai/Kimi-K2.6-TEE` ($0.74/$3.50, 262k ctx) and `zai-org/GLM-5.1-TEE` ($1.20/$4.00, 202k ctx) — the current frontier coding/agentic pair on the platform (relative benchmark standing reported upstream, unverified as of 2026-06-11); budget agentic workhorse: `MiniMaxAI/MiniMax-M2.5-TEE` ($0.15/$1.20, 196k ctx). The script's cost-leaning ranker picks `google/gemma-4-31B-turbo-TEE`, `Qwen/Qwen3-235B-A22B-Thinking-2507-TEE`, `MiniMaxAI/MiniMax-M2.5-TEE` — override toward Kimi/GLM when run quality matters more than spend.

## Using a pack

Pick the intents you need. For each:

```bash
python plugins/chutes-ai/skills/chutes-routing/scripts/build_pool.py \
  --intent interactive-fast --alias interactive-fast
python plugins/chutes-ai/skills/chutes-routing/scripts/build_pool.py \
  --intent cheap-background --alias cheap-background
python plugins/chutes-ai/skills/chutes-routing/scripts/build_pool.py \
  --intent tee-chat --alias tee-chat
```

Then in application code:

```python
client.chat.completions.create(model="interactive-fast", ...)
client.chat.completions.create(model="cheap-background", ...)
```

Aliases resolve server-side to the chute_ids you pinned. When Chutes lands a new checkpoint that belongs in an intent, repoint the alias — no code change.

## Lifecycle hygiene

- **Monthly audit.** Run `audit_pool.py --alias <name>` for each alias in your pack. Warns on price drift, missing members, or feature changes.
- **Blue/green alias repoint.** To switch `interactive-fast` to a new pool with zero gap: create `interactive-fast-next` pointing at the new members, A/B traffic briefly, then delete the old `interactive-fast` and rename `interactive-fast-next` (recreate under the final name). Chutes has no native rename — delete + recreate is the pattern.
- **Document what each alias means** in a single `ALIASES.md` in your repo so future engineers know the intent, not just the name.

## Anti-patterns

- **Packs larger than ~6 intents.** More aliases than intent creates alias churn of its own.
- **Team-wide aliases for one-off experiments.** Use personal aliases (`personal/foo-test`) for experiments; promote to the shared pack only after the experiment sticks.
- **Pointing two aliases at the same pool.** If they're the same, they're the same alias. Delete the duplicate.
- **Expecting aliases to survive account migration.** Aliases are account-scoped. Moving between Chutes accounts means recreating the pack.
