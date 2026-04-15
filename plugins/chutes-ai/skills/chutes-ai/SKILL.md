---
name: chutes-ai
description: "Chutes.ai hub skill — the entry point for decentralized open-source AI inference on Chutes. Use this skill when a user mentions Chutes, chutes.ai, decentralized AI, DeepSeek/Llama/Qwen API access, serverless GPU inference, or wants to register, manage API keys, discover models, or make OpenAI-compatible inference calls. This is the hub: it handles the session credential check, account lifecycle, API key lifecycle, basic inference, and routes to sibling skills (chutes-sign-in, chutes-deploy, chutes-mcp-portability, chutes-routing, chutes-usage-and-billing, chutes-platform-ops, chutes-agent-registration) for everything else."
---

# Chutes.ai — Hub Skill (four product lanes)

This skill is the **hub** for Chutes.ai integration. It covers the "Use Chutes" lane end-to-end (account → API keys → models → inference) and routes to sibling skills for the other three lanes.

Chutes provides OpenAI-compatible inference for top open-source models (DeepSeek, Llama, Qwen, and many more) on decentralized GPU infrastructure. Many models are free or very cheap. Any tool that talks to OpenAI can point at Chutes instead.

## Four product lanes

| Lane | What | Skill |
|---|---|---|
| **Use Chutes** | Account, API keys, models, inference, routing basics | `chutes-ai` (this skill) |
| **Build on Chutes** | Sign in with Chutes, OAuth apps, framework adapters | `chutes-sign-in` **[BETA]** |
| **Operate on Chutes** | Model aliases, usage/quota/billing, secret rotation, token lifecycle | `chutes-routing` / `chutes-usage-and-billing` / `chutes-platform-ops` (wave 2 stubs) |
| **Run agents with Chutes** | Claude / Hermes / Cursor / Aider via MCP + drop-in configs | `chutes-mcp-portability` **[BETA]** |

Plus: deploying your own chutes (vLLM / diffusion / custom CDK / teeify) lives in `chutes-deploy` **[BETA]**, and agent-native self-onboarding lives in `chutes-agent-registration` (wave 2 stub).

## Skill router — when to hand off

Hand off to the matching sibling skill immediately when the user says anything in the right column:

| Hand off to | User intent |
|---|---|
| `chutes-sign-in` | "Add Sign in with Chutes to my app", OAuth app, `/idp/apps`, PKCE, `cid_`/`csc_`, rotate client secret, scopes, Next.js auth |
| `chutes-deploy` | Deploy a model on Chutes, vLLM chute, diffusion chute, build a chute image, teeify, rolling updates, `POST /chutes/`, `POST /images/` |
| `chutes-mcp-portability` | Use Chutes from Cursor / Cline / Aider / Hermes / Claude Desktop, MCP server, drop-in config, make Chutes available to another agent |
| `chutes-routing` (stub) | `default:latency`, `default:throughput`, inline model pools, stable model aliases, routing recipes, cost-aware routing |
| `chutes-usage-and-billing` (stub) | Chutes spend, quotas, discounts, subscription usage, payment history, invocation stats |
| `chutes-platform-ops` (stub) | Rotate OAuth client secret (outside SIWC setup), introspect/revoke Chutes tokens, list authorizations, model alias CRUD |
| `chutes-agent-registration` (stub) | Agent self-onboarding without human signup, `POST /users/agent_registration`, hotkey-signed registration |

Wave 2 stubs describe scope and endpoints but do not yet have walkthroughs. When the user hits a stub, explain the stub status and point at the read-only MCP tools in `chutes-mcp-portability` for interim data.

---

## Session Initialization

When this skill is first invoked in a session, **check for stored credentials before doing anything else**:

```bash
python <skill-scripts-dir>/manage_credentials.py check
```

- If credentials exist → retrieve the API key silently for use in API calls:
  ```bash
  python <skill-scripts-dir>/manage_credentials.py get --field api_key
  ```
- If no credentials exist → proceed with Account Creation (below) and save immediately after.
- **Never paste raw `cpk_` / `cid_` / `csc_` values into the conversation.** Use them only in request headers and subprocess stdin.

Replace `<skill-scripts-dir>` with `plugins/chutes-ai/skills/chutes-ai/scripts/` in this repo.

