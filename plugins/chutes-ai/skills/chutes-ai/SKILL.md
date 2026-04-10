---
name: chutes-ai
description: "Chutes.ai integration skill for accessing decentralized open-source AI inference. Use this skill whenever the user mentions Chutes, chutes.ai, open-source model inference, decentralized AI, DeepSeek API, Llama API access, serverless GPU inference, or wants to access cheap/free open-source AI models. Also trigger when users ask about setting up alternative AI providers, getting API keys for open-source models, comparing inference costs, running models on decentralized compute, TEE/confidential AI inference, or when an agent needs to tap into additional AI capabilities beyond its own. If the user wants to register for an AI inference service, check balances, discover available models, or make OpenAI-compatible API calls to open-source models, this is the right skill."
---

# Chutes.ai — Decentralized AI Inference Skill

This skill enables Claude to help users (and other agents) register for, configure, and use Chutes.ai — a decentralized serverless compute platform for open-source AI models powered by Bittensor. It covers the full lifecycle: account creation, API key management, model discovery, making inference calls, and managing billing/payments.

Chutes provides high-performance inference for top open-source models (DeepSeek, Llama, Qwen, and many more) through an **OpenAI-compatible API**, which means any tool or library that works with OpenAI can point at Chutes instead. Models run on decentralized GPU infrastructure, and many are available for free or at very low cost.

## Why this matters

Open-source AI models are powerful but hosting them is expensive and complex. Chutes removes that barrier — users get instant API access to hundreds of models without managing any infrastructure. For agents, this means the ability to tap into specialized models (reasoning, code, vision, etc.) on demand.

---

## Session Initialization

When this skill is first invoked in a session, check for stored credentials before doing anything else:

```bash
python <skill-scripts-dir>/manage_credentials.py check
```

- If credentials exist for a profile → retrieve the API key silently for use in API calls:
  ```bash
  python <skill-scripts-dir>/manage_credentials.py get --field api_key
  ```
- If no credentials exist → proceed with account creation (Step 1) and save credentials immediately after.
- **NEVER paste raw credential values into conversation text.** Use them only in API call headers.

Replace `<skill-scripts-dir>` with the actual path to the `scripts/` directory where `manage_credentials.py` is installed.

---

## Quick Orientation

There are two base URLs to remember:

| Purpose | Base URL |
|---------|----------|
| **Account management** (keys, billing, users) | `https://api.chutes.ai` |
| **Inference** (chat completions, models list) | `https://llm.chutes.ai/v1` |

Every request needs an API key passed as a Bearer token:
```
Authorization: Bearer cpk_...
```

API keys are prefixed `cpk_`. All POST/PATCH requests need `Content-Type: application/json`. List endpoints return paginated results (0-indexed pages, default limit 25) in the shape `{ "total", "page", "limit", "items": [...] }`. Errors come back as `{ "detail": "..." }`.

---

## Step 1: Account Creation

Chutes uses a **32-character alphanumeric fingerprint** as the primary credential. This is important to communicate clearly to users because the fingerprint is shown **only once** during creation and cannot be recovered without a linked Bittensor wallet.

### How to register

**Via API (recommended for agents):**
```
POST https://api.chutes.ai/users/register
Body: { "username": "desired-username" }
```
Usernames must be 3-20 characters, alphanumeric only.

**Via web browser:**
Direct users to `https://chutes.ai/auth/start` — this is the registration page. Important: the "Create Account" button on `https://chutes.ai/auth` opens a support widget, NOT the registration form. Always use `/auth/start`.

**Via OAuth:**
Users can sign in with Google or GitHub at `https://chutes.ai/auth`, then create or link an account.

### After registration — the fingerprint

The response will include the 32-character fingerprint. Immediately:

