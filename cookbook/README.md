# Chutes Cookbook

Small, runnable examples for every core capability of the Chutes inference API. Each file is self-contained, takes its key from `CHUTES_API_KEY`, and prints what it costs to run (these are paid calls — fractions of a cent each at current pricing).

These files are also the **source of truth for code snippets on chutes.ai page drafts** (see [`../site/`](../site/README.md)): if an example here breaks, the site snippet is broken too.

## Setup

```bash
pip install openai                      # the only Python dependency
export CHUTES_API_KEY=cpk_...      # from https://chutes.ai/auth/start
# optional: override the default model used by the examples
export CHUTES_MODEL=deepseek-ai/DeepSeek-V3.2-TEE
```

If you use the toolkit's keychain store, export inline without echoing the secret:

```bash
export CHUTES_API_KEY="$(python plugins/chutes-ai/skills/chutes-ai/scripts/manage_credentials.py get --field api_key)"
```

## Python

| File | Shows | Default model |
|---|---|---|
| [`python/01_first_call.py`](python/01_first_call.py) | Minimal chat completion + token usage | cheapest in catalog |
| [`python/02_streaming.py`](python/02_streaming.py) | SSE streaming deltas | cheapest in catalog |
| [`python/03_tool_calling.py`](python/03_tool_calling.py) | Function calling round-trip | Gemma-4-31B-turbo |
| [`python/04_structured_output.py`](python/04_structured_output.py) | JSON-schema-enforced output | Gemma-4-31B-turbo |
| [`python/05_routing_failover.py`](python/05_routing_failover.py) | Inline multi-model pool + `:latency` strategy | 3-model pool |
| [`python/06_vision.py`](python/06_vision.py) | Image input | Qwen3.6-27B |
| [`python/07_mini_agent.py`](python/07_mini_agent.py) | **A complete tool-calling agent loop in ~100 lines** | Gemma-4-31B-turbo |

## JavaScript

| File | Shows |
|---|---|
| [`javascript/chat.mjs`](javascript/chat.mjs) | Chat + streaming with the OpenAI SDK (`npm i openai`) |

## Conventions

- Auth is always `Authorization: Bearer cpk_...` — the OpenAI SDKs do this by default. Never use `X-API-Key` (silently ignored on inference).
- Model IDs churn. Examples default to known-good IDs but accept `CHUTES_MODEL`; when in doubt, `curl https://llm.chutes.ai/v1/models` (public) and pick from `data[].id`.
- Feature support varies per model — check `supported_features` before assuming tools/JSON mode work.

## Verification status

Labels follow the repo's [BETA policy](../docs/roadmap.md#beta-labeling-policy): each example is marked in its docstring header as **[VERIFIED <date>]** (ran live against the paid API) or **[BETA]** (syntax-checked, not yet exercised live).

**Examples 01–07 (+ chat.mjs) were run live on 2026-10-07** against the paid API (key from the toolkit keychain, total spend well under $0.01; defaults re-pointed at live models after MiniMax-M2.5-TEE and GLM-5-TEE left the catalog). A former 08 video-generation example was removed 2026-10-07 after its target chute (vonkaiser-minimaxh3fl2va) was delisted; the media-chute pattern and its hard-won gotchas live in [docs/endpoint-guide.md §7](../docs/endpoint-guide.md). Findings from those runs, preserved as gotchas:

- `05_routing_failover.py` — both the plain pool and the `:latency` strategy returned HTTP 200; `resp.model` reports the pool member that actually served the request.
- `06_vision.py` — remote image URLs are fetched **server-side by Chutes**, and some hosts (Wikimedia returned 403) block that fetcher. The example now ships a data-URI test image; the model described it correctly.
- `07_mini_agent.py` — Gemma-4-31B-turbo completed the two-tool chain (calculator → letter count) in two turns with no retries (2026-10-07 run; MiniMax-M2.5 did the same on the 2026-06-11 run before it was delisted).
