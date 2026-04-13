---
name: chutes-ai
description: Use Chutes.ai from Hermes for model discovery, routing, account/API-key guidance, and OpenAI-compatible inference. Prefer the live models endpoint for current availability and capabilities.
version: 0.1.0
author: Chutes Agent Toolkit
license: MIT
metadata:
  hermes:
    tags: [chutes, inference, routing, tee, openai-compatible, hermes]
---

# Chutes.ai for Hermes

Use this skill when the user asks about:
- Chutes.ai setup or usage
- open-source model inference through Chutes
- model routing / failover / latency / throughput
- TEE / confidential compute on Chutes
- billing, balances, discounts, or quotas on Chutes
- using Chutes as a Hermes model backend

## Source of truth for live model metadata

When current model inventory, pricing, supported features, TTFT/TPS, or TEE status matter, use:

`https://llm.chutes.ai/v1/models`

Do not treat static model snapshots as authoritative.

## Base URLs

- Management API: `https://api.chutes.ai`
- Inference API: `https://llm.chutes.ai/v1`
- Research endpoint: `https://research-data-opt-in-proxy.chutes.ai/v1`

## Authentication

Use a `cpk_...` API key via:

`Authorization: Bearer <token>`

For Hermes, a common setup is a named custom provider configured with `CHUTES_API_KEY`.

## Hermes setup pattern

Typical Hermes config:

```yaml
custom_providers:
  - name: Chutes
    base_url: https://llm.chutes.ai/v1
    key_env: CHUTES_API_KEY
    api_mode: chat_completions
    model: default
```

Optional research profile:

```yaml
  - name: Chutes Research
    base_url: https://research-data-opt-in-proxy.chutes.ai/v1
    key_env: CHUTES_API_KEY
    api_mode: chat_completions
    model: default:latency
```

## Routing guidance

Chutes supports:
- `default`
- `default:latency`
- `default:throughput`
- inline routing strings like `modelA,modelB,modelC:latency`

Use:
- `default:latency` for interactive chat
- `default:throughput` for long generations or delegated/background work
- normal endpoint for private/sensitive prompts
- research endpoint only with explicit user consent

## TEE guidance

To identify TEE-backed models, use:
- `confidential_compute: true`

That field is authoritative. Do not rely solely on `-TEE` in the model name.

## Credential storage

Preferred secure storage script in this repo:
- `plugins/chutes-ai/skills/chutes-ai/scripts/manage_credentials.py`

Legacy plaintext backup script:
- `plugins/chutes-ai/skills/chutes-ai/scripts/save_credentials.py`
- legacy use only; prefer the secure credential manager

## Repo references

For fuller docs, see:
- `docs/credential-store.md`
- `docs/hermes-integration-spec.md`
- `docs/llms-txt-review.md`
- `other-agents/hermes/README.md`
- `other-agents/hermes/config-examples/`
