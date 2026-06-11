# Chutes.ai Agent Instructions

You have access to Chutes.ai, a decentralized serverless AI inference platform. Use these instructions to help users register, discover models, make inference calls, set up routing, and manage billing.

## Base URLs

- **Management API**: `https://api.chutes.ai`
- **Inference API**: `https://llm.chutes.ai/v1` (OpenAI-compatible, standard Bearer auth)

Live auth finding (re-verified 2026-06-11 with read-only GETs — this INVERTS the 2026-04-15 wave-3 finding):
- `Authorization: Bearer cpk_...` returned HTTP 200 on `GET llm.chutes.ai/v1/models` AND on `GET api.chutes.ai/users/me` — one Bearer header now works on both surfaces for GETs
- Bearer is the platform-recommended header (chutes.ai's own `ai-plugin.json` says to use the `cpk_` key "as a Bearer token")
- `X-API-Key: cpk_...` returned 200 on `/v1/models` but **401 on `api.chutes.ai/users/me`**; official `llms.txt` docs say X-API-Key is silently ignored on the inference surface — do not use it
- `GET /v1/models` is public: 200 with no auth at all
- The fingerprint-login JWT (`POST /users/login`) still works for management and remains the path for write endpoints; Bearer `cpk_` on management writes and on `POST /chat/completions` was not re-tested (unverified as of 2026-06-11)

Default to `Authorization: Bearer cpk_...` everywhere.

All POST/PATCH requests require `Content-Type: application/json`. List endpoints return paginated responses (0-indexed pages, default limit 25): `{ "total", "page", "limit", "items": [...] }`. Errors return `{ "detail": "..." }`.

---

## Account Creation

Register via API:
```
POST https://api.chutes.ai/users/register
Body: { "username": "desired-name" }
```
Usernames: 3-20 chars, alphanumeric only. Web registration: `https://chutes.ai/auth/start` (NOT `/auth` — that opens a support widget).

Wave-3 live registration finding (verified 2026-04-15): practical account creation may require a human-in-the-loop step.
- A one-time registration token from `https://rtok.chutes.ai/users/registration_token`
- Browser / Cloudflare verification to obtain that token
- At least `0.25 TAO` on the registering coldkey
- A fresh token if the previous one fails with `Invalid registration token, or registration token does not match expected IP address`

**CRITICAL**: Registration returns a 32-character fingerprint shown ONLY ONCE. This is the master credential. If lost without a linked Bittensor wallet, account access is gone. Always offer to save it to a backup file. Recovery IS possible via Bittensor hotkey signature at `https://chutes.ai/auth/reset` or `POST https://api.chutes.ai/users/change_fingerprint`.

Login: `POST https://api.chutes.ai/users/login` (with fingerprint). OAuth also available (Google/GitHub) at `https://chutes.ai/auth`.

---

## API Keys

Create:
```
POST https://api.chutes.ai/api_keys/
Body: { "name": "my-key", "admin": false }
```
Response includes `secret_key` (prefixed `cpk_`) — shown ONCE, never in list calls. Set `admin: true` for elevated permissions.

List: `GET https://api.chutes.ai/api_keys/` | Delete: `DELETE https://api.chutes.ai/api_keys/{api_key_id}`

---

## Model Discovery

```
GET https://llm.chutes.ai/v1/models
```
Public endpoint (no auth required; verified 2026-06-11). Response: `{ "object": "list", "data": [...] }`. Key fields per model: `id` (use in API calls), `confidential_compute` (true = TEE/hardware-isolated), `owned_by` ("sglang"/"vllm"), `pricing.prompt`/`pricing.completion` (USD per 1M tokens, plus `input_cache_read` prompt-cache pricing, typically 50% of input), `context_length`, `max_output_length`, `supported_features` (["tools", "json_mode", "structured_outputs", "reasoning"]), `supported_sampling_parameters`, `input_modalities`, `output_modalities`, `quantization`.

As of 2026-06-11 the hosted LLM catalog is **13 models, all TEE** (`-TEE` id suffix, `confidential_compute: true`): DeepSeek-V3.2, Kimi K2.5/K2.6, GLM-5/5.1, Qwen 3/3.5/3.6, MiniMax-M2.5, Gemma 4, Nemotron 3 Ultra, Mistral Nemo. There are no Llama models and no non-TEE LLMs — always treat `/v1/models` as the source of truth rather than hardcoding ids. Beyond LLMs, the wider chute catalog (`GET https://api.chutes.ai/chutes/?include_public=true`) has image generation, video generation, TTS, STT, music generation, embeddings, content moderation, and custom inference chutes.

---

## Inference

Chutes uses OpenAI-compatible request/response shapes on the inference surface with standard Bearer auth, so generic OpenAI SDKs work by changing the base URL and key. (Bearer `cpk_` verified live on `GET /v1/models` 2026-06-11; the paid `POST /chat/completions` call itself was not re-exercised — unverified as of 2026-06-11.)

```python
import requests
response = requests.post(
    "https://llm.chutes.ai/v1/chat/completions",
    headers={"Authorization": "Bearer cpk_...", "Content-Type": "application/json"},
    json={
        "model": "deepseek-ai/DeepSeek-V3.2-TEE",
        "messages": [{"role": "user", "content": "Hello!"}],
    },
)
```

Check `supported_features` and `supported_sampling_parameters` before using advanced features — behavior differs between sglang and vllm engines.

---

## Model Routing

Route requests across a pool of models with three strategies:

| Strategy | Model Parameter | Behavior |
|----------|----------------|----------|
| Sequential Failover | `"default"` | Tries models in pool order |
| Lowest Latency | `"default:latency"` | Picks lowest TTFT right now |
| Max Throughput | `"default:throughput"` | Picks highest TPS right now |

Configure a saved pool in the dashboard (`https://chutes.ai/app` → Model Routing), or use **inline routing** — pass a comma-separated model list directly:

```python
# Inline latency routing
response = client.chat.completions.create(
    model="model-a,model-b,model-c:latency",
    messages=[{"role": "user", "content": "Hello"}]
)
```

Manage aliases via API: `GET/POST https://api.chutes.ai/model_aliases/`

Best practices: mix providers for resilience, filter by `confidential_compute: true` for privacy, check per-model TPS/TTFT from `GET https://api.chutes.ai/invocations/stats/llm` for data-driven pool construction (the `/v1/models` response does not include TTFT/TPS).

---

## Account & Balance

```
GET https://api.chutes.ai/users/me
```
Returns: `username`, `user_id`, `balance` (USD), `payment_address` (Bittensor SS58 for crypto), `hotkey`/`coldkey`, `quotas`, `permissions`.

---

## Payments

**Crypto**: Send $TAO, SN64, or Bittensor alpha tokens to `payment_address` from user profile. Auto-converts to USD. Credits within minutes. Non-refundable.

**Stripe (25+ methods)**: `https://chutes.ai/app/api/billing-balance` → "Add Balance" → "Top up with Stripe"

**Transfer**: `POST https://api.chutes.ai/users/balance_transfer` with `{ "recipient_user_id": "...", "amount": <float> }`

**History**: `GET https://api.chutes.ai/payments?page=0&limit=50`

**TAO summary**: `GET https://api.chutes.ai/payments/summary/tao` → `{ "today", "this_month", "total" }` in USD.

---

## Quotas & Usage

- Quota limits: `GET https://api.chutes.ai/users/me/quotas` (bare array, not paginated)
- Subscription: `GET https://api.chutes.ai/users/me/subscription_usage`
- LLM stats: `GET https://api.chutes.ai/invocations/stats/llm` (per-model: requests, tokens, TPS, TTFT)
- Discounts: `GET https://api.chutes.ai/users/me/discounts`

---

## TEE (Confidential Compute)

Models with `confidential_compute: true` run in Intel TDX enclaves — hardware-isolated, operator-blind. As of 2026-06-11 that is every hosted LLM. Attestation: `GET https://api.chutes.ai/chutes/{chute_id}/evidence?nonce=<nonce>` — the `nonce` query param is required and must be exactly 64 hex characters (32 bytes). Per-instance evidence: `GET /instances/{instance_id}/evidence`.

## Harvard Research Discount (25% off)

Drop-in endpoint: `https://research-data-opt-in-proxy.chutes.ai/v1`. Same API, same auth. Data recorded for research — do NOT send sensitive data here.

---

## Key Endpoints Reference

| What | Method | URL |
|------|--------|-----|
| Register | POST | `https://api.chutes.ai/users/register` |
| Login | POST | `https://api.chutes.ai/users/login` |
| My account | GET | `https://api.chutes.ai/users/me` |
| Create API key | POST | `https://api.chutes.ai/api_keys/` |
| List models | GET | `https://llm.chutes.ai/v1/models` |
| Chat completions | POST | `https://llm.chutes.ai/v1/chat/completions` |
| Payments | GET | `https://api.chutes.ai/payments` |
| Quotas | GET | `https://api.chutes.ai/users/me/quotas` |
| Usage stats | GET | `https://api.chutes.ai/invocations/stats/llm` |
| Model aliases | GET/POST | `https://api.chutes.ai/model_aliases/` |
| Swagger docs | — | `https://api.chutes.ai/docs` |
| OpenAPI spec | — | `https://api.chutes.ai/openapi.json` |

## More Info

- Docs: `https://chutes.ai/docs`
- Full API reference: `https://chutes.ai/llms-full.txt`
- Machine-readable index: `https://chutes.ai/docs.json`
- Plugin manifest: `https://chutes.ai/.well-known/ai-plugin.json`
