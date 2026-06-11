# The Chutes Endpoint Guide

**One page. Any agent. Copy, paste, ship.**

This is the universal instruction set for talking to [Chutes.ai](https://chutes.ai) — decentralized, serverless inference for open-source AI models, powered by Bittensor. Every hosted model runs inside a hardware-isolated **TEE** (Trusted Execution Environment), and the whole thing speaks the **OpenAI API**. If your tool can talk to OpenAI, it can talk to Chutes by changing two lines.

> **TL;DR**
> - **Inference base URL:** `https://llm.chutes.ai/v1`
> - **Auth header:** `Authorization: Bearer cpk_...` (everywhere — see [Auth](#2-auth-the-one-rule-that-matters))
> - **It's the OpenAI API.** Point any OpenAI SDK at the base URL above and you're done.
> - **Models change. The list doesn't lie:** `GET https://llm.chutes.ai/v1/models` is public and is the source of truth.

---

## Table of contents

1. [Two base URLs](#1-two-base-urls)
2. [Auth: the one rule that matters](#2-auth-the-one-rule-that-matters)
3. [Get a key in 60 seconds](#3-get-a-key-in-60-seconds)
4. [Your first call (5 languages)](#4-your-first-call-5-languages)
5. [Discover models (and never hardcode)](#5-discover-models-and-never-hardcode)
6. [Smart routing: one request, many models](#6-smart-routing-one-request-many-models)
7. [Streaming, tools, JSON mode, vision](#7-streaming-tools-json-mode-vision)
8. [Privacy: every model is a TEE](#8-privacy-every-model-is-a-tee)
9. [Money: pricing, balance, the 25% research discount](#9-money-pricing-balance-the-25-research-discount)
10. [Errors & gotchas](#10-errors--gotchas)
11. [Endpoint cheat sheet](#11-endpoint-cheat-sheet)
12. [Machine-readable interfaces](#12-machine-readable-interfaces)

---

## 1. Two base URLs

Chutes has exactly two hosts. Keep them straight and everything else is easy.

| Purpose | Base URL | Auth needed? |
|---|---|---|
| **Inference** — chat completions, model list | `https://llm.chutes.ai/v1` | Bearer for completions; `GET /models` is public |
| **Account & platform** — keys, billing, usage, OAuth | `https://api.chutes.ai` | Bearer |

That's it. `llm.chutes.ai` is the OpenAI-compatible inference plane. `api.chutes.ai` is everything else.

---

## 2. Auth: the one rule that matters

```http
Authorization: Bearer cpk_xxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

**Use `Authorization: Bearer` with your `cpk_` key on every authenticated request, on both hosts.** This is exactly what standard OpenAI SDKs send by default — so they work with zero auth glue.

A few hard-won truths (live-verified 2026-06-11):

- ✅ **`Authorization: Bearer cpk_...`** works on `llm.chutes.ai` *and* `api.chutes.ai`, including real paid `POST /v1/chat/completions` (HTTP 200).
- ❌ **`X-API-Key`** is **silently ignored** on the inference plane — a completion sent with it lands on the anonymous rate-limit path (HTTP 429), byte-identical to sending no auth at all — and returns **401** on the management API. Don't use it.
- 🌐 **`GET /v1/models`** needs **no auth**. Convenient for discovery, but a `200` there does **not** prove your key works. Validate keys against an authenticated endpoint (e.g. `GET https://api.chutes.ai/users/me`).

> **Keys are `cpk_`-prefixed and shown exactly once.** Store them in a secret manager or env var. This repo ships a keychain-backed [`manage_credentials.py`](../README.md#secure-credential-store) so agents never paste raw secrets into a chat.

---

## 3. Get a key in 60 seconds

**Humans:** open [chutes.ai/auth/start](https://chutes.ai/auth/start) → create account → create an API key in the [dashboard](https://chutes.ai/app). (Note: the button on `chutes.ai/auth` opens a support widget — always use `/auth/start`.)

**Agents / programmatic:**

```bash
# 1. Register (username: 3–20 chars, alphanumeric). Returns a 32-char fingerprint — shown ONCE.
curl -X POST https://api.chutes.ai/users/register \
  -H "Content-Type: application/json" \
  -d '{"username": "your-handle"}'

# 2. Create an API key (authenticate with the session from step 1).
curl -X POST https://api.chutes.ai/api_keys/ \
  -H "Authorization: Bearer <session>" \
  -H "Content-Type: application/json" \
  -d '{"name": "my-agent-key", "admin": false}'
# → response.secret_key is your cpk_ key. Save it now; it is never shown again.
```

> ⚠️ **The fingerprint is the master credential.** It's displayed once and can only be recovered if you've linked a Bittensor wallet (reset at [chutes.ai/auth/reset](https://chutes.ai/auth/reset)). Back it up immediately.

---

## 4. Your first call (5 languages)

Same request, every ecosystem. Swap in your key and go.

### cURL
```bash
curl https://llm.chutes.ai/v1/chat/completions \
  -H "Authorization: Bearer $CHUTES_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "deepseek-ai/DeepSeek-V3.2-TEE",
    "messages": [{"role": "user", "content": "Say hello in one sentence."}]
  }'
```

### Python (OpenAI SDK)
```python
from openai import OpenAI

client = OpenAI(
    base_url="https://llm.chutes.ai/v1",
    api_key="cpk_...",  # or os.environ["CHUTES_API_KEY"]
)

resp = client.chat.completions.create(
    model="deepseek-ai/DeepSeek-V3.2-TEE",
    messages=[{"role": "user", "content": "Say hello in one sentence."}],
)
print(resp.choices[0].message.content)
```

### JavaScript / TypeScript (OpenAI SDK)
```ts
import OpenAI from "openai";

const client = new OpenAI({
  baseURL: "https://llm.chutes.ai/v1",
  apiKey: process.env.CHUTES_API_KEY,
});

const resp = await client.chat.completions.create({
  model: "deepseek-ai/DeepSeek-V3.2-TEE",
  messages: [{ role: "user", content: "Say hello in one sentence." }],
});
console.log(resp.choices[0].message.content);
```

### Vercel AI SDK
```bash
npm install @chutes-ai/ai-sdk-provider
```
```ts
import { createChutes } from "@chutes-ai/ai-sdk-provider";
import { generateText } from "ai";

const chutes = createChutes({ apiKey: process.env.CHUTES_API_KEY });

const { text } = await generateText({
  model: chutes("deepseek-ai/DeepSeek-V3.2-TEE"),
  prompt: "Say hello in one sentence.",
});
```

### LiteLLM
```python
import litellm

resp = litellm.completion(
    model="chutes_ai/deepseek-ai/DeepSeek-V3.2-TEE",
    messages=[{"role": "user", "content": "Say hello in one sentence."}],
    api_key="cpk_...",
)
```

> Connecting **Hermes** or **OpenClaw**? Jump to their drop-in configs: [Hermes](../other-agents/hermes/README.md) · [OpenClaw](../other-agents/openclaw/README.md).

---

## 5. Discover models (and never hardcode)

Model IDs change as the catalog evolves. **Always ask the live endpoint** instead of pinning an ID that may vanish:

```bash
curl https://llm.chutes.ai/v1/models   # public, no auth
```

Each model object carries everything you need to choose well:

| Field | What it tells you |
|---|---|
| `id` | The string to pass as `model` (e.g. `Qwen/Qwen3.5-397B-A17B-TEE`) |
| `context_length` / `max_output_length` | Input window / max generation |
| `pricing.prompt` / `pricing.completion` | USD per **1M** tokens (in / out) |
| `pricing.input_cache_read` | Discounted rate on prompt-cache hits |
| `confidential_compute` | `true` ⇒ runs in a TEE (use this, not the `-TEE` suffix) |
| `supported_features` | e.g. `["tools","json_mode","structured_outputs","reasoning"]` |
| `supported_sampling_parameters` | Which sampling knobs the engine accepts |
| `input_modalities` | `["text"]`, `["text","image"]`, `["text","image","video"]` |
| `owned_by` | Inference engine: `sglang` or `vllm` |

A convenience snapshot lives at [`docs/known-models.md`](known-models.md) and [`data/chutes-models.json`](../data/chutes-models.json), **auto-refreshed daily** by GitHub Actions. The live `/v1/models` call is always the source of truth.

> 💡 **Latency/throughput is not in `/v1/models`.** For live TTFT/TPS, query `GET https://api.chutes.ai/invocations/stats/llm`, or just let routing pick for you (next section).

---

## 6. Smart routing: one request, many models

Don't bet your uptime on a single model. Chutes lets you pass a **pool** and a **strategy** right in the `model` field.

### Inline routing (zero setup)
Comma-separate model IDs; append a strategy suffix:

```python
# Sequential failover — try each in order until one answers
model="zai-org/GLM-5-TEE,deepseek-ai/DeepSeek-V3.2-TEE,Qwen/Qwen3.5-397B-A17B-TEE"

# Lowest latency right now (best for interactive chat)
model="zai-org/GLM-5-TEE,deepseek-ai/DeepSeek-V3.2-TEE:latency"

# Highest throughput right now (best for long generations / batch)
model="zai-org/GLM-5-TEE,deepseek-ai/DeepSeek-V3.2-TEE:throughput"
```

### Saved pool + aliases (set once in the dashboard)
Configure a pool at [chutes.ai/app](https://chutes.ai/app) → Model Routing, then use:

| Alias | Strategy |
|---|---|
| `default` | Sequential failover |
| `default:latency` | Fastest first token |
| `default:throughput` | Most tokens/sec |

A single concrete model ID bypasses routing entirely. Manage pools via `GET/POST https://api.chutes.ai/model_aliases/`. Deep recipes (build pools from live data, TEE-only pools, alias governance) live in the [`chutes-routing` skill](../plugins/chutes-ai/skills/chutes-routing/SKILL.md).

---

## 7. Streaming, tools, JSON mode, vision

All standard OpenAI features — gated by each model's `supported_features`, so check the model list first.

**Streaming** — set `stream: true`, read SSE chunks:
```python
stream = client.chat.completions.create(
    model="deepseek-ai/DeepSeek-V3.2-TEE",
    messages=[{"role": "user", "content": "Stream me a haiku."}],
    stream=True,
)
for chunk in stream:
    print(chunk.choices[0].delta.content or "", end="")
```

**Tool / function calling** — pass `tools=[...]`; works on any model whose `supported_features` includes `"tools"`.

**JSON mode & structured outputs** — `response_format={"type": "json_object"}` on models advertising `"json_mode"`; full JSON-schema enforcement on models advertising `"structured_outputs"`.

**Vision** — send image parts in `content` to models whose `input_modalities` include `"image"` (e.g. `google/gemma-4-31B-turbo-TEE`, `Qwen/Qwen3.6-27B-TEE`, the Kimi-K2 line). Kimi also accepts `"video"`.

> Before sending exotic sampling params (`top_k`, `repetition_penalty`, …), check the model's `supported_sampling_parameters`. `sglang` and `vllm` engines accept different knobs.

---

## 8. Privacy: every model is a TEE

As of the latest snapshot, **100% of hosted models run with `confidential_compute: true`** — inside Intel TDX hardware enclaves. Prompts and responses are hardware-isolated; even Chutes operators can't read them.

- **Filter on the boolean, not the suffix.** Trust `confidential_compute: true`, not the `-TEE` in the name.
- **Want proof, not promises?** Each chute exposes attestation evidence at `GET https://api.chutes.ai/chutes/{chute_id}/evidence` (requires a 64-hex-char `nonce`), plus golden measurements at `GET https://api.chutes.ai/servers/tee/measurements`. The [`chutes-tee` skill](../plugins/chutes-ai/skills/chutes-tee/SKILL.md) fetches and parses real TDX/GPU quotes. Don't claim *cryptographic* attestation unless Intel DCAP verification actually ran and passed.

---

## 9. Money: pricing, balance, the 25% research discount

**Pricing** is per-model, USD per 1M tokens, in the `pricing` object of each model. Prompt-cache hits are billed at the cheaper `input_cache_read` rate automatically. Public GPU/TAO pricing: `GET https://api.chutes.ai/pricing`.

**Balance & account:** `GET https://api.chutes.ai/users/me` → `balance` (USD), `payment_address` (Bittensor SS58 for crypto top-ups), quotas, and more.

**Top up:**
- **Crypto** — send `$TAO`, SN64, or any Bittensor alpha token to your `payment_address`; auto-converts to USD within minutes (non-refundable).
- **Stripe** — [chutes.ai/app](https://chutes.ai/app) → billing → "Add Balance" → "Top up with Stripe" (25+ payment methods).

**25% research discount:** swap the inference base URL for `https://research-data-opt-in-proxy.chutes.ai/v1` — same API, same models, same key, **25% cheaper**. The trade: prompts/responses are recorded for joint caching research with Harvard. **Never send sensitive data here.** Confirm it's active via `GET https://api.chutes.ai/users/me/discounts`.

---

## 10. Errors & gotchas

| Symptom | Likely cause | Fix |
|---|---|---|
| `429` on a completion you authenticated | You sent `X-API-Key`, which is ignored → anonymous rate limit | Use `Authorization: Bearer cpk_...` |
| `401` on `api.chutes.ai` | Missing/invalid Bearer, or `X-API-Key` | Send a valid `Bearer cpk_...` |
| `200` on `/v1/models` but completions fail | `/v1/models` is public — it never validated your key | Test against `GET /users/me` |
| `model not found` | Stale hardcoded ID | Re-query `GET /v1/models`; IDs change |
| Param rejected | Engine doesn't support that sampling knob | Check `supported_sampling_parameters` |
| Tool call ignored | Model lacks `"tools"` | Pick a model whose `supported_features` includes it |

Errors return JSON shaped like `{ "detail": "..." }`. List endpoints paginate: `{ "total", "page", "limit", "items": [...] }` (0-indexed pages, default limit 25). POST/PATCH need `Content-Type: application/json`.

---

## 11. Endpoint cheat sheet

| What | Method | URL |
|---|---|---|
| Register | POST | `https://api.chutes.ai/users/register` |
| My account / balance | GET | `https://api.chutes.ai/users/me` |
| Create API key | POST | `https://api.chutes.ai/api_keys/` |
| List / delete API keys | GET / DELETE | `https://api.chutes.ai/api_keys/{id}` |
| **List models** | GET | `https://llm.chutes.ai/v1/models` *(public)* |
| **Chat completions** | POST | `https://llm.chutes.ai/v1/chat/completions` |
| Live latency/throughput | GET | `https://api.chutes.ai/invocations/stats/llm` |
| Model aliases (routing) | GET / POST | `https://api.chutes.ai/model_aliases/` |
| Quotas | GET | `https://api.chutes.ai/users/me/quotas` |
| Discounts | GET | `https://api.chutes.ai/users/me/discounts` |
| Pricing (public) | GET | `https://api.chutes.ai/pricing` |
| TEE evidence | GET | `https://api.chutes.ai/chutes/{chute_id}/evidence?nonce=<64-hex>` |
| TEE golden measurements | GET | `https://api.chutes.ai/servers/tee/measurements` |
| Swagger UI | — | `https://api.chutes.ai/docs` |

---

## 12. Machine-readable interfaces

Point tool-based frameworks (AutoGPT, LangChain loaders, ChatGPT-plugin format) straight at these:

- **OpenAPI spec:** `https://api.chutes.ai/openapi.json`
- **Plugin manifest:** `https://chutes.ai/.well-known/ai-plugin.json`
- **Agent-facing docs:** `https://chutes.ai/llms.txt` (also `llms-full.txt`, `docs.json`)
- **Live model list:** `https://llm.chutes.ai/v1/models`

---

### Where to go next

- **Use it in Claude** → install the plugin from this repo's [README](../README.md#install-for-claude-code--cowork)
- **Use it in Hermes** → [`other-agents/hermes/README.md`](../other-agents/hermes/README.md)
- **Use it in OpenClaw** → [`other-agents/openclaw/README.md`](../other-agents/openclaw/README.md)
- **Any other OpenAI-compatible client** → [`other-agents/openai-compatible/README.md`](../other-agents/openai-compatible/README.md)
- **Drop into any agent's system prompt** → [`other-agents/system-prompt/chutes-agent-prompt.md`](../other-agents/system-prompt/chutes-agent-prompt.md)

*Models and the catalog change. When live inventory, pricing, capabilities, or TEE status matter, `GET https://llm.chutes.ai/v1/models` is the source of truth.*
