# Page draft: `chutes.ai/agents/connect` — "Connect your agent"

> Status: draft copy, ready for design. Each recipe is condensed from a live-maintained guide in [chutes-agent-toolkit](https://github.com/Veightor/chutes-agent-toolkit); deep links go there so this page stays short. Designed as a tabbed/accordion page, one client per tab.

---

## Intro

# Two lines. Any client.

Everything below boils down to the same two settings:

| Setting | Value |
|---|---|
| Base URL | `https://llm.chutes.ai/v1` |
| API key | your `cpk_...` key, sent as `Authorization: Bearer` |

Standard OpenAI SDKs send Bearer by default, so most tools need zero auth configuration beyond pasting the key. Pick your client:

---

## Tab: Claude Code ⭐ (deepest integration)

Claude gets the full treatment: a 9-skill plugin suite, OS-keychain credential storage, and an MCP server. Claude can onboard you to Chutes end to end, including creating the account.

**Install (two commands):**

```
/plugin marketplace add Veightor/chutes-agent-toolkit
/plugin install chutes-ai@chutes-agent-toolkit
```

**What Claude can now do, by asking in plain English:**

| Say this | Claude uses |
|---|---|
| "Set me up with a Chutes account and API key" | `chutes-ai`, which registers, creates the key, stores it in your OS keychain (never pasted into chat) |
| "Which Chutes model for tool-calling under $1/M?" | live `/v1/models` + the model picker logic |
| "Build me a failover pool of the 3 cheapest vision models" | `chutes-routing`, which emits the routing string or saves an alias |
| "Prove my model runs in a TEE" | `chutes-tee`, which fetches and parses real TDX/GPU attestation evidence |
| "How much did I spend this week and am I near my quota?" | `chutes-usage-and-billing` |
| "Add Sign in with Chutes to my Next.js app" | `chutes-sign-in` [BETA] |

**Credentials are keychain-backed.** On first use Claude runs `manage_credentials.py check`; if a profile exists it reads the key silently, so raw secrets never appear in the transcript. Works across sessions and projects.

**Claude Desktop / MCP:** prefer tools over skills? Install the stdio MCP server (same repo):

```bash
uv tool install chutes-mcp-server \
  --from plugins/chutes-ai/skills/chutes-mcp-portability/mcp-server
```

**Make any project Chutes-native:** drop this into the project's `CLAUDE.md` so every session knows the rules without the plugin:

```markdown
## Chutes inference
- Base URL `https://llm.chutes.ai/v1` (OpenAI-compatible), auth `Authorization: Bearer $CHUTES_API_KEY`.
- Never send `X-API-Key`; it is silently ignored on inference.
- Never hardcode model IDs: discover via `GET https://llm.chutes.ai/v1/models` (public) and
  check `supported_features` / `pricing` before choosing.
- For resilience pass a pool: `model="<id1>,<id2>,<id3>"` (append `:latency` or `:throughput`).
```

[Full guide →](https://github.com/Veightor/chutes-agent-toolkit#install-for-claude-code--cowork)

## Tab: Cursor / Cline / Aider

Generate a drop-in config for any of them:

```bash
python plugins/chutes-ai/skills/chutes-mcp-portability/scripts/generate_agent_config.py \
  --target cursor,cline,aider
```

Or by hand, e.g. Aider:

```bash
export OPENAI_API_BASE=https://llm.chutes.ai/v1
export OPENAI_API_KEY=$CHUTES_API_KEY
aider --model openai/deepseek-ai/DeepSeek-V3.2-TEE
```

[Per-client references →](https://github.com/Veightor/chutes-agent-toolkit/tree/main/plugins/chutes-ai/skills/chutes-mcp-portability/references)

## Tab: Hermes

Named OpenAI-compatible provider in `~/.hermes/config.yaml`:

```yaml
providers:
  chutes:
    base_url: https://llm.chutes.ai/v1
    api_key_env: CHUTES_API_KEY
    models:
      - deepseek-ai/DeepSeek-V3.2-TEE
```

A full Hermes skill mirror (onboarding, routing, billing, TEE) ships in the toolkit.
[Hermes guide + config examples →](https://github.com/Veightor/chutes-agent-toolkit/tree/main/other-agents/hermes)

## Tab: OpenClaw

OpenAI-compatible provider in `openclaw.json` (JSON5):

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

[OpenClaw guide + routing/vision examples →](https://github.com/Veightor/chutes-agent-toolkit/tree/main/other-agents/openclaw)

## Tab: LangChain / LiteLLM / raw SDK

```python
# LangChain
from langchain_openai import ChatOpenAI
llm = ChatOpenAI(base_url="https://llm.chutes.ai/v1",
                 api_key=os.environ["CHUTES_API_KEY"],
                 model="deepseek-ai/DeepSeek-V3.2-TEE")

# LiteLLM
import litellm
litellm.completion(model="chutes_ai/deepseek-ai/DeepSeek-V3.2-TEE",
                   api_key=os.environ["CHUTES_API_KEY"],
                   messages=[...])
```

## Tab: Vercel AI SDK

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

## Tab: MCP (Claude Desktop & any MCP client)

The toolkit ships a stdio MCP server exposing Chutes management + inference as tools:

```bash
uv tool install chutes-mcp-server \
  --from plugins/chutes-ai/skills/chutes-mcp-portability/mcp-server
```

[MCP tool map →](https://github.com/Veightor/chutes-agent-toolkit/blob/main/plugins/chutes-ai/skills/chutes-mcp-portability/references/mcp-tool-map.md)

## Tab: Any other agent (system prompt)

No plugin system? Paste the [Chutes system-prompt block](https://github.com/Veightor/chutes-agent-toolkit/blob/main/other-agents/system-prompt/chutes-agent-prompt.md) into your agent's instructions. It teaches the endpoints, auth rule, and discovery flow in ~1 page.

---

## Footer strip

Stuck? The [endpoint guide](https://github.com/Veightor/chutes-agent-toolkit/blob/main/docs/endpoint-guide.md) covers errors and gotchas, including the #1 trap: sending `X-API-Key` instead of `Authorization: Bearer` (it's silently ignored and you'll hit anonymous rate limits).

---

## Build notes (not page copy)

- Tabs ordered by observed demand: Claude → Cursor/Cline/Aider → Hermes → OpenClaw → frameworks → MCP/system-prompt. Reorder freely from analytics.
- Model IDs in snippets churn with the catalog. Either render the example ID from `/v1/models` at build time or pin a redirector alias the platform commits to keeping.
- The Hermes YAML shape (`providers:`) matches Hermes v0.16.0; the toolkit tracks this; re-check there before shipping changes.
