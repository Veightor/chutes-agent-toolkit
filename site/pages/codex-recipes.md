# Page draft: `chutes.ai/agents/codex/recipes` — "Codex + Chutes recipes"

> Status: draft copy for the Chutes site. Use as cards, accordions, or short docs beneath the Codex landing page. Every recipe is condensed from [`other-agents/codex/README.md`](../../other-agents/codex/README.md) and the live-verified cookbook; this repo does not claim built-in Chutes support in any upstream Codex build — these are the OpenAI-compatible configuration patterns Codex-style agents and tools accept.

---

## Intro

# Recipes for running Codex-style agents on Chutes

Use these when you want more than a basic completion: per-task model presets, failover pools, a credible smoke test, secure key handling, and a fallback for locked-down runtimes.

Each recipe follows the same rule: Chutes is OpenAI-compatible at `https://llm.chutes.ai/v1`, auth is `Authorization: Bearer`, and the key lives in `CHUTES_API_KEY`.

---

## Recipe 1: Map Chutes into the OpenAI environment variables

**Use when:** Your agent or tool reads the standard OpenAI env vars and accepts a custom base URL.

```bash
export CHUTES_API_KEY="cpk_..."   # from your secret manager — never commit it

export OPENAI_BASE_URL="https://llm.chutes.ai/v1"
export OPENAI_API_KEY="$CHUTES_API_KEY"
```

**Rule of thumb:** keep `CHUTES_API_KEY` as the durable name; map to `OPENAI_API_KEY` only inside tools that require the OpenAI variable name. Do not paste keys into agent prompts, committed config, demo transcripts, or issue comments.

**Site note:** render a "copy" button, but never show a realistic-looking key — `cpk_...` only.

---

## Recipe 2: Configure a config-driven agent

**Use when:** The runtime takes a provider config block instead of env vars.

```json
{
  "provider": "openai-compatible",
  "base_url": "https://llm.chutes.ai/v1",
  "api_key_env": "CHUTES_API_KEY",
  "model": "deepseek-ai/DeepSeek-V3.2-TEE"
}
```

Swap the model (an example ID — IDs churn) for any live ID from `/v1/models`, an inline pool (`"<id1>,<id2>:latency"`), or a `default:*` alias once a routing pool is configured at chutes.ai/app → Model Routing.

**Caveat:** reference the key by env-var name (`api_key_env`), never as a literal, so generated configs stay safe to commit.

---

## Recipe 3: Run the smoke test

**Use when:** You want proof the endpoint and key work before wiring the agent.

```python
import os
from openai import OpenAI

client = OpenAI(
    base_url="https://llm.chutes.ai/v1",
    api_key=os.environ["CHUTES_API_KEY"],
)

response = client.chat.completions.create(
    model="deepseek-ai/DeepSeek-V3.2-TEE",  # any live ID from /v1/models
    messages=[
        {
            "role": "user",
            "content": "Reply with one short sentence confirming Chutes is configured.",
        }
    ],
)
print(response.choices[0].message.content)
```

**Verify properly:** `GET https://llm.chutes.ai/v1/models` is public, so a successful model-list call does not prove the key works. Validate credentials with an authenticated completion or `GET https://api.chutes.ai/users/me`.

---

## Recipe 4: Pick a model per coding task

**Use when:** One static model ID is serving interactive loops, review, planning, and background work alike.

The `default:*` aliases below assume a routing pool configured once at chutes.ai/app → Model Routing; without one, use a live model ID or an inline pool string instead.

| Codex-style task | Model value | Why |
|---|---|---|
| Interactive coding | `default:latency` | Fastest first token and failover during edit-test loops. |
| Code review | Live model ID with `tools`, `json_mode`, and `reasoning`, or `default:latency` | Use current `/v1/models` metadata when you need explicit capabilities. |
| Planning and architecture | Long-context live model ID with `reasoning` | Context windows and reasoning support change; query the catalog first. |
| Background docs, summaries, lint triage | Cheapest suitable live model ID, or `default:throughput` | Cost-aware bulk work without blocking on one static model. |
| Private or sensitive workflows | Any live model with `confidential_compute: true` | The boolean is the source of truth, not the `-TEE` suffix. |

Avoid hardcoding dated model claims in agent prompts:

```bash
curl https://llm.chutes.ai/v1/models
```

Then choose from the returned `id`, `pricing`, `context_length`, `input_modalities`, `supported_features`, `supported_sampling_parameters`, and `confidential_compute` fields.

---

## Recipe 5: Let a script do the picking

**Use when:** You want the presets table computed from live data instead of read by a human.

```bash
# Cheapest tool-capable models, emitted as an inline latency pool
python3 scripts/pick_model.py --task agentic --routing latency

# Other useful calls
python3 scripts/pick_model.py --need tools,structured_outputs --modality image
python3 scripts/pick_model.py --task cheap --max-input-price 0.2 --json
```

