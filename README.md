# Chutes Agent Toolkit

Give any AI agent access to [Chutes.ai](https://chutes.ai) — decentralized serverless inference for 40+ open-source AI models (DeepSeek, Llama, Qwen, GLM, Mistral, and more), powered by Bittensor.

This repo is both a **Claude plugin marketplace** and a **multi-agent toolkit**. Install it in one command for Claude, or grab the system prompt for any other agent.

It is also the staging ground for a Hermes integration path: first via named custom-provider docs and skills, then via a future first-class Chutes provider implementation in a Hermes fork/PR.

## Install for Claude (Code / Cowork)

### Option 1: Plugin Marketplace (recommended)

Add this repo as a marketplace, then install the plugin:

```
/plugin marketplace add YOUR_ORG/chutes-agent-toolkit
/plugin install chutes-ai@chutes-agent-toolkit
```

That's it. Claude now has full Chutes.ai capabilities. Try asking:

- *"Set me up with a Chutes account and API key"*
- *"What open-source models are available on Chutes?"*
- *"Set up model routing with TEE models for lowest latency"*
- *"Show me how to call DeepSeek from Python using Chutes"*

### Option 2: Direct Skill Copy

If you prefer not to use the marketplace system, copy the skill directly:

```bash
cp -r plugins/chutes-ai/skills/chutes-ai ~/.claude/skills/chutes-ai
```

## Install for Other Agents

### Any LLM Agent (GPT, Gemini, Llama, etc.)

Copy the contents of [`other-agents/system-prompt/chutes-agent-prompt.md`](other-agents/system-prompt/chutes-agent-prompt.md) into your agent's system prompt. It's a single self-contained file with all the API details, code examples, and instructions.

### Hermes

Hermes works with Chutes today via named custom-provider configuration. See:
- [`other-agents/hermes/README.md`](other-agents/hermes/README.md)
- [`other-agents/hermes/config-examples/`](other-agents/hermes/config-examples/)

### LangChain / LiteLLM / Vercel AI SDK / AutoGPT

Chutes is OpenAI-compatible — change the base URL and you're done. See [`other-agents/openai-compatible/README.md`](other-agents/openai-compatible/README.md) for framework-specific setup.

Quick version:

```python
from openai import OpenAI

client = OpenAI(
    base_url="https://llm.chutes.ai/v1",
    api_key="cpk_..."
)
```

Chutes also publishes standard machine-readable interfaces for tool-based frameworks:

- **Plugin manifest**: `https://chutes.ai/.well-known/ai-plugin.json`
- **OpenAPI spec**: `https://api.chutes.ai/openapi.json`

## What Agents Can Do

- **Create accounts** — register on Chutes.ai with proper credential handling and backup
- **Manage API keys** — create, list, and delete `cpk_` prefixed keys
- **Secure credential store** — save keys to the OS keychain and read them back in future sessions
- **Discover models** — browse 40+ models with real-time pricing, TTFT, and TPS data
- **Make inference calls** — OpenAI-compatible API (Python, Node, cURL, any SDK)
- **Model routing** — failover, latency-optimized, or throughput-optimized multi-model pools
- **Billing** — top up via crypto ($TAO/Bittensor) or Stripe (25+ payment methods)
- **Usage tracking** — quotas, invocation stats, per-model costs
- **TEE models** — hardware-isolated inference via Intel TDX for privacy-sensitive workloads

## Secure Credential Store

This toolkit includes `manage_credentials.py` — a secure credential manager that stores API keys, fingerprints, and OAuth secrets in the **OS keychain** rather than plaintext files. Credentials persist across sessions and projects, so once saved, agents can read them back automatically in future conversations.

### Security model

| Data | Storage | Protection |
|------|---------|------------|
| `api_key` (`cpk_...`) | OS keychain | Encrypted at rest, per-app access control |
| `fingerprint` (32-char master credential) | OS keychain | Encrypted at rest, per-app access control |
| `client_id` / `client_secret` (OAuth apps) | OS keychain | Encrypted at rest, per-app access control |
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

# Manage multiple profiles (default, production, research, etc.)
python manage_credentials.py set-profile --profile production --api-key cpk_prod...
python manage_credentials.py get --profile production --field api_key
python manage_credentials.py list-profiles

# Save OAuth app credentials
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

| Variable | Field |
|----------|-------|
| `CHUTES_API_KEY` | `api_key` |
| `CHUTES_FINGERPRINT` | `fingerprint` |
| `CHUTES_CLIENT_ID` | `client_id` |
| `CHUTES_CLIENT_SECRET` | `client_secret` |
| `CHUTES_PROFILE` | active profile name |

### Agent usage pattern

When the Chutes skill is invoked in a new session, it first runs `manage_credentials.py check` to see if credentials already exist. If so, it reads the API key silently for use in API calls — never pasting raw secrets into the conversation. If not, it walks the user through account creation and saves credentials immediately after.

> **Note on the deprecated `save_credentials.py`**: The original `save_credentials.py` script wrote credentials to a plaintext backup file. It is now deprecated and emits a warning — use `manage_credentials.py` for all new credential storage.

## Repo Structure

```
chutes-agent-toolkit/
├── plugins/
│   └── chutes-ai/
│       ├── .claude-plugin/
│       │   └── plugin.json
│       └── skills/
│           └── chutes-ai/
│               ├── SKILL.md
│               ├── references/
│               │   ├── api-reference.md
│               │   └── known-models.md
│               └── scripts/
│                   ├── manage_credentials.py
│                   └── save_credentials.py
├── other-agents/
│   ├── hermes/
│   │   ├── README.md
│   │   ├── config-examples/
│   │   └── skills/
│   │       └── chutes-ai/
│   │           └── SKILL.md
│   ├── system-prompt/
│   │   └── chutes-agent-prompt.md
│   └── openai-compatible/
│       └── README.md
├── docs/
│   ├── api-reference.md
│   ├── known-models.md
│   ├── roadmap.md
│   ├── hermes-integration-spec.md
│   ├── credential-store.md
│   ├── save-credentials-deprecation.md
│   └── llms-txt-review.md
├── evals/
│   ├── evals.json
│   └── README.md
├── scripts/
│   └── run_evals.py
├── tests/
│   ├── test_manage_credentials.py
│   └── test_run_evals.py
├── LICENSE
└── README.md
```

## Chutes.ai Links

| Resource | URL |
|----------|-----|
| Dashboard | https://chutes.ai/app |
| Documentation | https://chutes.ai/docs |
| API Swagger UI | https://api.chutes.ai/docs |
| Models (JSON) | https://llm.chutes.ai/v1/models |
| GitHub (SDK) | https://github.com/chutesai/chutes |

## Contributing

PRs welcome! The shared docs live in `docs/` — update there and changes benefit all platforms. The Claude skill lives in `plugins/chutes-ai/skills/chutes-ai/SKILL.md`.

Eval tooling:
- `evals/evals.json`
- `evals/README.md`
- `scripts/run_evals.py`

Useful planning docs in this repo:
- `docs/roadmap.md`
- `docs/pre-hermes-phase2-checklist.md`
- `docs/hermes-integration-spec.md`
- `docs/llms-txt-review.md`
- `docs/credential-store.md`
- `docs/save-credentials-deprecation.md`

## License

MIT
