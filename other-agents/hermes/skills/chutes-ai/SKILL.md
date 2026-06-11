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

Use a `cpk_...` API key. Store it as `CHUTES_API_KEY` in `~/.hermes/.env` or in this repo's keychain-backed credential manager; never paste the raw key into config examples or chat.

Chutes auth was re-verified in the shared Chutes skills on 2026-06-11: use standard bearer authorization semantics (`Authorization: Bearer` plus the `cpk_...` value) for configured providers. `GET /v1/models` is public and should not be used as proof that a specific auth header works. Older April notes about `X-API-Key` are superseded for Hermes-facing setup.

## Hermes setup pattern

Typical Hermes config:

```yaml
providers:
  chutes:
    name: Chutes
    base_url: https://llm.chutes.ai/v1
    key_env: CHUTES_API_KEY
    transport: chat_completions
    default_model: default:latency
    discover_models: true
    models:
      default: {}
      "default:latency": {}
      "default:throughput": {}

model:
  provider: custom:chutes
  default: default:latency
```

Legacy Hermes configs may use `custom_providers:` with equivalent `name`, `base_url`, `key_env`, `api_mode`, and `model` fields.

Optional research profile:

```yaml
providers:
  chutes-research:
    name: Chutes Research Opt-In
    base_url: https://research-data-opt-in-proxy.chutes.ai/v1
    key_env: CHUTES_API_KEY
    transport: chat_completions
    default_model: default:latency
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

## Four product lanes — sibling skills

This skill is the Hermes-facing **hub**. For deeper capabilities, hand off to sibling skills in `other-agents/hermes/skills/`:

| Lane | Skill | Status |
|---|---|---|
| **Build on Chutes** | `chutes-sign-in` — Sign in with Chutes (OAuth + PKCE), OAuth app CRUD, client secret rotation | **BETA for dev-server verification** |
| **Operate on Chutes** | `chutes-routing` — intent-based model pools, routing strings, alias audits | VERIFIED |
| **Operate on Chutes** | `chutes-usage-and-billing` — read-only spend, quotas, discounts, exports | VERIFIED |
| **Operate on Chutes** | `chutes-platform-ops` — OAuth fleet and alias ops | MIXED; token scripts BETA |
| **Run agents with Chutes** | `chutes-deploy` — vLLM / diffusion / custom CDK deploy, teeify, rolling updates | **permanent BETA for deploy-side writes** |
| **Run agents with Chutes** | `chutes-mcp-portability` — Chutes MCP server + drop-in configs for Hermes / Cursor / Cline / Aider | READ TOOLS VERIFIED; write tools BETA |
| **Run agents with Chutes** | `chutes-agent-registration` — Bittensor-backed agent registration prep | **BETA** |
| **Use/Verify Chutes** | `chutes-tee` — evidence fetch + TDX/GPU attestation parsing | SHAPE-VALID |

These Hermes skills are thin entry points. Shared scripts and deep references stay single-sourced under `plugins/chutes-ai/skills/`.

## Repo references

For fuller docs, see:
- `docs/credential-store.md`
- `docs/hermes-integration-spec.md`
- `docs/sign-in-with-chutes.md`
- `docs/model-aliases.md`
- `docs/llms-txt-review.md`
- `other-agents/hermes/README.md`
- `other-agents/hermes/config-examples/`
- `plugins/chutes-ai/skills/chutes-ai/references/model-aliases.md`
