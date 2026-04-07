# Chutes Agent Toolkit

Give any AI agent access to [Chutes.ai](https://chutes.ai) — decentralized serverless inference for 40+ open-source AI models (DeepSeek, Llama, Qwen, GLM, Mistral, and more), powered by Bittensor.

This repo is both a **Claude plugin marketplace** and a **multi-agent toolkit**. Install it in one command for Claude, or grab the system prompt for any other agent.

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
- **Discover models** — browse 40+ models with real-time pricing, TTFT, and TPS data
- **Make inference calls** — OpenAI-compatible API (Python, Node, cURL, any SDK)
- **Model routing** — failover, latency-optimized, or throughput-optimized multi-model pools
- **Billing** — top up via crypto ($TAO/Bittensor) or Stripe (25+ payment methods)
- **Usage tracking** — quotas, invocation stats, per-model costs
- **TEE models** — hardware-isolated inference via Intel TDX for privacy-sensitive workloads

## Repo Structure

```
chutes-agent-toolkit/
├── .claude-plugin/
│   └── marketplace.json              # Claude plugin marketplace definition
├── plugins/
│   └── chutes-ai/                    # The Claude plugin
│       ├── .claude-plugin/
│       │   └── plugin.json           # Plugin manifest (name, version, metadata)
│       └── skills/
│           └── chutes-ai/
│               ├── SKILL.md          # Main skill (full 6-step workflow)
│               ├── references/
│               │   ├── api-reference.md
│               │   └── known-models.md
│               └── scripts/
│                   └── save_credentials.py
├── other-agents/
│   ├── system-prompt/
│   │   └── chutes-agent-prompt.md    # Paste into any agent's system prompt
│   └── openai-compatible/
│       └── README.md                 # LangChain, LiteLLM, Vercel AI SDK, AutoGPT
├── docs/                             # Shared reference docs
│   ├── api-reference.md
│   ├── known-models.md
│   └── llms.txt
├── evals/
│   └── evals.json                    # Test cases
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

## License

MIT