It queries `GET https://llm.chutes.ai/v1/models` (public, no auth) and falls back to the repo's daily snapshot when offline. The `--routing latency` output is an inline pool string you can paste straight into the `model` field — zero dashboard setup needed.

---

## Recipe 6: Sidecar fallback for locked-down runtimes

**Use when:** Your Codex runtime does not expose custom provider configuration.

Keep Chutes in a sidecar tool, SDK-backed task runner, MCP server, or repo-local script until that runtime offers a supported provider surface. Starting points, all live-verified 2026-06-11 in the cookbook:

- [`cookbook/python/01_first_call.py`](../../cookbook/python/01_first_call.py) — minimal completion + token usage
- [`cookbook/python/03_tool_calling.py`](../../cookbook/python/03_tool_calling.py) — function-calling round-trip
- [`cookbook/python/04_structured_output.py`](../../cookbook/python/04_structured_output.py) — JSON-schema-enforced output
- [`cookbook/python/05_routing_failover.py`](../../cookbook/python/05_routing_failover.py) — inline multi-model pool + `:latency`
- [`cookbook/python/07_mini_agent.py`](../../cookbook/python/07_mini_agent.py) — a complete tool-calling agent loop in ~100 lines

---

## Recipe 7: First-run demo prompts

**Use when:** Setup is done and you want to exercise the agent on real coding work.

Verbatim from the Codex guide:

```text
Audit this repository for the smallest failing test path, patch the bug, and rerun only the relevant test command. Use Chutes through CHUTES_API_KEY and do not print secrets.
```

```text
Review this diff for correctness risks, missing tests, and stale model assumptions. Ground any Chutes model recommendation in /v1/models.
```

```text
Plan a migration from one hardcoded model ID to Chutes routing aliases for interactive coding, code review, and background tasks.
```

```text
Rewrite this agent landing-page copy so it explains confidential_compute benefits without claiming cryptographic attestation unless DCAP verification ran.
```

---

## Troubleshooting card

| Symptom | Likely cause | Fix |
|---|---|---|
| `429` on a completion you authenticated | `X-API-Key` is silently ignored on inference → anonymous rate-limit path | Use `Authorization: Bearer` with the `cpk_` key |
| `200` from `/v1/models`, completions fail | `/v1/models` is public and never validated your key | Test against `GET https://api.chutes.ai/users/me` |
| `model not found` | Stale hardcoded model ID | Re-query `GET /v1/models`; IDs churn |
| `default:latency` / `default:throughput` fails | No routing pool configured | Set one up once at chutes.ai/app → Model Routing, or use a concrete ID / inline pool |
| Tool call ignored | Model's `supported_features` lacks `tools` | Pick a tool-capable model (`scripts/pick_model.py --task agentic`) |
| Runtime rejects the provider config | That Codex build doesn't expose custom provider knobs | Use Recipe 6 (sidecar/SDK/MCP/repo-script fallback) |

---

## Which recipe do I need?

1. Runtime reads OpenAI env vars? → Recipe 1, then Recipe 3 to verify.
2. Runtime takes a provider config block? → Recipe 2, then Recipe 3.
3. Runtime exposes neither? → Recipe 6 (sidecar fallback).
4. One model serving every task? → Recipe 4, automated by Recipe 5.
5. Working but want proof it's exercised end to end? → Recipe 7.

Routing aliases vs. concrete IDs, one more time: `default:*` needs a one-time pool at chutes.ai/app → Model Routing; concrete IDs from `/v1/models` and inline pool strings (`"<id1>,<id2>:latency"`) work with zero setup. Use concrete IDs whenever a task requires a specific context window, modality, tool support, or price.

---

## Build notes (not page copy)

- Turn each recipe into a card with a "copy" button and a deep link to `other-agents/codex/README.md` (the canonical guide and source of truth for endpoint facts, presets, demo prompts, and limitations).
- Keep the guide's honesty framing visible: status is guide_only (`data/agent-use-cases.json`); Codex-specific built-in provider support is not claimed by this repo. Don't let card copy drift into "Codex supports Chutes natively."
- Live-driven vs. static: model IDs in Recipes 2-3 and any pricing/capability claims must render from `/v1/models` (or be visibly marked as examples); the auth rule, env-var mapping, config shape, and routing-alias prerequisite are stable copy.
- Code snippets trace to `cookbook/python/` (live-verified 2026-06-11) and `scripts/pick_model.py`; keep them in sync — if a cookbook example breaks, the site snippet is broken too.
- Auth fact to preserve in any snippet review: Bearer everywhere; `X-API-Key` is silently ignored on inference (verified live 2026-06-11, see `docs/endpoint-guide.md`).
- Key placeholders are `cpk_...` or `$CHUTES_API_KEY` only.
