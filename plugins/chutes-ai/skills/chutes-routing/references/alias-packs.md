# Alias Packs — Opinionated Routing Recipes

> Source of truth for recommended alias names. Live `/v1/models` is the source of truth for the actual members; these are intent definitions, not pinned model lists.

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

### 2. `interactive-rich`
- **Filter:** `'reasoning' in supported_features` AND `context_length >= 32768`.
- **Rank:** blend cost and reasoning capability — current implementation: cost ascending with a 20% penalty for models lacking `reasoning`.
- **Strategy suffix:** `:latency`.
- **Size:** 2-3 members. Quality matters more than diversity.
- **Use when:** chat UIs where answer quality matters more than cost.

### 3. `cheap-background`
- **Filter:** text I/O. `'tools' in supported_features` optional.
- **Rank:** cheapest first, full stop.
- **Strategy suffix:** `:throughput` (or none — a single cheapest choice is fine).
- **Size:** 1-2 members. Background jobs tolerate single-model failures; retry wins over pool diversity.
- **Use when:** summarization, tagging, classification, batch ETL.

### 4. `private-reasoning` / `tee-chat`
- **Filter:** `confidential_compute=true`. Add `'reasoning' in supported_features` for `private-reasoning`; add `text` modality for `tee-chat`.
- **Rank:** cheapest first among TEE models.
- **Strategy suffix:** `:latency`.
- **Size:** 3-4 TEE members (pools here are smaller because the TEE subset is smaller).
- **Use when:** sensitive prompts, regulated data, anything where you'd want to explain to an auditor *why* you chose the model.
- **Note:** `chutes-tee` (wave 2) will add attestation verification on top of TEE flag filtering. Flag alone is not cryptographic proof.

### 5. `agent-coder`
- **Filter:** `'tools' in supported_features` AND `context_length >= 65536`.
- **Rank:** quality-leaning — cost ascending with a 30% penalty for quantizations below bf16.
- **Strategy suffix:** none (failover-only; latency matters less for long agent loops than reliability).
- **Size:** 2-3 members.
- **Use when:** code agents, tool-calling loops, anything where a malformed tool response breaks the run.

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