1. **Show the fingerprint to the user clearly** and explain it's their master credential
2. **Offer to create a backup file** — save the fingerprint, username, and user_id to a local file (e.g., `chutes-credentials-backup.txt`) so they don't lose it
3. **Explain recovery options**: if the fingerprint is lost, it CAN be reset via a Bittensor hotkey signature at `https://chutes.ai/auth/reset` or via `POST https://api.chutes.ai/users/change_fingerprint`. So there is hope if they lose it, but only if they've linked a Bittensor wallet.

### Logging in

```
POST https://api.chutes.ai/users/login
```
Body includes the fingerprint. This returns a session/token for further operations.

---

## Step 2: API Key Creation

Once the account exists, create an API key for programmatic access:

```
POST https://api.chutes.ai/api_keys/
Body: { "name": "my-agent-key", "admin": false }
```

The response includes a `secret_key` field (prefixed `cpk_`) — this is the API key. It is **shown only once** in this response, never again in list calls. Save it immediately.

Set `"admin": true` for elevated permissions (manage other keys, etc.). For most inference use cases, `admin: false` is fine.

**List existing keys:**
```
GET https://api.chutes.ai/api_keys/
```
Returns paginated list, but `secret_key` is NOT included — only metadata like name, created_at, last_used_at.

**Delete a key:**
```
DELETE https://api.chutes.ai/api_keys/{api_key_id}
```

### Extracting user_id from an API key

The `user_id` is embedded in the key itself. For a key formatted as `cpk_<key_id>.<user_id_hex>.<secret>`, insert hyphens into the middle segment at positions 8-4-4-4-12 to get the UUID. Alternatively, just call `GET https://api.chutes.ai/users/me` — it returns everything including user_id.

---

## Step 2b: Credential Store

After creating an account and API key, **immediately save credentials** to the secure credential store. This stores secrets in the OS keychain (macOS Keychain or Linux Secret Service) — not in plaintext files. Credentials persist across sessions and projects.

### Save credentials after registration

```bash
python <skill-scripts-dir>/manage_credentials.py set-profile \
  --username <username> \
  --user-id <user_id> \
  --fingerprint <fingerprint> \
  --api-key <api_key>
```

This stores secret fields (api_key, fingerprint) in the OS keychain and non-secret metadata (username, user_id) in `~/.chutes/config` with `chmod 600`.

### Read credentials in a new session

```bash
# Get a specific field (raw value, safe for shell substitution)
python <skill-scripts-dir>/manage_credentials.py get --field api_key

# Get all fields as JSON
python <skill-scripts-dir>/manage_credentials.py get
```

### Multiple profiles

Use `--profile` to manage separate credential sets (e.g., personal vs. production):

```bash
# Save to a named profile
python <skill-scripts-dir>/manage_credentials.py set-profile --profile production --api-key cpk_prod...

# Read from a named profile
python <skill-scripts-dir>/manage_credentials.py get --profile production --field api_key

# List all profiles
python <skill-scripts-dir>/manage_credentials.py list-profiles
```

### Save OAuth app credentials

When creating OAuth apps ("Sign in with Chutes"), store the client credentials:

```bash
python <skill-scripts-dir>/manage_credentials.py set-profile \
  --profile oauth.my-app \
  --client-id <cid_...> \
  --client-secret <csc_...>
```

### Environment variable overrides (for CI/CD)

Environment variables always take precedence over stored credentials:
- `CHUTES_API_KEY` → api_key
- `CHUTES_FINGERPRINT` → fingerprint
- `CHUTES_CLIENT_ID` → client_id
- `CHUTES_CLIENT_SECRET` → client_secret
- `CHUTES_PROFILE` → profile name

### Check credential status

```bash
python <skill-scripts-dir>/manage_credentials.py check
```

Returns a JSON status object showing which backend is active, which profiles exist, and whether file permissions are secure — without revealing any secrets.

### Security model

- **Secrets** (api_key, fingerprint, client_secret, client_id) are stored in the OS keychain, not in files
- **macOS**: Uses Keychain Access — secrets are encrypted at rest and require explicit app authorization
- **Linux**: Uses freedesktop Secret Service (GNOME Keyring / KDE Wallet) if available, otherwise falls back to AES-256-GCM encrypted file
- **Non-secret metadata** (username, user_id) stored in `~/.chutes/config` with `chmod 600`
- **Process safety**: Secrets are piped via stdin, never passed as CLI arguments (prevents `ps aux` exposure)
- `~/.chutes/` directory has a `.gitignore` containing `*` as an extra guard against accidental commits

