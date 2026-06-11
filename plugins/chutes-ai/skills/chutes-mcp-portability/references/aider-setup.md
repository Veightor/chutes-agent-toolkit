# Chutes in Aider (OpenAI-like payloads, no MCP) **[BETA]**

Aider does not speak MCP — it speaks the OpenAI HTTP API, sending `Authorization: Bearer $OPENAI_API_KEY`. Good news: the April 2026 auth mismatch is gone. Re-verified 2026-06-11, `Authorization: Bearer cpk_...` returns 200 on `GET llm.chutes.ai/v1/models`, and Bearer is now the platform-recommended header (per chutes.ai's own `ai-plugin.json` / `llms.txt`; official docs say `X-API-Key` is silently ignored on the inference surface). This setup stays **[BETA]** only because a paid `POST /chat/completions` round-trip through Aider has not been re-exercised (unverified as of 2026-06-11).

## Generate the config

```bash
python plugins/chutes-ai/skills/chutes-mcp-portability/scripts/generate_agent_config.py \
  --target aider --out ~
```

This writes `~/.aider.conf.yml`:

```yaml
openai-api-base: https://llm.chutes.ai/v1
openai-api-key: ${CHUTES_API_KEY}
model: deepseek-ai/DeepSeek-V3.2-TEE
edit-format: diff
```

If an `~/.aider.conf.yml` already exists, the script writes next to it and prints the diff — apply manually.

## Set the env var

```bash
export CHUTES_API_KEY=$(python plugins/chutes-ai/skills/chutes-ai/scripts/manage_credentials.py get --field api_key)
```

Put this in `~/.zshrc` or `~/.bashrc`.

## Pick a model

Aider caches capabilities per model. As of 2026-06-11 the Chutes catalog is 13 models, **all TEE** (`-TEE` suffix, `confidential_compute: true`) — older non-TEE ids like `deepseek-ai/DeepSeek-V3-0324` and `deepseek-ai/DeepSeek-R1` no longer exist on `/v1/models`. A few reasonable starting points:

| Intent | Model |
|---|---|
| Everyday editing | `deepseek-ai/DeepSeek-V3.2-TEE` |
| Coding/agentic flagship | `moonshotai/Kimi-K2.6-TEE` or `zai-org/GLM-5.1-TEE` |
| Budget coding workhorse | `MiniMaxAI/MiniMax-M2.5-TEE` |
| Cheap background | `Qwen/Qwen3-32B-TEE` (or `unsloth/Mistral-Nemo-Instruct-2407-TEE`, the cheapest) |
| Reasoning-heavy refactors | `Qwen/Qwen3-235B-A22B-Thinking-2507-TEE` |

You can also use routing strings as the model id:

```yaml
model: deepseek-ai/DeepSeek-V3.2-TEE,zai-org/GLM-5-TEE,Qwen/Qwen3-32B-TEE:latency
```

Aider will pass this through as the `model` parameter, and Chutes' router will rank the pool by TTFT per request.

## Verify

```bash
aider --version
aider --show-model-warnings <any-file>
```

The first line of Aider output should show the Chutes model id. A simple test edit confirms the round-trip.

## Troubleshooting

- **401 Unauthorized** — `CHUTES_API_KEY` is empty or wrong. Bearer `cpk_...` itself is accepted on the inference surface (re-verified 2026-06-11 on `/v1/models`), so a 401 now points at the key value, not the header.
- **"Unknown model"** — Aider has a hardcoded list of known models; if yours isn't on it, add `--no-verify-ssl` / `--no-model-check` and trust `/v1/models`.
- **Edits not applying** — `edit-format: diff` is the most forgiving format for Chutes models. `whole` is next. `udiff` is strict and sometimes misses.
