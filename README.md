# Chutes Agent Toolkit

> **Give any AI agent access to [Chutes.ai](https://chutes.ai)** — decentralized, serverless, 100%-TEE inference for open-source models, through the OpenAI API.

[![Refresh Chutes models](https://github.com/Veightor/chutes-agent-toolkit/actions/workflows/refresh-chutes-models.yml/badge.svg)](https://github.com/Veightor/chutes-agent-toolkit/actions/workflows/refresh-chutes-models.yml)
[![Models](https://img.shields.io/badge/dynamic/json?url=https%3A%2F%2Fraw.githubusercontent.com%2FVeightor%2Fchutes-agent-toolkit%2Fmain%2Fdata%2Fchutes-models.json&query=%24.count&label=models&color=brightgreen&logo=huggingface&logoColor=white)](https://llm.chutes.ai/v1/models)
[![Models updated](https://img.shields.io/badge/dynamic/json?url=https%3A%2F%2Fraw.githubusercontent.com%2FVeightor%2Fchutes-agent-toolkit%2Fmain%2Fdata%2Fchutes-models.json&query=%24.fetched_at&label=models%20updated&color=2496ED&logo=githubactions&logoColor=white)](data/chutes-models.json)
[![Plugin version](https://img.shields.io/badge/dynamic/json?url=https%3A%2F%2Fraw.githubusercontent.com%2FVeightor%2Fchutes-agent-toolkit%2Fmain%2Fplugins%2Fchutes-ai%2F.claude-plugin%2Fplugin.json&query=%24.version&label=plugin&prefix=v&color=blueviolet)](plugins/chutes-ai/.claude-plugin/plugin.json)
[![API: OpenAI-compatible](https://img.shields.io/badge/API-OpenAI--compatible-412991?logo=openai&logoColor=white)](docs/endpoint-guide.md)
[![Inference: 100% TEE](https://img.shields.io/badge/inference-100%25%20TEE--backed-success?logo=intel&logoColor=white)](docs/endpoint-guide.md#8-privacy-every-model-is-a-tee)
[![Powered by Bittensor](https://img.shields.io/badge/powered%20by-Bittensor-FF6B00)](https://bittensor.com)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

One toolkit, every agent. Drop Chutes into **Claude**, **Hermes**, **OpenClaw**, or any OpenAI-compatible client — decentralized serverless inference for open-source models (Kimi, GLM, Qwen, DeepSeek, MiniMax, Gemma, Nemotron, Mistral), powered by Bittensor. The hosted catalog is currently **all TEE-backed** (`confidential_compute: true`); the live list at [`https://llm.chutes.ai/v1/models`](https://llm.chutes.ai/v1/models) is always the source of truth (and the badges above read straight from the daily-refreshed snapshot).

### 🚀 Start here

| You want to… | Go to |
|---|---|
| **Call the endpoint from anything** (the one-page universal guide) | 📘 [**`docs/endpoint-guide.md`**](docs/endpoint-guide.md) |
| Use it inside **Claude** (Code / Cowork) | [Install for Claude](#install-for-claude-code--cowork) |
| Use it inside **Hermes** | [`other-agents/hermes/`](other-agents/hermes/README.md) |
| Use it inside **OpenClaw** 🦞 **[BETA]** | [`other-agents/openclaw/`](other-agents/openclaw/README.md) |
| Use it in **Aider / Cursor / Cline / LangChain / LiteLLM** | [`other-agents/openai-compatible/`](other-agents/openai-compatible/README.md) |
| Drop it into **any agent's system prompt** | [`other-agents/system-prompt/`](other-agents/system-prompt/chutes-agent-prompt.md) |

This repo is both a **Claude plugin marketplace** and a **multi-agent toolkit** — the same skills, scripts, and docs work everywhere. It also stages Hermes integration assets: custom-provider configuration, a Hermes skill mirror, and MCP setup guidance that track current Hermes CLI behavior.

### Versions

| Component | Version | Notes |
|---|---|---|
| Toolkit / `chutes-ai` plugin | **v1.3.0** | see [`plugin.json`](plugins/chutes-ai/.claude-plugin/plugin.json) |
| Model snapshot | _auto_ | daily-refreshed → badges above + [`data/chutes-models.json`](data/chutes-models.json) |
| Chutes SDK (PyPI `chutes`) | 0.6.9 (stable) | for `chutes deploy` / TEE `tee=True` |
| Hermes (verified against) | v0.16.0 | named OpenAI-compatible provider |
| OpenClaw (verified against) | `openclaw@latest` | `models.providers` JSON5 config |
| Last live API re-verification | 2026-06-11 | auth + catalog + TEE, see below |

---

## The four product lanes

The toolkit is organized around four product lanes, each with one or more focused skills:

| Lane | What it covers | Skills |
|---|---|---|
| **Use Chutes** | Account, API keys, models, OpenAI-compatible inference, basic routing, TEE model selection. | `chutes-ai` (hub), `chutes-routing`, `chutes-tee` |
| **Build on Chutes** | "Sign in with Chutes" — OAuth 2.0 + OIDC + PKCE. Register apps, vendor the upstream Next.js package, manage scopes, rotate client secrets safely. | `chutes-sign-in` |
| **Operate on Chutes** | Spend + quota dashboards, fleet-scale OAuth app audit, bulk secret rotation, alias governance, TEE attestation verification. | `chutes-usage-and-billing`, `chutes-platform-ops`, `chutes-tee` |
| **Run agents with Chutes** | Chute deploy (vLLM / diffusion / TEE via the SDK's `tee=True`), MCP server + drop-in configs for Cursor / Cline / Aider / Hermes / Claude Desktop, autonomous agent registration. | `chutes-deploy` **[BETA]**, `chutes-mcp-portability`, `chutes-agent-registration` **[BETA]** |

Wave 1 shipped the core four-lane split with wave-2 skills as stubs. **Wave 2 landed all four wave-2 stubs as full live-verified skills + a new `chutes-tee` attestation skill**, and graduated most wave-1 items out of BETA after live end-to-end verification against a real Chutes account.

---

## Beta features

Anything that touches chute deployment — or anything that hasn't been exercised against a live Chutes account before the commit that introduced it — ships labeled **BETA**. A BETA label is only removed by a commit that references a recorded verification run.

### Wave-2 live verification (2026-04-13) — what graduated

Exercised end-to-end against a real Chutes account during wave 2 (see `~/.claude/plans/chutes-maxi-wave-2.md`) and **graduated out of BETA**. Every non-deploy skill was verified with real API calls and real data shapes.

- **`chutes-sign-in`** — full `register → vendor → rotate` cycle verified on a scratch Next.js App Router project; OAuth app created + deleted server-side. Two real wave-1 bugs caught and fixed during verification (wrong upstream source paths; `rotate_secret.py` path segment using `client_id` instead of `app_id` UUID). Only `verify_siwc.py` step 4 (dev-server hit) stays BETA.
- **`chutes-mcp-portability`** — `chutes-mcp-server --self-check` passed + 7 read tools exercised live: `chutes_list_models`, `chutes_get_quota`, `chutes_list_aliases`, `chutes_list_chutes`, `chutes_get_usage`, `chutes_get_discounts`, `chutes_list_api_keys`.
- **`chutes-routing`** — new full skill. `build_pool.py` verified across 3 intents + alias round-trip; `audit_pool.py` verified. Caught + fixed wave-1 schema bug: `/model_aliases/` accepts `{alias, chute_ids:[uuid,...]}`, not `{alias, model}`.
- **`chutes-usage-and-billing`** — new full skill. `spend_summary.py`, `cost_breakdown.py`, `quota_guard.py`, `download_export.py` all verified. Discovered that `/users/me/subscription_usage` is the real personal spend dashboard (4-hour + monthly caps); `/invocations/*` and `/payments*` are platform-wide aggregates; exports are CSV not JSON.
- **`chutes-platform-ops`** — new full skill. `list_apps.py`, `audit_stale_apps.py`, `rotate_all.py --dry-run`, `alias_crud.py` all verified against 16 real OAuth apps on the test account. Found that `/idp/apps?mine=true` is ignored — client-side filter required.
- **`chutes-tee`** — brand new skill. `fetch_evidence.py`, `verify_quote.py`, `verify_gpu_attestation.py`, `attest_chute.py` all exercised live against a real TEE chute (`Qwen/Qwen3-32B-TEE`). Parsed real TDX v4 quote (5006 bytes, 7 instances, 56 Hopper GPUs). Ships as `shape-valid` verdict; cryptographic validation is opt-in via Intel DCAP tooling.
- **`manage_credentials.py`** — `app_id` field added; OAuth env aliases verified live.

### 2026-06-11 refresh — what changed on the platform

A full re-verification pass (real GETs against the live API, no management writes, plus a live paid completion call) updated the toolkit. The wave-2 records above are kept as history; current facts that supersede them:

- **Auth inverted since April**: `Authorization: Bearer cpk_...` now works on **both** `llm.chutes.ai` and `api.chutes.ai` — verified live 2026-06-11, including a real paid `POST /v1/chat/completions` (HTTP 200, completion returned); `X-API-Key` returns **401 on the management API**, and on inference it is **confirmed silently ignored**: the same completion POST sent with `X-API-Key` got the anonymous nginx 429 rate-limit response, byte-identical to a fully unauthenticated POST, while Bearer succeeded in the same minute. Bearer is the platform-recommended header everywhere. The old "fingerprint-login JWT required for `/users/me`" workaround is no longer needed for GETs. `GET /v1/models` is now public (no auth required).
- **Catalog collapsed to TEE-only**: 13 models, every one `-TEE` / `confidential_compute: true`. The entire non-TEE tier (including all Llama models) is gone. New flagships since April: Kimi-K2.5/K2.6, GLM-5/5.1, Qwen3.5-397B, MiniMax-M2.5, DeepSeek-V3.2, Gemma-4, Nemotron-3-Ultra.
- **`PUT /chutes/{id}/teeify` is gone from the API** (verified absent from `openapi.json` 2026-06-11). The deploy-side TEE switch is the SDK's `tee=True` template kwarg. `teeify_chute.py` and the MCP `chutes_teeify` tool are marked defunct.
- **TEE attestation re-verified end-to-end**: the same Qwen3-32B-TEE chute now reports 14 instances on **Blackwell** GPUs (was 7 instances / Hopper in April); evidence endpoint requires a 64-hex-char `nonce` query param; new public `GET /servers/tee/measurements` golden-measurement endpoint verified.
- **Usage/billing re-verified**: `spend_summary.py`, `cost_breakdown.py`, `quota_guard.py` all ran live unchanged. Hourly exports now need a `.csv` suffix and are frozen at 2026-04-20 (later dates 404; `/invocations/exports/recent` returns 500 — unverified whether intentional, as of 2026-06-11).
- **Agent registration**: live status GET re-verified; terminal status is `"completed"` (not `"ready"` as previously documented).
- Read-only scripts across `chutes-platform-ops`, `chutes-routing`, and `chutes-agent-registration` were re-run live; write/deploy flows were not re-exercised and keep their existing labels. Exception: `POST /v1/chat/completions` **was** exercised live with Bearer on 2026-06-11 (direct model id, `unsloth/Mistral-Nemo-Instruct-2407-TEE`) — the response carried `x-chutes-invocationid` plus quota headers, and `usage.prompt_tokens_details.cached_tokens` shows prompt caching is active on inference.

### Still BETA

- **`chutes-deploy`** — permanent BETA under the deploy-features policy. Wave-2 live verification found that the easy-deploy lanes (`POST /chutes/vllm`, `POST /chutes/diffusion`) were gated server-side with HTTP 403 `{"detail":"Easy deployment is currently disabled!"}` on at least some account classes; both endpoints are still present in `openapi.json` but the gate could not be re-probed read-only, so assume gated (unverified as of 2026-06-11). The API requires `revision` to be a full 40-hex HF commit SHA (`^[a-fA-F0-9]{40}$`) — now verified server-side, and `--revision` branch→SHA auto-resolve is in place. `teeify_chute.py` is **[BETA — DEFUNCT]**: `PUT /chutes/{id}/teeify` no longer exists. A new self-serve private TEE deploy product (RTX Pro 6000, $1.80/hr + 3× hourly deploy fee) appeared on the pricing page **[BETA]** (unverified as of 2026-06-11).
- **`chutes-agent-registration`** — dry-run verified. Stays BETA because creating a real Bittensor-backed agent account has on-chain implications that are the wrong shape for automated verification. Graduates on the first intentional human-initiated agent registration.
- **`chutes-sign-in:verify_siwc.py`** — steps 1-3 (files / env / keychain) verified live; step 4 (dev server `/api/auth/chutes/session` hit) requires `npm install` + `npm run dev` which is out of scope for automated verification.
- **`chutes-platform-ops:introspect_token.py` / `revoke_token.py`** — both need a real OAuth access token from a completed SIWC browser flow. Graduate on the first live run against a real token.
- **`chutes-mcp-portability` write tools** — `chutes_deploy_vllm`, `chutes_deploy_diffusion`, `chutes_teeify` (now also deprecated in place: the upstream endpoint is gone), `chutes_set_alias`, `chutes_delete_alias`, `chutes_create_api_key` stay permanent BETA under the deploy-features policy. `chutes_set_alias` / `chutes_delete_alias` were functionally exercised in wave 2 (and the wave-1 schema bug was fixed), but deploy-side writes keep the label.
- **`chutes-mcp-portability` three unexercised read tools** — `chutes_chat_complete` (the underlying `POST /v1/chat/completions` + Bearer auth were verified live 2026-06-11 via direct curl, but the tool itself has not been exercised through the MCP path), `chutes_get_evidence` (the `chutes-tee` skill exercises the underlying endpoint but not through the MCP path), `chutes_oauth_introspect` (needs a live OAuth token).
- **`chutes-tee` verified-verdict pipeline** — the scripts detect Intel DCAP but the cryptographic-validation wiring is spec-only; `shape-valid` remains the practical verdict ceiling **[BETA]**.
- **Research data-opt-in proxy (25% discount)** — documented from `chutes.ai/llms.txt`, not exercised end-to-end on this account **[BETA]**.

---

## Install for Claude (Code / Cowork)

### Option 1: Plugin Marketplace (recommended)

Add this repo as a marketplace, then install the plugin:

```
/plugin marketplace add YOUR_ORG/chutes-agent-toolkit
/plugin install chutes-ai@chutes-agent-toolkit
```

Claude now has the full four-lane skill suite. Try asking:

- *"Set me up with a Chutes account and API key"* → `chutes-ai` hub
- *"Add Sign in with Chutes to my Next.js app"* → `chutes-sign-in` **[BETA]**
- *"Deploy Qwen 3 as a vLLM chute with a stable alias"* → `chutes-deploy` **[BETA]**
- *"Make Chutes available in Cursor via MCP"* → `chutes-mcp-portability` **[BETA]**
- *"What open-source models are available on Chutes?"* → `chutes-ai` hub
- *"Set up TEE-only routing for lowest latency"* → `chutes-ai` hub (deep recipes in `chutes-routing`)

### Option 2: Direct Skill Copy

If you prefer not to use the marketplace system, copy the skills directly:

```bash
cp -r plugins/chutes-ai/skills/* ~/.claude/skills/
```

## Install for Other Agents

### Hermes

Hermes works with Chutes today via named OpenAI-compatible provider configuration (`providers:` preferred, legacy `custom_providers:` still supported), and has a full Hermes skill mirror at `other-agents/hermes/skills/`:

- `other-agents/hermes/skills/chutes-ai/` — hub
- `other-agents/hermes/skills/chutes-sign-in/` **[BETA: dev-server verification only]**
- `other-agents/hermes/skills/chutes-routing/` — verified routing + alias pool builder
- `other-agents/hermes/skills/chutes-usage-and-billing/` — verified read-only spend/quota diagnostics
- `other-agents/hermes/skills/chutes-platform-ops/` — mixed; token scripts remain BETA
- `other-agents/hermes/skills/chutes-deploy/` **[BETA: deploy-side writes]**
- `other-agents/hermes/skills/chutes-mcp-portability/` — MCP read tools verified; write tools BETA
- `other-agents/hermes/skills/chutes-agent-registration/` **[BETA]**
- `other-agents/hermes/skills/chutes-tee/` — TEE evidence parsing, shape-valid attestation

See also:
- [`docs/hermes-chutes-toolkit-guide.md`](docs/hermes-chutes-toolkit-guide.md)
- [`other-agents/hermes/README.md`](other-agents/hermes/README.md)
- [`other-agents/hermes/config-examples/`](other-agents/hermes/config-examples/)

Hermes users can either copy those skills into `~/.hermes/skills/` or mount the directory with `skills.external_dirs` in `~/.hermes/config.yaml`. Scripts live in the Claude plugin tree; Hermes users invoke them from the repo root. There is one implementation, two skill trees.

### OpenClaw 🦞 **[BETA]**

> **[BETA]** Doc-derived from OpenClaw's official model-providers guide; the Chutes side is live-verified, the OpenClaw wiring is not yet exercised end-to-end. Details in [`other-agents/openclaw/README.md`](other-agents/openclaw/README.md).

[OpenClaw](https://openclaw.ai) is a self-hosted gateway that wires your chat apps (Discord, Slack, Telegram, iMessage, WhatsApp, Teams, Signal, Matrix, …) to AI coding agents. Chutes plugs in as an OpenAI-compatible provider in `openclaw.json` (JSON5), so your channel agents run on open-source TEE models:

```json5
models: {
  providers: {
    chutes: {
      baseUrl: "https://llm.chutes.ai/v1",
      apiKey: "${CHUTES_API_KEY}",
      api: "openai-completions",
      models: [{ id: "deepseek-ai/DeepSeek-V3.2-TEE", name: "DeepSeek V3.2 (TEE)" }],
    },
  },
}
```

Full guide + routing/vision config examples: [`other-agents/openclaw/README.md`](other-agents/openclaw/README.md) · [`config-examples/`](other-agents/openclaw/config-examples/).

### Any OpenAI-compatible client (Aider, Cursor, Cline, LangChain, LiteLLM, …)

The `chutes-mcp-portability` skill generates drop-in configs:

```bash
python plugins/chutes-ai/skills/chutes-mcp-portability/scripts/generate_agent_config.py \
  --target cursor,aider,hermes
```

For MCP-aware clients, install the stdio MCP server:

```bash
uv tool install chutes-mcp-server \
  --from plugins/chutes-ai/skills/chutes-mcp-portability/mcp-server
```

See [`other-agents/openai-compatible/README.md`](other-agents/openai-compatible/README.md) for the raw OpenAI-compat setup.

### Any LLM Agent (GPT, Gemini, Llama, etc.)

Copy the contents of [`other-agents/system-prompt/chutes-agent-prompt.md`](other-agents/system-prompt/chutes-agent-prompt.md) (or generate a fresh one via `generate_agent_config.py --target system-prompt`) into your agent's system prompt.

Quick inference snippet (verified live auth shape, 2026-06-11):

```python
import requests

response = requests.get(
    "https://llm.chutes.ai/v1/models",
    headers={"Authorization": "Bearer cpk_..."},
    timeout=30,
)
response.raise_for_status()
```

Note: auth behavior **inverted** since the April verification. Live tests on 2026-06-11 show `Authorization: Bearer cpk_...` working on both `llm.chutes.ai` and `api.chutes.ai` — including a real paid `POST /v1/chat/completions` (HTTP 200, completion returned) — while `X-API-Key` returns 401 on the management API and is **confirmed silently ignored on inference** (a completion POST with it hit the anonymous 429 path, byte-identical to no auth at all). Use Bearer everywhere — this is also what the platform's own `ai-plugin.json` instructs. Standard OpenAI SDKs (which send Bearer) work as-is. `GET /v1/models` no longer requires auth at all.

Standard machine-readable interfaces:

- **Plugin manifest**: `https://chutes.ai/.well-known/ai-plugin.json`
- **OpenAPI spec**: `https://api.chutes.ai/openapi.json`
- **Agent-facing docs**: `https://chutes.ai/llms.txt` (also `llms-full.txt` and `docs.json`)

---

## What agents can do

- **Create accounts** — register on Chutes.ai with proper credential handling and backup
- **Manage API keys** — create, list, and delete `cpk_` prefixed keys
- **Secure credential store** — save keys to the OS keychain and read them back in future sessions
- **Discover models** — browse the live catalog with real-time pricing from `/v1/models`; `docs/known-models.md` and `data/chutes-models.json` are auto-refreshed daily by GitHub Actions from that public endpoint. TTFT/TPS comes from `/invocations/stats/llm`, not the models list
- **Make inference calls** — OpenAI-compatible request/response API; authenticate with `Authorization: Bearer cpk_...` everywhere
- **Model routing** — failover, latency-optimized, or throughput-optimized multi-model pools
- **Model aliases** — stable semantic handles like `interactive-fast` that survive model churn
- **Sign in with Chutes** **[BETA]** — turn any Next.js App Router app into an OAuth relying party
- **Deploy chutes** **[BETA]** — vLLM / diffusion / custom CDK deploy (TEE via `tee=True`), stream build logs
- **MCP portability** **[BETA]** — drive Chutes from Cursor / Cline / Aider / Hermes / Claude Desktop
- **Billing** — top up via crypto ($TAO/Bittensor) or Stripe (25+ payment methods)
- **Usage tracking** — quotas, invocation stats, per-model costs
- **TEE models** — hardware-isolated inference via Intel TDX for privacy-sensitive workloads; the entire hosted catalog is now TEE-backed, with verifiable attestation via the `chutes-tee` skill

---

## Secure credential store

This toolkit includes `manage_credentials.py` — a secure credential manager that stores API keys, fingerprints, and OAuth secrets in the **OS keychain** rather than plaintext files. Credentials persist across sessions and projects, so once saved, agents can read them back automatically in future conversations.

### Security model

| Data | Storage | Protection |
|------|---------|------------|
| `api_key` (`cpk_...`) | OS keychain | Encrypted at rest, per-app access control |
| `fingerprint` (32-char master credential) | OS keychain | Encrypted at rest, per-app access control |
| `client_id` / `client_secret` (OAuth apps, `cid_` / `csc_`) | OS keychain | Encrypted at rest, per-app access control |
| `username`, `user_id` (non-secret metadata) | `~/.chutes/config` | `chmod 600`, directory `chmod 700` |

**Backend auto-detection:**
- **macOS** → Keychain Access (via `security` command)
- **Linux** → freedesktop Secret Service (GNOME Keyring / KDE Wallet, via `secret-tool`)
- **Fallback** → AES-256-GCM encrypted file with key derived from machine identity (PBKDF2-SHA256, 600k iterations)

**What this protects against:**
- Other users on the same machine reading secrets
- Malware with user-level file access (keychain requires explicit app authorization)
- Disk image / backup theft (keychain entries are not in standard backups)
- Accidental git commits (`~/.chutes/.gitignore` contains `*` as a guard)
- `ps aux` exposure — secrets are never passed as command-line arguments to child processes

### CLI reference

```bash
# Save a full credential profile
python manage_credentials.py set-profile \
  --username alice \
  --user-id 550e8400-e29b-41d4-a716-446655440000 \
  --fingerprint <32-char-fingerprint> \
  --api-key cpk_...

# Read a specific field (raw value, safe for shell substitution)
python manage_credentials.py get --field api_key

# Read all fields as JSON
python manage_credentials.py get

# Update a single field
python manage_credentials.py set --field api_key --value cpk_new...

# Manage multiple profiles (default, production, oauth.my-app, etc.)
python manage_credentials.py set-profile --profile production --api-key cpk_prod...
python manage_credentials.py get --profile production --field api_key
python manage_credentials.py list-profiles

# Save OAuth app credentials (used by chutes-sign-in)
python manage_credentials.py set-profile \
  --profile oauth.my-app \
  --client-id cid_... \
  --client-secret csc_...

# Status check (shows backend, profiles, permissions — no secrets)
python manage_credentials.py check

# Delete a profile from both config and the keychain
python manage_credentials.py delete --profile production
```

### Environment variable overrides

For CI/CD and headless environments, env vars always take precedence over the stored keychain values:

| Variable | Field | Notes |
|---|---|---|
| `CHUTES_API_KEY` | `api_key` | |
| `CHUTES_FINGERPRINT` | `fingerprint` | |
| `CHUTES_OAUTH_CLIENT_ID` | `client_id` | preferred name (matches SIWC upstream) |
| `CHUTES_CLIENT_ID` | `client_id` | legacy alias, still accepted |
| `CHUTES_OAUTH_CLIENT_SECRET` | `client_secret` | preferred name |
| `CHUTES_CLIENT_SECRET` | `client_secret` | legacy alias, still accepted |
| `CHUTES_PROFILE` | active profile name | |

### Agent usage pattern

When any Chutes skill is invoked in a new session, it first runs `manage_credentials.py check` to see if credentials already exist. If so, it reads the API key silently for use in API calls — never pasting raw secrets into the conversation. If not, it walks the user through account creation and saves credentials immediately after.

> **Note on the deprecated `save_credentials.py`**: The original `save_credentials.py` script wrote credentials to a plaintext backup file. It is now deprecated and emits a warning — use `manage_credentials.py` for all new credential storage.

---

## Repo structure

```
chutes-agent-toolkit/
├── plugins/
│   └── chutes-ai/
│       ├── .claude-plugin/plugin.json
│       └── skills/
│           ├── chutes-ai/                    # hub (Use Chutes lane)
│           │   ├── SKILL.md
│           │   ├── references/
│           │   │   ├── api-reference.md
│           │   │   ├── known-models.md
│           │   │   └── model-aliases.md      # NEW
│           │   └── scripts/
│           │       ├── manage_credentials.py
│           │       └── save_credentials.py   # deprecated
│           ├── chutes-sign-in/                # [BETA] Build on Chutes
│           │   ├── SKILL.md
│           │   ├── references/ (oauth-flow, idp-endpoints, scope-cookbook, frameworks/)
│           │   └── scripts/ (register_oauth_app, install_siwc, verify_siwc, rotate_secret)
│           ├── chutes-deploy/                 # [BETA] Run agents with Chutes
│           │   ├── SKILL.md
│           │   ├── references/ (vllm-recipe, diffusion-recipe, teeify, rolling-updates)
│           │   └── scripts/ (deploy_vllm, deploy_diffusion, build_image, deploy_custom, teeify_chute, alias_deploy)
│           ├── chutes-mcp-portability/        # [BETA] Run agents with Chutes
│           │   ├── SKILL.md
│           │   ├── references/ (mcp-tool-map, cursor-setup, cline-setup, aider-setup, openrouter-style)
│           │   ├── mcp-server/ (server.py, pyproject.toml)
│           │   └── scripts/generate_agent_config.py
│           ├── chutes-routing/                # verified live
│           ├── chutes-usage-and-billing/      # verified live (read-only)
│           ├── chutes-platform-ops/           # mixed; token scripts BETA
│           ├── chutes-tee/                    # shape-valid attestation
│           └── chutes-agent-registration/     # [BETA]
├── other-agents/
│   ├── hermes/
│   │   ├── README.md
│   │   ├── config-examples/
│   │   └── skills/                            # symmetric mirror of the Claude tree
│   │       ├── chutes-ai/
│   │       ├── chutes-sign-in/                # [BETA: dev-server verification]
│   │       ├── chutes-routing/                # verified
│   │       ├── chutes-usage-and-billing/      # verified read-only
│   │       ├── chutes-platform-ops/           # mixed; token scripts BETA
│   │       ├── chutes-deploy/                 # [BETA: deploy writes]
│   │       ├── chutes-mcp-portability/        # read tools verified; writes BETA
│   │       ├── chutes-agent-registration/     # [BETA]
│   │       └── chutes-tee/                    # shape-valid attestation
│   ├── openclaw/                            # OpenClaw gateway integration
│   │   ├── README.md
│   │   └── config-examples/                 # openclaw.json, openclaw-routing.json
│   ├── system-prompt/
│   │   └── chutes-agent-prompt.md
│   └── openai-compatible/
│       └── README.md
├── docs/
│   ├── endpoint-guide.md                    # ⭐ universal one-page endpoint guide
│   ├── api-reference.md
│   ├── known-models.md
│   ├── hermes-chutes-toolkit-guide.md
│   ├── roadmap.md
│   ├── hermes-integration-spec.md
│   ├── chutes-maxi-proposal.md                # Hermes-generated proposal
│   ├── credential-store.md
│   ├── save-credentials-deprecation.md
│   └── llms-txt-review.md
├── evals/ (evals.json, README.md)
├── scripts/run_evals.py
├── tests/ (test_manage_credentials.py, test_run_evals.py)
├── LICENSE
└── README.md
```

---

## Chutes.ai links

| Resource | URL |
|----------|-----|
| Dashboard | https://chutes.ai/app |
| Documentation | https://chutes.ai/docs |
| API Swagger UI | https://api.chutes.ai/docs |
| OpenAPI spec | https://api.chutes.ai/openapi.json |
| Models (JSON, public) | https://llm.chutes.ai/v1/models |
| Agent-facing docs (llms.txt) | https://chutes.ai/llms.txt |
| Plugin manifest | https://chutes.ai/.well-known/ai-plugin.json |
| Public GPU/TAO pricing (JSON) | https://api.chutes.ai/pricing |
| Sign in with Chutes (upstream) | https://github.com/chutesai/Sign-in-with-Chutes |
| GitHub (SDK, PyPI `chutes` 0.6.9 stable) | https://github.com/chutesai/chutes |
| Vercel AI SDK provider | https://www.npmjs.com/package/@chutes-ai/ai-sdk-provider |

Model snapshot automation:

- `scripts/update_chutes_models.py` fetches `https://llm.chutes.ai/v1/models` with no auth headers.
- `.github/workflows/refresh-chutes-models.yml` runs it once per day and on manual dispatch.
- Generated outputs: `data/chutes-models.json`, `docs/known-models.md`, and `plugins/chutes-ai/skills/chutes-ai/references/known-models.md`.

## Contributing

PRs welcome. The shared canon lives in `docs/`; update there and changes benefit every platform. Wave-1 skills live in `plugins/chutes-ai/skills/`; Hermes mirrors live in `other-agents/hermes/skills/`. Scripts are single-sourced in the Claude plugin tree.

Eval tooling:
- `evals/evals.json`
- `evals/README.md`
- `scripts/run_evals.py`

Useful planning docs:
- `docs/roadmap.md`
- `docs/hermes-integration-spec.md`
- `docs/chutes-maxi-proposal.md`
- `docs/credential-store.md`

## License

MIT