---

## Step 3: Model Discovery

Before making inference calls, discover what's available:

```
GET https://llm.chutes.ai/v1/models
Authorization: Bearer cpk_...
```

Response: `{ "object": "list", "data": [...] }`. Each model includes:

- **`id`** — the model name to use in API calls (e.g., `deepseek-ai/DeepSeek-V3-0324-TEE`)
- **`root`** — base model name (for TEE models, this strips the `-TEE` suffix)
- **`chute_id`** — UUID for cost tracking
- **`confidential_compute`** — `true` if the model runs in a TEE (Intel TDX hardware isolation). Use this boolean, not the `-TEE` suffix, as the source of truth.
- **`owned_by`** — inference engine: `"sglang"` or `"vllm"` (affects which sampling params are supported)
- **`pricing.prompt`** / **`pricing.completion`** — USD per 1 million tokens
- **`pricing.input_cache_read`** — discounted rate for cache hits
- **`context_length`** — max input context window in tokens
- **`max_output_length`** — max generation length
- **`supported_features`** — array like `["tools", "json_mode", "structured_outputs", "reasoning"]`
- **`supported_sampling_parameters`** — what params the model accepts (e.g., `temperature`, `top_p`, `top_k`)
- **`input_modalities`** / **`output_modalities`** — e.g., `["text"]` or `["text", "image"]`
- **`quantization`** — e.g., `bf16`, `fp8`, `fp4`

### Model categories available on Chutes

Chutes hosts far more than just LLMs:
- **Language models** — chat, completion, reasoning (DeepSeek, Llama, Qwen, etc.)
- **Image generation** — diffusion models
- **Video generation** — text-to-video, image-to-video
- **Text-to-Speech** — 54 voices across 9 languages (EN-US, EN-GB, ES, FR, HI, IT, JA, PT-BR, ZH)
- **Speech-to-Text** — transcription
- **Music generation**
- **Content moderation**
- **Custom inference** — deploy your own models

### Picking the right model

For a quick reference of known models with performance data and use-case recommendations, see `references/known-models.md`. Always query the live API for the most current data, but that file gives you a solid starting point.

When helping users choose, consider:
- **Task**: reasoning tasks → DeepSeek-R1; general chat → DeepSeek-V3 or Llama; code → specialized coding models
- **Privacy**: if the user needs hardware-level isolation, filter for `confidential_compute: true` (TEE models)
- **Cost**: check `pricing.prompt` and `pricing.completion`; cache hits get discounted via `pricing.input_cache_read`
- **Features**: check `supported_features` — not all models support tool calling or structured output
- **Context**: match `context_length` to the user's needs

---

## Step 4: Making Inference Calls

Chutes is **fully OpenAI-compatible**. Point any OpenAI SDK or client at `https://llm.chutes.ai/v1`:

### Python (OpenAI SDK)
```python
from openai import OpenAI

client = OpenAI(
    base_url="https://llm.chutes.ai/v1",
    api_key="cpk_..."
)

response = client.chat.completions.create(
    model="deepseek-ai/DeepSeek-V3-0324",
    messages=[{"role": "user", "content": "Hello!"}]
)
print(response.choices[0].message.content)
```

### cURL
```bash
curl https://llm.chutes.ai/v1/chat/completions \
  -H "Authorization: Bearer cpk_..." \
  -H "Content-Type: application/json" \
  -d '{
    "model": "deepseek-ai/DeepSeek-V3-0324",
    "messages": [{"role": "user", "content": "Hello!"}]
  }'
```

