# Chutes as a Generic OpenAI-Like Endpoint **[BETA]**

For any tool that expects OpenAI-style request/response payloads, Chutes is close — but live auth currently differs from the standard OpenAI Bearer-token pattern.

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
OPENAI_API_KEY=cpk_...
```

Important: many OpenAI-style clients will send `Authorization: Bearer $OPENAI_API_KEY`. In live verification on 2026-04-15, Chutes inference accepted `X-API-Key: cpk_...` but returned 401 for `Authorization: Bearer cpk_...`. So this env pattern is best treated as experimental until Bearer `cpk_...` is accepted on the inference surface.

Source it in your shell:

```bash
set -a
source ~/tmp/chutes-env/chutes.env
set +a
export CHUTES_API_KEY=$(python plugins/chutes-ai/skills/chutes-ai/scripts/manage_credentials.py get --field api_key)
```

## Works with

- Raw HTTP clients where you control headers directly
- SDKs/wrappers only if they let you override the auth header to `X-API-Key`
- MCP clients via the `chutes-mcp-server` bridge (recommended)

## Caveats

- **OpenAI env vars alone are not sufficient in many clients today.** If the client hardcodes `Authorization: Bearer $OPENAI_API_KEY`, expect a 401 until Chutes accepts Bearer `cpk_...` on the inference surface.
- **Different engines accept different sampling params.** `temperature`, `top_p`, `top_k`, `max_tokens` are safe. `n > 1` is usually fine but test.
- **Tool calling works** on models whose `supported_features` includes `tools`. Not every model does.
- **Embeddings and TTS/STT endpoints** are not OpenAI-compatible on Chutes today; use the Chutes-native endpoints instead.

## Switching between OpenAI and Chutes cleanly

If a project needs to flip between real OpenAI and Chutes, prefer a thin wrapper that can change both the base URL and the auth header. If the client cannot send `X-API-Key` for Chutes mode, the switch is not truly drop-in yet.

```bash
# Chutes mode (only works if the client can send X-API-Key)
export OPENAI_API_BASE=https://llm.chutes.ai/v1
export OPENAI_API_KEY=cpk_...

# OpenAI mode
unset OPENAI_API_BASE
export OPENAI_API_KEY=sk-...
```

Most OpenAI SDKs default to `https://api.openai.com/v1` when `OPENAI_API_BASE` is unset.
