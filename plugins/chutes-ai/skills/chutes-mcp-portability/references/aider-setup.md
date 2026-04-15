# Chutes in Aider (OpenAI-like payloads, no MCP) **[BETA]**

Aider does not speak MCP — it speaks the OpenAI HTTP API. That means the base URL shape fits, but live auth may not: verified 2026-04-15, Chutes inference accepted `X-API-Key: cpk_...` while `Authorization: Bearer cpk_...` returned 401. So treat direct Aider usage as experimental until Aider can send `X-API-Key` or Chutes accepts Bearer `cpk_...`.

## Generate the config

```bash
python plugins/chutes-ai/skills/chutes-mcp-portability/scripts/generate_agent_config.py \
  --target aider --out ~
```

This writes `~/.aider.conf.yml`:

```yaml
openai-api-base: https://llm.chutes.ai/v1
openai-api-key: ${CHUTES_API_KEY}
model: deepseek-ai/DeepSeek-V3-0324
edit-format: diff
```

If an `~/.aider.conf.yml` already exists, the script writes next to it and prints the diff — apply manually.

## Set the env var

```bash
export CHUTES_API_KEY=$(python plugins/chutes-ai/skills/chutes-ai/scripts/manage_credentials.py get --field api_key)
```

Put this in `~/.zshrc` or `~/.bashrc`.

## Pick a model

Aider caches capabilities per model. A few reasonable starting points on Chutes:

| Intent | Model |
|---|---|
| Everyday editing | `deepseek-ai/DeepSeek-V3-0324` |
| Cheap background | a small Qwen model (check `/v1/models`) |
| Reasoning-heavy refactors | `deepseek-ai/DeepSeek-R1` or similar |
| Privacy-sensitive | any model with `confidential_compute: true` |

You can also use routing strings as the model id:

```yaml
model: deepseek-ai/DeepSeek-V3-0324,zai-org/GLM-5-Turbo,Qwen/Qwen3-32B-TEE:latency
```

Aider will pass this through as the `model` parameter, and Chutes' router will rank the pool by TTFT per request.

## Verify

```bash
aider --version
aider --show-model-warnings <any-file>
```

The first line of Aider output should show the Chutes model id. A simple test edit confirms the round-trip.

## Troubleshooting

- **401 Unauthorized** — Aider is probably sending `Authorization: Bearer $CHUTES_API_KEY`. That is a known live mismatch today; prefer the MCP server path until Chutes accepts Bearer `cpk_...` or Aider can send `X-API-Key`.
- **"Unknown model"** — Aider has a hardcoded list of known models; if yours isn't on it, add `--no-verify-ssl` / `--no-model-check` and trust `/v1/models`.
- **Edits not applying** — `edit-format: diff` is the most forgiving format for Chutes models. `whole` is next. `udiff` is strict and sometimes misses.