### JavaScript / Node
```javascript
import OpenAI from 'openai';

const client = new OpenAI({
    baseURL: 'https://llm.chutes.ai/v1',
    apiKey: 'cpk_...'
});

const response = await client.chat.completions.create({
    model: 'deepseek-ai/DeepSeek-V3-0324',
    messages: [{ role: 'user', content: 'Hello!' }]
});
```

### Vercel AI SDK
Chutes also provides an official Vercel AI SDK provider:
```bash
npm install @chutes-ai/ai-sdk-provider
```

Check `supported_sampling_parameters` from the models endpoint before passing non-standard parameters — different engines (sglang vs vllm) support different options.

---

## Step 4b: Model Routing (Smart Multi-Model Requests)

Instead of hardcoding a single model, Chutes lets you define a **pool of models** and choose a routing strategy per request. This is powerful for reliability (failover), speed (lowest latency), or throughput (highest tokens/sec). There are two ways to use routing:

### Option 1: Saved Pool with the `default` Alias

Configure a model pool in the Chutes dashboard at `https://chutes.ai/app` under Model Routing. Once saved, use one of three aliases as the `model` parameter:

| Alias | Strategy | Behavior |
|-------|----------|----------|
| `"default"` | Sequential Failover | Tries models in pool order; if one is busy or fails, moves to the next |
| `"default:latency"` | Fastest Response | Picks the model with the lowest TTFT (Time to First Token) right now |
| `"default:throughput"` | Max Throughput | Picks the model with the highest TPS (tokens per second) right now |

All three strategies use the same saved pool — you just swap the alias per-request based on what matters for that call.

```python
# Fastest response time
response = client.chat.completions.create(
    model="default:latency",
    messages=[{"role": "user", "content": "Quick question..."}]
)

# Maximum generation speed
response = client.chat.completions.create(
    model="default:throughput",
    messages=[{"role": "user", "content": "Write a long essay..."}]
)

# Reliable failover (tries models in order)
response = client.chat.completions.create(
    model="default",
    messages=[{"role": "user", "content": "Important request..."}]
)
```

### Option 2: Inline Routing String

Skip the saved pool entirely — pass a comma-separated list of model names directly as the `model` parameter. Append `:latency` or `:throughput` to choose a strategy (default is sequential failover):

```python
# Inline failover — tries GLM-5-Turbo first, then GLM-4.7-TEE, etc.
response = client.chat.completions.create(
    model="zai-org/GLM-5-Turbo,zai-org/GLM-4.7-TEE,Qwen/Qwen3-32B-TEE",
    messages=[{"role": "user", "content": "Hello"}]
)

# Inline latency routing — picks the fastest of these three right now
response = client.chat.completions.create(
    model="zai-org/GLM-5-Turbo,zai-org/GLM-4.7-TEE,Qwen/Qwen3-32B-TEE:latency",
    messages=[{"role": "user", "content": "Hello"}]
)
```

Requests using a specific single model name (not an alias or comma-separated list) bypass routing entirely.

### Model Routing via API

**List model aliases:**
```
GET https://api.chutes.ai/model_aliases/
```

**Create a model alias:**
```
POST https://api.chutes.ai/model_aliases/
```

### Recommending Routing Configurations

When helping users set up routing, query `GET https://llm.chutes.ai/v1/models` to get real-time performance data. Each model includes TTFT and TPS metrics. Use these to make informed recommendations:

- **For latency-sensitive apps** (chatbots, interactive UIs): prioritize models with low TTFT. Smaller models tend to respond faster. Look for TTFT under 2000ms.
- **For batch/bulk workloads** (summarization, data processing): prioritize models with high TPS. Some models exceed 100+ tokens/sec.
- **For reliability**: include 3-4 models in the pool as failover options. Mix providers (e.g., a DeepSeek model + a Qwen model + a GLM model) so a single provider outage doesn't take you down.
- **For privacy**: filter for TEE models (`confidential_compute: true`) and build your pool exclusively from those.

