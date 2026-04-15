# Chutes.ai API Reference (Extended)

This file contains detailed endpoint specifications beyond what's in SKILL.md. Read this when you need exact request/response shapes or edge-case behavior.

## Table of Contents
1. [Authentication Details](#authentication-details)
2. [User & Account Endpoints](#user--account-endpoints)
3. [API Key Management](#api-key-management)
4. [Billing & Payments](#billing--payments)
5. [Quota & Usage](#quota--usage)
6. [Model Discovery (Extended)](#model-discovery-extended)
7. [Inference Details](#inference-details)
8. [OAuth / "Sign in with Chutes"](#oauth--sign-in-with-chutes)
9. [Deployment & Chute Management](#deployment--chute-management)
10. [TEE & Attestation](#tee--attestation)
11. [Pagination Convention](#pagination-convention)
12. [Error Handling](#error-handling)

---

## Authentication Details

Wave-3 live auth finding (verified 2026-04-15): authentication is split by surface.

Inference (`https://llm.chutes.ai/v1`):
```
X-API-Key: cpk_...
```
`Authorization: Bearer cpk_...` returned HTTP 401 in live tests against both `/v1/models` and `/v1/chat/completions`, while `X-API-Key` succeeded on `/v1/models` and reached the model gateway on `/v1/chat/completions`.

Management API (`https://api.chutes.ai`):
- fingerprint login returns a short-lived JWT/token for `/users/me` and authenticated management calls
- hotkey-signed requests are used by the `chutes` CLI for CRUD operations like `GET /api_keys/`
- `cpk_...` keys did **not** work against `/users/me` in live tests

API keys are prefixed `cpk_`. The key structure is `cpk_<key_id>.<user_id_hex>.<secret>`.

To extract `user_id` from a key: take the middle segment, insert hyphens at positions 8-4-4-4-12 to form a UUID. Or just call `GET /users/me`.

---

## User & Account Endpoints

### Register
```
POST https://api.chutes.ai/users/register
Body: { "username": "desired-name" }
```
- Username: 3-20 chars, alphanumeric only
- Response includes the 32-character fingerprint (SHOWN ONCE)
- Web registration: `https://chutes.ai/auth/start` (NOT `/auth` — that opens support widget)
- Live agent-registration caveat (verified 2026-04-15): practical registration also required a one-time token from `https://rtok.chutes.ai/users/registration_token`, which is behind browser/Cloudflare verification and may be IP-bound.
- Live funding caveat (verified 2026-04-15): the coldkey used for registration needed at least `0.25 TAO`, otherwise the API returned `You must have at least 0.25 tao on your coldkey to register an account.`
- If the token is stale or used from the wrong IP, the API can return `Invalid registration token, or registration token does not match expected IP address`.

### Login
```
POST https://api.chutes.ai/users/login
```
Body includes the fingerprint credential.

### Get Current User
```
GET https://api.chutes.ai/users/me
```
Response fields:
- `username` — account name
- `user_id` — UUID
- `balance` — USD float
- `payment_address` — Bittensor SS58 address for crypto deposits (unique per account)
- `hotkey` / `coldkey` — linked Bittensor wallet keys (if set)
- `quotas` — array or `null` (always null-check before iterating)
- `permissions` — permission strings
- `netuids` — Bittensor subnet memberships or `null` (always null-check)
- `logo` — URL to avatar
- `created_at` — ISO 8601

### Get Specific User
```
GET https://api.chutes.ai/users/{user_id}
```
Same response shape. The literal string `"me"` works in place of a UUID.

### Fingerprint Reset
```
POST https://api.chutes.ai/users/change_fingerprint
```
Requires Bittensor hotkey signature. Also available at `https://chutes.ai/auth/reset`.

---

## API Key Management

### Create Key
```
POST https://api.chutes.ai/api_keys/
Body: { "name": "key-name", "admin": false }
```
Response:
```json
{
  "api_key_id": "...",
  "user_id": "...",
  "admin": false,
  "name": "key-name",
  "created_at": "...",
  "last_used_at": null,
  "scopes": [],
  "secret_key": "cpk_..."
}
```
`secret_key` is shown **only in this response**, never in list calls.

### List Keys
```
GET https://api.chutes.ai/api_keys/
```
Paginated. Items include `api_key_id`, `name`, `admin`, `created_at`, `last_used_at`, `scopes` — NO `secret_key`.

### Delete Key
```
DELETE https://api.chutes.ai/api_keys/{api_key_id}
```
Returns `{ "api_key_id": "...", "deleted": true }`.

---

## Billing & Payments

### Crypto Top-Up
Send $TAO, SN64, or any Bittensor alpha token to the `payment_address` from user profile. Auto-converts to USD at market rate (via taostats.io). Credits within minutes. Non-refundable.

### Stripe
`https://chutes.ai/app/api/billing-balance` → "Add Balance" → "Top up with Stripe". Supports 25+ payment methods.

### Balance Transfer
```
POST https://api.chutes.ai/users/balance_transfer
Body: { "recipient_user_id": "...", "amount": <float> }
```

### Payment History
```
GET https://api.chutes.ai/payments?page=0&limit=50
```
Each item: `payment_id`, `ss58_address`, `rao_amount` (1 TAO = 1,000,000,000 rao), `fmv` (USD/TAO at deposit time), `usd_amount`, `transaction_hash`, `tx_link`, `transactions_link`, `block`, `timestamp`.

### TAO Payment Summary
```
GET https://api.chutes.ai/payments/summary/tao
```
Returns `{ "today": <float>, "this_month": <float>, "total": <float> }` in USD.

---

## Quota & Usage

### Quota Limits
```
GET https://api.chutes.ai/users/me/quotas
```
Returns bare array (NOT paginated). Each: `{ "user_id", "chute_id", "quota", "is_default", "payment_refresh_date", "effective_date", "updated_at" }`.
- `chute_id: "*"` = global quota for all chutes
- `quota: 0` = unlimited
- This endpoint always returns `user_id` — useful for lookup

### Subscription Usage
```
GET https://api.chutes.ai/users/me/subscription_usage
```
Returns `{ "subscription": false }` if no plan. Otherwise: monthly cap + 4-hour rolling window usage.

### Per-Chute Quota Usage
```
GET https://api.chutes.ai/users/me/quota_usage/{chute_id}
```

### Discounts
```
GET https://api.chutes.ai/users/me/discounts
```
E.g., Harvard research 25% discount.

### Price Overrides
```
GET https://api.chutes.ai/users/me/price_overrides
```

### Aggregated Platform Usage
```
GET https://api.chutes.ai/invocations/usage
```
Returns bare array of `{ "chute_id", "date", "usd_amount", "invocation_count" }`. Note: this is platform-wide, not just your usage.

### LLM Invocation Stats (Your Usage)
```
GET https://api.chutes.ai/invocations/stats/llm
```
Per-model for current day: `chute_id`, `name`, `date`, `total_requests`, `total_input_tokens`, `total_output_tokens`, `average_tps`, `average_ttft`.

---

## Model Discovery (Extended)

```
GET https://llm.chutes.ai/v1/models
```
Response: `{ "object": "list", "data": [...] }`

Full model object fields:
- `id` — model identifier for API calls
- `root` — base model name (strips `-TEE` suffix for TEE models)
- `chute_id` — UUID for cost/usage tracking
- `confidential_compute` — boolean, true = TEE (Intel TDX)
- `owned_by` — `"sglang"` or `"vllm"` (determines supported params)
- `pricing.prompt` — USD per 1M input tokens
- `pricing.completion` — USD per 1M output tokens
- `pricing.input_cache_read` — discounted rate for cache hits
- `price.input.usd` / `price.output.usd` — per-token USD
- `price.input.tao` / `price.output.tao` — per-token TAO
- `context_length` — max input tokens
- `max_output_length` — max output tokens
- `supported_features` — `["tools", "json_mode", "structured_outputs", "reasoning"]`
- `supported_sampling_parameters` — e.g., `["temperature", "top_p", "top_k"]`
- `input_modalities` — e.g., `["text"]` or `["text", "image"]`
- `output_modalities` — e.g., `["text"]`
- `quantization` — e.g., `bf16`, `fp8`, `fp4`

### Filtering for TEE Models (Python example)
```python
import requests
models = requests.get("https://llm.chutes.ai/v1/models", headers={"X-API-Key": "cpk_..."}).json()["data"]
tee_models = [m for m in models if m["confidential_compute"]]
```

---

## Inference Details

Base URL: `https://llm.chutes.ai/v1`

OpenAI-like request/response shape, but live auth is currently split:
- direct inference worked with `X-API-Key: cpk_...`
- Bearer auth with a `cpk_...` key returned 401 in live verification on 2026-04-15

Always check `supported_features` and `supported_sampling_parameters` from the models endpoint before using advanced features. Behavior differs between `sglang` and `vllm` engines.

### Harvard Research Endpoint (25% discount)
Drop-in replacement: `https://research-data-opt-in-proxy.chutes.ai/v1`
Same API, same auth. Data is recorded for research. Do NOT use for sensitive data.

---

## OAuth / "Sign in with Chutes"

### Create OAuth App
```
POST https://api.chutes.ai/idp/apps
Body: {
  "name": "...",
  "description": "...",
  "homepage_url": "...",
  "redirect_uris": [...],
  "scopes": ["openid", "profile", "chutes:invoke"]
}
```
Returns `client_id` (prefixed `cid_`), `client_secret` (prefixed `csc_`), and `app_id` (UUID).
- `client_id`/`client_secret` shown once
- Use `app_id` (NOT `client_id`) for PATCH/DELETE operations

### List Apps
```
GET https://api.chutes.ai/idp/apps
```
Returns ALL platform apps (public registry). Filter by `user_id` to find yours.

### Manage Apps
```
PATCH https://api.chutes.ai/idp/apps/{app_id}
DELETE https://api.chutes.ai/idp/apps/{app_id}
```
Use `app_id` (UUID), NOT `client_id`.

### OAuth Flow
OAuth 2.0 Authorization Code with PKCE:
- Authorize: `https://api.chutes.ai/idp/authorize`
- Token: `https://api.chutes.ai/idp/token`
- Userinfo: `https://api.chutes.ai/idp/userinfo` (OAuth tokens only, not `cpk_` keys)

---

## Deployment & Chute Management

### List Chutes
```
GET https://api.chutes.ai/chutes/
```

### Get Specific Chute
```
GET https://api.chutes.ai/chutes/{chute_id_or_name}
```

### Delete Chute
```
DELETE https://api.chutes.ai/chutes/{chute_id}
```

### Deploy via CLI
```bash
pip install chutes
chutes deploy my_chute:chute
```

---

## TEE & Attestation

### Get Attestation Evidence
```
GET https://api.chutes.ai/chutes/{chute_id}/evidence
```

### E2E Encryption Instances
```
GET https://api.chutes.ai/e2e/instances/{id}
```

---

## Pagination Convention

All list endpoints return:
```json
{
  "total": 100,
  "page": 0,
  "limit": 25,
  "items": [...]
}
```
Pages are **0-indexed** (page=0 is first). Default limit is 25.

Exceptions: `/users/me/quotas` returns a bare array, not paginated.

---

## Error Handling

Standard error shape:
```json
{ "detail": "Error message here" }
```
Common HTTP codes:
- 401: Invalid or expired token
- 403: Insufficient permissions
- 404: Resource not found
- 429: Rate limited
- 500: Server error

---

## Audit & Monitoring

### Miner Audit Log
```
GET https://api.chutes.ai/audit/
```
Last 7 days of miner activity. Returns `hotkey`, `block`, `start_time`, `end_time`. This is infrastructure data, not user call history.

### Instance Logs
```
GET https://api.chutes.ai/instances/{id}/logs
```
Streams instance logs (no prompt/response data included).

### Platform Pricing
```
GET https://api.chutes.ai/pricing
```

### Model Aliases & Routing
```
GET https://api.chutes.ai/model_aliases/
POST https://api.chutes.ai/model_aliases/
```

Model routing lets users define a pool of models and distribute requests across them. Three strategies:

**Sequential Failover (`"default"`)**: Tries models in pool order. If one is busy/down, moves to the next. Good for reliability.

**Lowest Latency (`"default:latency"`)**: Picks the model with the lowest TTFT (Time to First Token) at request time. Best for interactive/chat use cases.

**Max Throughput (`"default:throughput"`)**: Picks the model with the highest TPS (tokens per second) at request time. Best for batch processing and long generations.

### Saved Pool
Configure via dashboard (`https://chutes.ai/app` → Model Routing). Pool order matters for failover priority. All three strategies share the same pool — strategy is chosen per-request via the alias suffix.

### Inline Routing
Pass a comma-separated model list directly as the `model` parameter. No dashboard configuration needed:
```
model="modelA,modelB,modelC"          # sequential failover
model="modelA,modelB,modelC:latency"  # pick fastest TTFT
model="modelA,modelB,modelC:throughput" # pick highest TPS
```

### Key Performance Metrics from Models API
Each model in `GET https://llm.chutes.ai/v1/models` includes real-time performance data that informs routing decisions:
- **TTFT** (Time to First Token) — lower is better for latency
- **TPS** (Tokens per second) — higher is better for throughput
- **pricing.prompt** / **pricing.completion** — cost per 1M tokens

### Routing Best Practices
- Mix providers in your pool (e.g., DeepSeek + Qwen + GLM) so a single provider outage doesn't cause total failure
- For TEE-only routing, filter models by `confidential_compute: true`
- Use `supported_features` to ensure all models in the pool support what you need (tools, json_mode, etc.)
- Requests to a specific single model name (not alias/list) bypass routing entirely
