# Chutes Agent Toolkit

Give any AI agent access to [Chutes.ai](https://chutes.ai) — decentralized serverless inference for 40+ open-source AI models (DeepSeek, Llama, Qwen, GLM, Mistral, and more), powered by Bittensor.

This repo is both a **Claude plugin marketplace** and a **multi-agent toolkit**. The same skills, scripts, and docs work for Claude, Hermes, and any generic OpenAI-compatible client.

It is also the staging ground for deeper Hermes integration: custom-provider configuration + symmetric skill tree today, first-class provider PR later.

---

## The four product lanes

The toolkit is organized around four product lanes, each with one or more focused skills:

| Lane | What it covers | Skills |
|---|---|---|
| **Use Chutes** | Account, API keys, models, OpenAI-compatible inference, basic routing, TEE model selection. | `chutes-ai` (hub), `chutes-routing`, `chutes-tee` |
| **Build on Chutes** | "Sign in with Chutes" — OAuth 2.0 + OIDC + PKCE. Register apps, vendor the upstream Next.js package, manage scopes, rotate client secrets safely. | `chutes-sign-in` |
| **Operate on Chutes** | Spend + quota dashboards, fleet-scale OAuth app audit, bulk secret rotation, alias governance, TEE attestation verification. | `chutes-usage-and-billing`, `chutes-platform-ops`, `chutes-tee` |
| **Run agents with Chutes** | Chute deploy (vLLM / diffusion / teeify), MCP server + drop-in configs for Cursor / Cline / Aider / Hermes / Claude Desktop, autonomous agent registration. | `chutes-deploy` **[BETA]**, `chutes-mcp-portability`, `chutes-agent-registration` **[BETA]** |

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

### Still BETA

- **`chutes-deploy`** — permanent BETA under the deploy-features policy. Wave-2 live verification found that the easy-deploy lanes (`POST /chutes/vllm`, `POST /chutes/diffusion`) are currently gated server-side with HTTP 403 `{"detail":"Easy deployment is currently disabled!"}` on at least some account classes. Scripts now surface a clear fall-back hint; `--revision` branch→SHA auto-resolve is in place (wave-1 passed `main` which Chutes rejected).
- **`chutes-agent-registration`** — dry-run verified. Stays BETA because creating a real Bittensor-backed agent account has on-chain implications that are the wrong shape for automated verification. Graduates on the first intentional human-initiated agent registration.
- **`chutes-sign-in:verify_siwc.py`** — steps 1-3 (files / env / keychain) verified live; step 4 (dev server `/api/auth/chutes/session` hit) requires `npm install` + `npm run dev` which is out of scope for automated verification.
- **`chutes-platform-ops:introspect_token.py` / `revoke_token.py`** — both need a real OAuth access token from a completed SIWC browser flow. Graduate on the first live run against a real token.
- **`chutes-mcp-portability` write tools** — `chutes_deploy_vllm`, `chutes_deploy_diffusion`, `chutes_teeify`, `chutes_set_alias`, `chutes_delete_alias`, `chutes_create_api_key` stay permanent BETA under the deploy-features policy. `chutes_set_alias` / `chutes_delete_alias` were functionally exercised in wave 2 (and the wave-1 schema bug was fixed), but deploy-side writes keep the label.
- **`chutes-mcp-portability` three unexercised read tools** — `chutes_chat_complete` (paid), `chutes_get_evidence` (wave-2 `chutes-tee` skill exercises the underlying endpoint but not through the MCP path), `chutes_oauth_introspect` (needs a live OAuth token).

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
- *"Set up TEE-only routing for lowest latency"* → `chutes-ai` hub (deep recipes are wave-2 `chutes-routing`)

### Option 2: Direct Skill Copy

If you prefer not to use the marketplace system, copy the skills directly:

```bash
cp -r plugins/chutes-ai/skills/* ~/.claude/skills/
```

## Install for Other Agents

### Hermes

Hermes works with Chutes today via named custom-provider configuration, and now has a symmetric skill tree at `other-agents/hermes/skills/` mirroring the Claude tree:

- `other-agents/hermes/skills/chutes-ai/` — hub
- `other-agents/hermes/skills/chutes-sign-in/` **[BETA]**
- `other-agents/hermes/skills/chutes-deploy/` **[BETA]**
- `other-agents/hermes/skills/chutes-mcp-portability/` **[BETA]**

See also:
- [`other-agents/hermes/README.md`](other-agents/hermes/README.md)
- [`other-agents/hermes/config-examples/`](other-agents/hermes/config-examples/)

Scripts live in the Claude plugin tree; Hermes users invoke them from the repo root. There is one implementation, two skill trees.

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

Quick inference snippet (verified live auth shape):

```python
import requests

response = requests.get(
    "https://llm.chutes.ai/v1/models",
    headers={"X-API-Key": "cpk_..."},
    timeout=30,
)
response.raise_for_status()
```

Note: live tests on 2026-04-15 showed `X-API-Key: cpk_...` working for inference, while `Authorization: Bearer cpk_...` returned 401. Treat generic OpenAI-SDK compatibility as conditional until the inference surface accepts Bearer `cpk_...`.

Standard machine-readable interfaces:

- **Plugin manifest**: `https://chutes.ai/.well-known/ai-plugin.json`
- **OpenAPI spec**: `https://api.chutes.ai/openapi.json`

---

## What agents can do

- **Create accounts** — register on Chutes.ai with proper credential handling and backup
- **Manage API keys** — create, list, and delete `cpk_` prefixed keys
- **Secure credential store** — save keys to the OS keychain and read them back in future sessions
- **Discover models** — browse 40+ models with real-time pricing, TTFT, and TPS data
- **Make inference calls** — OpenAI-like request/response API; live auth currently prefers `X-API-Key` on the inference surface
- **Model routing** — failover, latency-optimized, or throughput-optimized multi-model pools
- **Model aliases** — stable semantic handles like `interactive-fast` that survive model churn
- **Sign in with Chutes** **[BETA]** — turn any Next.js App Router app into an OAuth relying party
- **Deploy chutes** **[BETA]** — vLLM / diffusion / custom CDK deploy, teeify affine chutes, stream build logs
- **MCP portability** **[BETA]** — drive Chutes from Cursor / Cline / Aider / Hermes / Claude Desktop
- **Billing** — top up via crypto ($TAO/Bittensor) or Stripe (25+ payment methods)
- **Usage tracking** — quotas, invocation stats, per-model costs
- **TEE models** — hardware-isolated inference via Intel TDX for privacy-sensitive workloads

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
│           ├── chutes-routing/                # [BETA] wave-2 stub
│           ├── chutes-usage-and-billing/      # [BETA] wave-2 stub
│           ├── chutes-platform-ops/           # [BETA] wave-2 stub
│           └── chutes-agent-registration/     # [BETA] wave-2 stub
├── other-agents/
│   ├── hermes/
│   │   ├── README.md
│   │   ├── config-examples/
│   │   └── skills/                            # symmetric mirror of the Claude tree
│   │       ├── chutes-ai/
│   │       ├── chutes-sign-in/                # [BETA]
│   │       ├── chutes-deploy/                 # [BETA]
│   │       └── chutes-mcp-portability/        # [BETA]
│   ├── system-prompt/
│   │   └── chutes-agent-prompt.md
│   └── openai-compatible/
│       └── README.md
├── docs/
│   ├── api-reference.md
│   ├── known-models.md
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
| Models (JSON) | https://llm.chutes.ai/v1/models |
| Sign in with Chutes (upstream) | https://github.com/chutesai/Sign-in-with-Chutes |
| GitHub (SDK) | https://github.com/chutesai/chutes |

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
