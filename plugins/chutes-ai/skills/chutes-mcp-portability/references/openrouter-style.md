# Chutes as a Generic OpenAI-Like Endpoint **[BETA]**

For any tool that expects OpenAI-style request/response payloads, Chutes now matches the standard pattern: `Authorization: Bearer cpk_...` is the platform-recommended header — live-verified 2026-06-11 on both `GET /v1/models` (itself now public) and a real paid `POST /chat/completions` (HTTP 200, completion returned). The label stays **[BETA]** only because the round-trip has not been exercised through an actual OpenAI-style client using these env blocks (the direct-curl path is verified).

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

OpenAI-style clients send `Authorization: Bearer $OPENAI_API_KEY` — and that is exactly right for Chutes now. The April 2026 finding (Bearer → 401) is inverted: re-verified 2026-06-11, Bearer `cpk_...` returns 200 on `GET llm.chutes.ai/v1/models`, on a real paid `POST llm.chutes.ai/v1/chat/completions`, and even on management GETs like `api.chutes.ai/users/me`. The old `X-API-Key` header is confirmed silently ignored on the inference surface (live 2026-06-11: a completion POST with it got the anonymous 429, byte-identical to no auth at all) — do not rely on it.

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

- **Completions auth is live-verified, client round-trips are not.** Bearer `cpk_...` returned a real completion on `POST /chat/completions` (verified 2026-06-11, direct curl); what remains unexercised is the same call made through each OpenAI-style client consuming these env blocks.
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
