# Chutes as a Generic OpenAI-Like Endpoint **[BETA]**

For any tool that expects OpenAI-style request/response payloads, Chutes now matches the standard pattern: `Authorization: Bearer cpk_...` is the platform-recommended header (re-verified live 2026-06-11 on `GET /v1/models`, which is itself now public). The label stays **[BETA]** because a paid `POST /chat/completions` round-trip was not re-exercised (unverified as of 2026-06-11).

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

OpenAI-style clients send `Authorization: Bearer $OPENAI_API_KEY` — and that is exactly right for Chutes now. The April 2026 finding (Bearer → 401) is inverted: re-verified 2026-06-11, Bearer `cpk_...` returns 200 on `GET llm.chutes.ai/v1/models` and even on management GETs like `api.chutes.ai/users/me`. Official Chutes docs (`llms.txt`) say the old `X-API-Key` header is silently ignored on the inference surface — do not rely on it.

Source it in your shell:

```bash
set -a
source ~/tmp/chutes-env/chutes.env
set +a
export CHUTES_API_KEY=$(python plugins/chutes-ai/skills/chutes-ai/scripts/manage_credentials.py get --field api_key)
```

## Works with

- Any OpenAI SDK or wrapper that lets you set the base URL — the standard Bearer header is the right one now
- Raw HTTP clients where you control headers directly
- MCP clients via the `chutes-mcp-server` bridge (for management tools too)

## Caveats

- **Completions auth not re-exercised.** Bearer `cpk_...` is verified on `GET /v1/models` (2026-06-11) and platform-recommended for everything; `POST /chat/completions` is a paid call and was not re-verified this pass (unverified as of 2026-06-11).
- **Different engines accept different sampling params.** `temperature`, `top_p`, `top_k`, `max_tokens` are safe. `n > 1` is usually fine but test.
- **Tool calling works** on models whose `supported_features` includes `tools`. Not every model does.
- **Embeddings and TTS/STT endpoints** are not OpenAI-compatible on Chutes today; use the Chutes-native endpoints instead.

## Switching between OpenAI and Chutes cleanly

If a project needs to flip between real OpenAI and Chutes, swapping the base URL and key is enough — both use standard Bearer auth.

```bash
# Chutes mode
export OPENAI_API_BASE=https://llm.chutes.ai/v1
export OPENAI_API_KEY=cpk_...

# OpenAI mode
unset OPENAI_API_BASE
export OPENAI_API_KEY=sk-...
```

Most OpenAI SDKs default to `https://api.openai.com/v1` when `OPENAI_API_BASE` is unset.
