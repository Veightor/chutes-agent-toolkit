# Page draft: `chutes.ai/agents/codex` — "Run Codex-style agents on Chutes"

> Status: draft copy for the Chutes site, condensed from [`other-agents/codex/README.md`](../../other-agents/codex/README.md) (status: guide_only). The Chutes endpoint behavior here was live-verified in the repo's 2026-06-11 refresh. This page does **not** claim that any upstream Codex build ships a built-in Chutes provider; it documents the Chutes setup pattern for Codex-style agents and tools that accept an OpenAI-compatible base URL, Bearer API key, and model value. Refresh model facts from `GET https://llm.chutes.ai/v1/models` before publication.

---

## Hero

# Your coding agent already speaks our API.

Codex-style coding agents — interactive edit-test loops, diff review, planning, background lint triage — run on whatever sits behind an OpenAI-compatible base URL. Chutes is exactly that: open-source models served through the OpenAI API shape, with the current hosted catalog running under `confidential_compute: true` inside TEEs.

If your runtime reads the standard OpenAI environment variables, the whole integration is two exports:

```bash
export OPENAI_BASE_URL="https://llm.chutes.ai/v1"
export OPENAI_API_KEY="$CHUTES_API_KEY"
```

If it's config-driven instead, the shape is just as small:

```json
{
  "provider": "openai-compatible",
  "base_url": "https://llm.chutes.ai/v1",
  "api_key_env": "CHUTES_API_KEY",
  "model": "deepseek-ai/DeepSeek-V3.2-TEE"
}
```

The model value is an example — swap in any live ID from `/v1/models`, an inline pool (`"<id1>,<id2>:latency"`), or a `default:*` alias once a routing pool is configured.

**Primary CTA:** Get a Chutes key
**Secondary CTA:** Open the Codex guide on GitHub

---

## Why coding-agent builders should care

### 1. No provider plugin to wait for

Chutes works through the configuration surface Codex-style agents already expose: OpenAI-compatible env vars, a provider config block, or the OpenAI SDK. There is nothing Codex-specific to install. (Honest flip side: provider surfaces vary by runtime — see the fallback card below.)

### 2. The right model per coding task, from live data

Interactive loops want fastest first token; background docs and lint triage want cheap throughput; planning wants long context and reasoning. The live catalog at `/v1/models` carries `pricing`, `context_length`, `supported_features`, `input_modalities`, and `confidential_compute` for every model, so the agent (or the [model picker](../../scripts/pick_model.py)) can choose per task instead of pinning one ID forever.

### 3. Failover without infrastructure

One model going down shouldn't stall an edit-test loop. Pass a pool inline in the `model` field with zero setup:

```text
model="<id1>,<id2>:latency"
```

Or configure a pool once at chutes.ai/app → Model Routing and call it as `default`, `default:latency`, or `default:throughput`.

### 4. Private by default, verifiable on request

As of 2026-06-11 the hosted LLM catalog is all TEE-backed, but the `confidential_compute` boolean on each model object remains the source of truth — filter on that, not the `-TEE` name suffix. Do not claim cryptographic attestation unless the verification path actually ran.

### 5. A documented fallback when the runtime is locked down

If your Codex runtime does not expose custom provider configuration, keep Chutes in a sidecar tool, SDK-backed task runner, MCP server, or repo-local script until that runtime offers a supported provider surface. The [cookbook](../../cookbook/README.md) ships a complete tool-calling mini agent in ~100 lines as a starting point.

---

## 60-second setup

```bash
# 1. Store the key under its durable name (from your secret manager — never commit it)
export CHUTES_API_KEY="cpk_..."

# 2. See what's live right now (public, no auth)
curl https://llm.chutes.ai/v1/models

# 3. Map into the OpenAI variables only where the tool needs them
export OPENAI_BASE_URL="https://llm.chutes.ai/v1"
export OPENAI_API_KEY="$CHUTES_API_KEY"

# 4. Smoke-test with a concrete model ID (see below)
python3 cookbook/python/01_first_call.py
```

Or run the verbatim smoke test from the guide:

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

`GET /v1/models` is public, so a `200` there does not prove the key works. Validate credentials with an authenticated completion or `GET https://api.chutes.ai/users/me`.

---

## Recommended presets per coding task

Render the model column live where possible. The `default:*` aliases assume a routing pool has been configured once at chutes.ai/app → Model Routing; without one, use a live model ID or an inline pool string instead.