---

## Quick Orientation

Two base URLs:

| Purpose | URL |
|---|---|
| Account management (keys, billing, chutes, `/idp/*`) | `https://api.chutes.ai` |
| Inference (OpenAI-like request/response shape) | `https://llm.chutes.ai/v1` |

Wave-3 live auth finding (verified 2026-04-15): auth differs by surface.
- Inference worked with `X-API-Key: cpk_...`
- Bearer auth with a `cpk_...` key returned 401 on live `/v1/models` and `/v1/chat/completions` tests
- Management endpoints like `/users/me` worked with the JWT returned by `POST /users/login` (fingerprint)
- CLI CRUD endpoints like `GET /api_keys/` worked with hotkey-signed headers, not `cpk_...`

Do not assume one auth header works everywhere.

---

## Step 1: Account Creation

Chutes uses a **32-character alphanumeric fingerprint** as the primary credential. It is shown **only once** during creation and cannot be recovered without a linked Bittensor wallet.

**Via API (recommended for agents):**
```
POST https://api.chutes.ai/users/register
Body: { "username": "desired-username" }
```
Usernames: 3–20 characters, alphanumeric.

Wave-3 live registration finding (verified 2026-04-15): the practical agent flow has extra prerequisites not captured in the bare endpoint sketch above.

- Registration requires a human-obtained one-time token from `https://rtok.chutes.ai/users/registration_token`.
- That token is protected by Cloudflare / browser verification and may be IP-bound, so a headless agent may need the user to fetch and paste it.
- The registering coldkey must have at least `0.25 TAO`, otherwise the API returns: `You must have at least 0.25 tao on your coldkey to register an account.`
- The token can expire or mismatch the caller IP; if registration starts failing with `Invalid registration token, or registration token does not match expected IP address`, fetch a fresh token and retry immediately.

For agent-led onboarding, treat this as a human-in-the-loop step rather than a fully autonomous one.

**Via web browser:** direct users to `https://chutes.ai/auth/start` (the "Create Account" button on `https://chutes.ai/auth` opens a support widget, not the form).

**Via Google / GitHub:** `https://chutes.ai/auth` → OAuth sign-in → link account.

After registration:
1. Show the fingerprint to the user clearly.
2. Save it to the credential store immediately (Step 2b below).
3. Mention recovery: if they link a Bittensor wallet, they can reset via `https://chutes.ai/auth/reset` or `POST /users/change_fingerprint`.

**Login:** `POST /users/login` with the fingerprint returns a session/JWT for further operations.

---

## Step 2: API Key Creation

```
POST https://api.chutes.ai/api_keys/
Body: { "name": "my-agent-key", "admin": false }
```

Response includes `secret_key` (prefixed `cpk_`) — **shown only once**. Save immediately.

Other API key operations:
- `GET /api_keys/` — list (no `secret_key` returned)
- `DELETE /api_keys/{api_key_id}` — revoke

The `user_id` is embedded in the key itself (`cpk_<key_id>.<user_id_hex>.<secret>`), or just call `GET /users/me`.

---

## Step 2b: Credential Store

After creating an account and API key, **immediately save credentials** to the secure credential store (OS keychain on macOS / Linux Secret Service, AES-256-GCM encrypted file fallback).

```bash
python <skill-scripts-dir>/manage_credentials.py set-profile \
  --username <username> \
  --user-id <user_id> \
  --fingerprint <fingerprint> \
  --api-key <api_key>
```

Read in a new session:
```bash
python <skill-scripts-dir>/manage_credentials.py get --field api_key
python <skill-scripts-dir>/manage_credentials.py get                # all fields as JSON
```

Multiple profiles: `--profile <name>` on any command. `list-profiles` to enumerate. `check` to inspect backend / permissions without revealing secrets.

**OAuth app credentials** (for Sign in with Chutes) use the same store under distinct fields:
```bash
python <skill-scripts-dir>/manage_credentials.py set-profile \
  --profile oauth.my-app \
  --client-id <cid_...> \
  --client-secret <csc_...>
```

