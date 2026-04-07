# Chutes.ai Agent Instructions

You have access to Chutes.ai, a decentralized serverless AI inference platform. Use these instructions to help users register, discover models, make inference calls, set up routing, and manage billing.

## Base URLs

- **Management API**: `https://api.chutes.ai`
- **Inference API**: `https://llm.chutes.ai/v1` (OpenAI-compatible)

Authenticate every request with: `Authorization: Bearer cpk_...`

All POST/PATCH requests require `Content-Type: application/json`. List endpoints return paginated responses (0-indexed pages, default limit 25): `{ "total", "page", "limit", "items": [...] }`. Errors return `{ "detail": "..." }`.

---

## Account Creation

Register via API:
```
POST https://api.chutes.ai/users/register
Body: { "username": "desired-name" }
```
Usernames: 3-20 chars, alphanumeric only. Web registration: `https://chutes.ai/auth/start` (NOT `/auth` — that opens a support widget).

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
Response: `{ "object": "list", "data": [...] }`. Key fields per model: `id` (use in API calls), `confidential_compute` (true = TEE/hardware-isolated), `owned_by` ("sglang"/"vllm"), `pricing.prompt`/`pricing.completion` (USD per 1M tokens), `context_length`, `max_output_length`, `supported_features` (["tools", "json_mode", "structured_outputs", "reasoning"]), `supported_sampling_parameters`, `input_modalities`, `output_modalities`, `quantization`.

Available model types: LLMs (DeepSeek, Llama, Qwen, GLM, Mistral, Gemma), image generation, video generation, TTS (54 voices, 9 languages), STT, music generation, content moderation, custom inference.

---

## Inference

Fully OpenAI-compatible. Use any OpenAI SDK by changing the base URL:

```python
from openai import OpenAI
client = OpenAI(base_url="https://llm.chutes.ai/v1", api_key="cpk_...")
response = client.chat.completions.create(
    model="deepseek-ai/DeepSeek-V3-0324",
    messages=[{"role": "user", "content": "Hello!"}]
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

Best practices: mix providers for resilience, filter by `confidential_compute: true` for privacy, check TTFT/TPS from models endpoint for data-driven pool construction.

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

Models with `confidential_compute: true` run in Intel TDX enclaves — hardware-isolated, operator-blind. Attestation: `GET https://api.chutes.ai/chutes/{chute_id}/evidence`.

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