| Codex-style task | Model value | Why |
|---|---|---|
| Interactive coding | `default:latency` | Fastest first token plus failover during edit-test loops. |
| Code review | Live model ID with `tools`, `json_mode`, and `reasoning`, or `default:latency` | Use current `/v1/models` metadata when you need explicit capabilities. |
| Planning and architecture | Long-context live model ID with `reasoning` | Context windows and reasoning support change; query the catalog first. |
| Background docs, summaries, lint triage | Cheapest suitable live model ID, or `default:throughput` for bulk work | Keeps non-interactive work cost-aware without blocking on one static model. |
| Private or sensitive workflows | Any live model with `confidential_compute: true` | Currently the whole hosted catalog, but the boolean stays the source of truth. |

Local helper that implements this table from live data:

```bash
python3 scripts/pick_model.py --task agentic --routing latency
```

---

## Demo prompts

After setup, these are good first-run prompts (verbatim from the guide):

- "Audit this repository for the smallest failing test path, patch the bug, and rerun only the relevant test command. Use Chutes through CHUTES_API_KEY and do not print secrets."
- "Review this diff for correctness risks, missing tests, and stale model assumptions. Ground any Chutes model recommendation in /v1/models."
- "Plan a migration from one hardcoded model ID to Chutes routing aliases for interactive coding, code review, and background tasks."
- "Rewrite this agent landing-page copy so it explains confidential_compute benefits without claiming cryptographic attestation unless DCAP verification ran."

---

## Troubleshooting

| Symptom | Likely cause | Fix |
|---|---|---|
| `429` on a completion you authenticated | `X-API-Key` was sent — it's silently ignored on inference, landing on the anonymous rate-limit path | Use `Authorization: Bearer` (the OpenAI SDKs do this by default) |
| `200` from `/v1/models`, completions fail | `/v1/models` is public and never validated your key | Test against `GET https://api.chutes.ai/users/me` or an authenticated completion |
| `model not found` | Stale hardcoded model ID | Re-query `GET /v1/models`; IDs churn |
| `default:latency` fails | No routing pool configured yet | Configure a pool once at chutes.ai/app → Model Routing, or use a live ID / inline pool string |
| Runtime won't accept a custom provider | That Codex build doesn't expose provider knobs | Use the sidecar/SDK/MCP/repo-script fallback from the guide |

---

## Page sections for design

1. Hero with the two-export env block and the JSON provider shape.
2. Five cards: No plugin needed, Per-task models, Failover, Privacy, Locked-runtime fallback.
3. 60-second setup with the smoke test in a terminal mock.
4. Presets table with a "model picker" widget (port `scripts/pick_model.py`).
5. Demo prompt cards.
6. Troubleshooting accordion.
7. Recipe cards linking to `/agents/codex/recipes`.
8. CTA: GitHub guide, endpoint guide, `/agents/connect`.

---

## Links

- Codex guide (canonical): `other-agents/codex/README.md`
- Universal endpoint guide: `docs/endpoint-guide.md`
- Connect-your-agent page (short Codex tab): `site/pages/connect-your-agent.md`
- Runnable cookbook: `cookbook/README.md`
- Model picker: `scripts/pick_model.py`
- Use-case data: `data/agent-use-cases.json`

---

## Build notes (not page copy)

- **The honesty boundary is load-bearing.** The status blockquote and hero must keep the framing from `other-agents/codex/README.md`: this repo verifies the Chutes endpoint behavior, not built-in Chutes support in any upstream Codex build (`data/agent-use-cases.json` codex entry: `status: guide_only`). If a Codex build ships first-class support later, update the guide first, then this page.
- Never present `default`/`default:latency`/`default:throughput` as zero-setup — they require a pool configured once at chutes.ai/app → Model Routing. Inline pools and concrete IDs are the zero-setup paths.
- Key placeholders are `cpk_...` or `$CHUTES_API_KEY`, never realistic-looking keys. `CHUTES_API_KEY` is the durable name; `OPENAI_API_KEY` is a per-tool mapping only.
- Concrete model IDs in snippets (e.g. `deepseek-ai/DeepSeek-V3.2-TEE`) are examples that churn; render from `/v1/models` at build time or pin a platform-committed alias.
- Source-of-truth files: `other-agents/codex/README.md` (facts, presets, demo prompts, limitations), `docs/endpoint-guide.md` (auth/routing/errors), `cookbook/` (code snippets, live-verified 2026-06-11), `scripts/pick_model.py` (picker widget logic), `data/agent-use-cases.json` (status + proof points).
- Do not rank Codex against other clients on this page; it is one documented path among several (see `/agents/connect` tab order notes).