Here's an example of how to programmatically build a latency-optimized pool:
```python
import requests

models = requests.get(
    "https://llm.chutes.ai/v1/models",
    headers={"Authorization": "Bearer cpk_..."}
).json()["data"]

# Filter for TEE models with tool support, sorted by lowest TTFT
tee_with_tools = [
    m for m in models
    if m.get("confidential_compute")
    and "tools" in m.get("supported_features", [])
]
# Sort by pricing (cheapest first) as a tiebreaker
tee_with_tools.sort(key=lambda m: m["pricing"]["prompt"])

# Build inline routing string from top 4
pool = ",".join(m["id"] for m in tee_with_tools[:4])
print(f"Latency routing: {pool}:latency")
print(f"Throughput routing: {pool}:throughput")
```

---

## Step 5: Account Info & Balance

### Check account details
```
GET https://api.chutes.ai/users/me
Authorization: Bearer cpk_...
```
Returns: `username`, `user_id`, `balance` (USD), `payment_address` (Bittensor SS58 address for crypto top-ups), `hotkey`/`coldkey`, `quotas`, `permissions`, and more.

### Check balance
The `balance` field in the user info response is your current USD balance.

---

## Step 6: Payments & Billing

Chutes supports multiple payment methods:

### Crypto (Bittensor network)
Send **$TAO**, **SN64**, or any **Bittensor alpha token** to the `payment_address` from your user profile (it's a unique SS58 address per account). Tokens auto-convert to USD at current market rates (via taostats.io) and credit within minutes. Deposits are non-refundable.

### Stripe (25+ methods)
For credit cards, debit cards, and many other payment methods, direct users to:
`https://chutes.ai/app/api/billing-balance` → click "Add Balance" → "Top up with Stripe"

### Transfer between users
```
POST https://api.chutes.ai/users/balance_transfer
Body: { "recipient_user_id": "...", "amount": <float> }
```

### Payment history
```
GET https://api.chutes.ai/payments?page=0&limit=50
```
Each record includes: `payment_id`, `ss58_address`, `rao_amount`, `fmv` (USD per TAO at time of deposit), `usd_amount`, `transaction_hash`, `tx_link`, `block`, `timestamp`.

### Payment summaries (TAO deposits)
```
GET https://api.chutes.ai/payments/summary/tao
```
Returns `{ "today": <float>, "this_month": <float>, "total": <float> }` in USD.

---

## Quota & Usage Tracking

**View quota limits:**
```
GET https://api.chutes.ai/users/me/quotas
```
Returns a bare array (not paginated). `chute_id: "*"` = global quota. `quota: 0` = unlimited.

**Subscription usage:**
```
GET https://api.chutes.ai/users/me/subscription_usage
```

**Per-model invocation stats (your usage, current day):**
```
GET https://api.chutes.ai/invocations/stats/llm
```
Returns per-model: `total_requests`, `total_input_tokens`, `total_output_tokens`, `average_tps`, `average_ttft`.

**Active discounts:**
```
GET https://api.chutes.ai/users/me/discounts
```

**Price overrides (if negotiated):**
```
GET https://api.chutes.ai/users/me/price_overrides
```

---

## Special Features

### Trusted Execution Environments (TEE)
Models with `confidential_compute: true` run inside Intel TDX hardware enclaves. Prompts and responses are hardware-isolated — even Chutes operators cannot read them. Attestation evidence available via `GET https://api.chutes.ai/chutes/{chute_id}/evidence`.

### Harvard Research Discount (25% off)
Use the endpoint `https://research-data-opt-in-proxy.chutes.ai/v1` as a drop-in replacement for `https://llm.chutes.ai/v1`. Same API, same models, same auth — but 25% cheaper. The trade-off: prompts and responses are recorded for joint research with Harvard on caching algorithms. Do NOT send sensitive data here. Verify discount is active via `GET https://api.chutes.ai/users/me/discounts`.

### Cache Hit Pricing
Repeated or similar prompts may hit Chutes' inference cache, automatically getting the discounted `input_cache_read` rate. This happens transparently.

### OAuth Apps ("Sign in with Chutes")
For building apps that authenticate via Chutes:
```
POST https://api.chutes.ai/idp/apps
Body: { "name": "...", "description": "...", "homepage_url": "...", "redirect_uris": [...], "scopes": ["openid","profile","chutes:invoke"] }
```
Returns `client_id` (prefixed `cid_`) and `client_secret` (prefixed `csc_`). Uses OAuth 2.0 Authorization Code with PKCE. See `references/api-reference.md` for full details.

---

## Deploying Custom Models

If the user wants to deploy their own model on the Chutes network:

1. Install the SDK: `pip install chutes`
2. Deploy: `chutes deploy my_chute:chute`
3. List deployments: `GET https://api.chutes.ai/chutes/`
4. Delete: `DELETE https://api.chutes.ai/chutes/{chute_id}`

Full SDK docs at `https://chutes.ai/docs`. Templates available for vLLM, SGLang, and Diffusion.

---

## Credential Security Checklist

When helping a user set up Chutes, always:

1. **Warn about the fingerprint** — it's shown once, ever. Losing it without a linked wallet means losing access.
2. **Save credentials to the secure store** — run `manage_credentials.py set-profile` immediately after registration to store secrets in the OS keychain. Do NOT save credentials to plaintext files.
3. **Explain the API key** — also shown once (the `secret_key` field). If lost, delete the old key and create a new one.
4. **Mention fingerprint recovery** — if they link a Bittensor wallet (hotkey), they can reset the fingerprint at `https://chutes.ai/auth/reset` or via `POST https://api.chutes.ai/users/change_fingerprint`.
5. **Never echo secrets in conversation** — use `manage_credentials.py get --field api_key` to retrieve credentials programmatically; never paste raw values into the chat.

---

## Quick Reference: Key Endpoints

| What | Method | URL |
|------|--------|-----|
| Register | POST | `https://api.chutes.ai/users/register` |
| Login | POST | `https://api.chutes.ai/users/login` |
| My account info | GET | `https://api.chutes.ai/users/me` |
| Create API key | POST | `https://api.chutes.ai/api_keys/` |
| List API keys | GET | `https://api.chutes.ai/api_keys/` |
| Delete API key | DELETE | `https://api.chutes.ai/api_keys/{id}` |
| List models | GET | `https://llm.chutes.ai/v1/models` |
| Chat completions | POST | `https://llm.chutes.ai/v1/chat/completions` |
| Check balance | GET | `https://api.chutes.ai/users/me` (balance field) |
| Payment history | GET | `https://api.chutes.ai/payments` |
| TAO payment summary | GET | `https://api.chutes.ai/payments/summary/tao` |
| Quota limits | GET | `https://api.chutes.ai/users/me/quotas` |
| Usage stats | GET | `https://api.chutes.ai/invocations/stats/llm` |
| Discounts | GET | `https://api.chutes.ai/users/me/discounts` |
| Transfer balance | POST | `https://api.chutes.ai/users/balance_transfer` |
| List model aliases | GET | `https://api.chutes.ai/model_aliases/` |
| Create model alias | POST | `https://api.chutes.ai/model_aliases/` |
| Swagger docs | — | `https://api.chutes.ai/docs` |

---

## Additional Resources

For detailed endpoint schemas and parameters beyond what's covered here, read `references/api-reference.md`.

- **Full API docs**: `https://api.chutes.ai/docs` (Swagger UI)
- **SDK docs**: `https://chutes.ai/docs`
- **Quick start**: `https://chutes.ai/docs/getting-started/quickstart`
- **Machine-readable index**: `https://chutes.ai/docs.json`
- **OpenAPI schema**: `https://api.chutes.ai/openapi.json`
- **Plugin manifest**: `https://chutes.ai/.well-known/ai-plugin.json`
- **GitHub repos**: `https://github.com/chutesai/chutes` (SDK), `https://github.com/chutesai/chutes-api` (API)
- **Knowledge base**: `https://chutesai.zohodesk.com/portal/en/kb/chutes-ai`