Env var overrides (highest priority, for CI/CD):
- `CHUTES_API_KEY`, `CHUTES_FINGERPRINT`
- `CHUTES_OAUTH_CLIENT_ID` / `CHUTES_CLIENT_ID` (either is accepted)
- `CHUTES_OAUTH_CLIENT_SECRET` / `CHUTES_CLIENT_SECRET` (either is accepted)
- `CHUTES_PROFILE` (profile name)

Security details live in `references/api-reference.md` and `docs/credential-store.md`.

---

## Step 3: Model Discovery

```
GET https://llm.chutes.ai/v1/models
X-API-Key: cpk_...
```

Each model exposes `id`, `root`, `chute_id`, `confidential_compute` (boolean — **use this, not the `-TEE` suffix**, as source of truth), `owned_by` (`sglang` / `vllm`), `pricing.{prompt,completion,input_cache_read}` (USD per 1M tokens), `context_length`, `max_output_length`, `supported_features` (`tools`, `json_mode`, `structured_outputs`, `reasoning`), `supported_sampling_parameters`, `input_modalities`, `output_modalities`, `quantization`.

Chutes hosts more than LLMs: **image, video, TTS (54 voices / 9 languages), STT, music, moderation, and custom inference.**

Quick static reference: `references/known-models.md`. Always query the live endpoint for authoritative data.

When helping users choose:
- **Task** → DeepSeek-R1 (reasoning), DeepSeek-V3 / Llama / Qwen (chat), specialized code models.
- **Privacy** → filter `confidential_compute: true`.
- **Cost** → `pricing.prompt`, `pricing.completion`, cache hits via `pricing.input_cache_read`.
- **Features** → `supported_features` (not every model has tools / structured output).
- **Context** → match `context_length`.

---

## Step 4: Making Inference Calls

Chutes uses OpenAI-like request/response shapes on the inference surface, but live auth currently differs from OpenAI SDK defaults.

Verified live 2026-04-15:
- `X-API-Key: cpk_...` worked for inference
- Bearer auth with a `cpk_...` key returned 401 on `/v1/models` and `/v1/chat/completions`

So for direct HTTP calls, use `X-API-Key`.

For generic OpenAI SDKs that hardcode `Authorization: Bearer`, treat Chutes as **conditionally compatible** until the platform accepts Bearer `cpk_...` on the inference surface.

**Python (raw HTTP until Bearer `cpk_...` is accepted live):**
```python
import requests

response = requests.post(
    "https://llm.chutes.ai/v1/chat/completions",
    headers={"X-API-Key": "cpk_...", "Content-Type": "application/json"},
    json={
        "model": "deepseek-ai/DeepSeek-V3-0324",
        "messages": [{"role": "user", "content": "Hello!"}],
    },
    timeout=60,
)
response.raise_for_status()
print(response.json()["choices"][0]["message"]["content"])
```

**cURL:**
```bash
curl https://llm.chutes.ai/v1/chat/completions \
  -H "X-API-Key: cpk_..." \
  -H "Content-Type: application/json" \
  -d '{"model":"deepseek-ai/DeepSeek-V3-0324","messages":[{"role":"user","content":"Hello!"}]}'
```

**Node (raw fetch until Bearer `cpk_...` is accepted live):**
```javascript
const response = await fetch('https://llm.chutes.ai/v1/chat/completions', {
  method: 'POST',
  headers: {
    'X-API-Key': 'cpk_...',
    'Content-Type': 'application/json',
  },
  body: JSON.stringify({
    model: 'deepseek-ai/DeepSeek-V3-0324',
    messages: [{ role: 'user', content: 'Hello!' }],
  }),
});
```

**Vercel AI SDK:** `npm install @chutes-ai/ai-sdk-provider`.

Different engines (`sglang` vs `vllm`) accept different sampling params — check `supported_sampling_parameters` before passing non-standard options.

### Inline routing (one-liner; full recipes in `chutes-routing`)

Pass a comma-separated model list as `model` for sequential failover, append `:latency` or `:throughput` to rank by live metrics:
```
model="zai-org/GLM-5-Turbo,zai-org/GLM-4.7-TEE,Qwen/Qwen3-32B-TEE:latency"
```

Saved pools via the dashboard use `default`, `default:latency`, `default:throughput`. For routing recipes, stable aliases, and cost-aware routing, hand off to the `chutes-routing` skill (wave 2 stub — use the MCP tools meanwhile).

