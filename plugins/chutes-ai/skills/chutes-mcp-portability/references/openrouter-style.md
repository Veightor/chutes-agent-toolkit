# Chutes as a Generic OpenAI-Compatible Endpoint **[BETA]**

For any tool that expects OpenAI-style env vars (`OPENAI_API_BASE` / `OPENAI_BASE_URL` / `OPENAI_API_KEY`), Chutes is a drop-in replacement.

## Generate the env block

```bash
python plugins/chutes-ai/skills/chutes-mcp-portability/scripts/generate_agent_config.py \
  --target openrouter --out ~/tmp/chutes-env
cat ~/tmp/chutes-env/chutes.env
```

The script writes:

```
OPENAI_API_BASE=https://llm.chutes.ai/v1
OPENAI_BASE_URL=https://llm.chutes.ai/v1
OPENAI_API_KEY=${CHUTES_API_KEY}
```

Source it in your shell:

```bash
set -a
source ~/tmp/chutes-env/chutes.env
set +a
export CHUTES_API_KEY=$(python plugins/chutes-ai/skills/chutes-ai/scripts/manage_credentials.py get --field api_key)
```

## Works with

- Raw `openai` / `@openai/openai-node` SDK
- LangChain with `ChatOpenAI`
- LlamaIndex
- Continue (VS Code)
- Any tool that follows "set `OPENAI_*` env vars"

## Caveats

- **Model identifiers are Chutes-specific.** Check `/v1/models` before picking an id.
- **Different engines accept different sampling params.** `temperature`, `top_p`, `top_k`, `max_tokens` are safe. `n > 1` is usually fine but test.
- **Tool calling works** on models whose `supported_features` includes `tools`. Not every model does.
- **Embeddings and TTS/STT endpoints** are not OpenAI-compatible on Chutes today; use the Chutes-native endpoints instead.

## Switching between OpenAI and Chutes cleanly

If a project needs to flip between real OpenAI and Chutes:

```bash
# Chutes mode
export OPENAI_API_BASE=https://llm.chutes.ai/v1
export OPENAI_API_KEY=$CHUTES_API_KEY

# OpenAI mode
unset OPENAI_API_BASE
export OPENAI_API_KEY=$REAL_OPENAI_KEY
```

Most OpenAI SDKs default to `https://api.openai.com/v1` when `OPENAI_API_BASE` is unset.