---

## Step 5: Account Info & Basic Balance

```
GET https://api.chutes.ai/users/me
```
Use the JWT returned by `POST /users/login` (fingerprint) for this endpoint.

Live finding: `cpk_...` did not work against `/users/me`; Bearer JWT did.

Returns `username`, `user_id`, `balance` (USD), `payment_address` (Bittensor SS58), `hotkey`/`coldkey`, `quotas`, `permissions`.

For anything beyond a balance check — discounts, quotas by chute, subscription usage, invocation stats, payment history — hand off to `chutes-usage-and-billing` (wave 2 stub; use MCP read tools in the meantime).

---

## Special features (one-line summaries, deep content in siblings)

- **TEE (confidential compute).** Models with `confidential_compute: true` run in Intel TDX. Attestation evidence: `GET /chutes/{chute_id}/evidence`. Full verification flow is wave 2.
- **Harvard research endpoint (25% off).** Drop-in replacement base URL `https://research-data-opt-in-proxy.chutes.ai/v1`. Trade-off: prompts/responses are recorded for research. Do not send sensitive data.
- **Cache hit pricing.** Repeated prompts transparently hit the cache and pay `pricing.input_cache_read`.
- **Sign in with Chutes.** OAuth 2.0 + PKCE. `POST /idp/apps`, `cid_` / `csc_` returned. Full integrator flow lives in `chutes-sign-in`.
- **Model aliases.** Stable semantic handles via `/model_aliases/`. Recommended packs (`interactive-fast`, `private-reasoning`, `cheap-background`, `agent-coder`, `tee-chat`) live in `chutes-routing` stub; create one with `chutes-deploy` → `alias_deploy.py` **[BETA]**.
- **Custom deployment.** `chutes-deploy` **[BETA]** covers vLLM / diffusion / teeify / rolling updates.

---

## Credential Security Checklist

1. **Fingerprint is shown once.** Losing it without a linked wallet means losing access.
2. **Always save credentials to the keychain store.** Never write them to plaintext files.
3. **API key is shown once.** If lost, delete the key and create a new one.
4. **Never echo secrets in conversation.** Use `manage_credentials.py get --field <field>` and pipe the output.
5. **Fingerprint recovery** works if a Bittensor wallet is linked (`https://chutes.ai/auth/reset` or `POST /users/change_fingerprint`).

---

## Quick Reference: Key Endpoints

| What | Method | URL |
|---|---|---|
| Register | POST | `https://api.chutes.ai/users/register` |
| Login | POST | `https://api.chutes.ai/users/login` |
| My account info | GET | `https://api.chutes.ai/users/me` |
| Create / list / delete API key | POST / GET / DELETE | `https://api.chutes.ai/api_keys/[{id}]` |
| List models | GET | `https://llm.chutes.ai/v1/models` |
| Chat completions | POST | `https://llm.chutes.ai/v1/chat/completions` |
| Payment history | GET | `https://api.chutes.ai/payments` |
| Quota limits | GET | `https://api.chutes.ai/users/me/quotas` |
| Discounts | GET | `https://api.chutes.ai/users/me/discounts` |
| List / create model alias | GET / POST | `https://api.chutes.ai/model_aliases/` |
| OAuth app create | POST | `https://api.chutes.ai/idp/apps` |
| Chute TEE evidence | GET | `https://api.chutes.ai/chutes/{id}/evidence` |

Everything else: see `references/api-reference.md` or `https://api.chutes.ai/openapi.json`.

---

## Additional Resources

- `references/api-reference.md` — extended endpoint details
- `references/known-models.md` — static snapshot of popular models
- `references/model-aliases.md` — alias packs + lifecycle (NEW)
- `docs/sign-in-with-chutes.md` — OAuth / app builder overview
- `docs/model-aliases.md` — why aliases beat hardcoded IDs
- Full Swagger docs: `https://api.chutes.ai/docs`
- Plugin manifest: `https://chutes.ai/.well-known/ai-plugin.json`
- OpenAPI schema: `https://api.chutes.ai/openapi.json`
- Knowledge base: `https://chutesai.zohodesk.com/portal/en/kb/chutes-ai`
