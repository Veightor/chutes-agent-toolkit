---
name: chutes-mcp-portability
description: "[BETA] Make Chutes.ai available to Hermes and any other MCP or OpenAI-compatible agent. Installs the Chutes MCP server (stdio), writes drop-in configs for Cursor / Cline / Aider / Hermes custom-provider / system-prompt agents, and runs a health check. Triggers on: MCP chutes, chutes MCP server, hermes chutes provider, cursor chutes, cline chutes, aider chutes, openai-compatible chutes, drop-in chutes config."
version: 0.1.0
author: Chutes Agent Toolkit
license: MIT
metadata:
  hermes:
    tags: [chutes, mcp, portability, openai-compatible, hermes, beta]
    status: beta
---

# Chutes MCP + Portability for Hermes **[BETA]**

> **Status: BETA** — mirror of the Claude-plugin `chutes-mcp-portability` skill. BETA until a live MCP health check (`chutes_list_models` over stdio against a real `cpk_`) has been executed and recorded. Write / deploy tools stay BETA permanently under the deploy-features policy.

## When to use this skill

A Hermes user wants to:

- Make Chutes available to a non-Hermes client they also use (Cursor, Cline, Aider, Claude Desktop).
- Set up Hermes itself as an MCP client that talks to the Chutes MCP server.
- Regenerate `other-agents/hermes/config-examples/chutes-*.yaml` from the current repo shape.
- Write a paste-able system prompt block that tells a generic agent how to call Chutes.

## Walkthrough (Hermes-facing)

Full walkthrough lives at `plugins/chutes-ai/skills/chutes-mcp-portability/`. Hermes users run:

```bash
# Install the MCP server
uv tool install chutes-mcp-server \
  --from plugins/chutes-ai/skills/chutes-mcp-portability/mcp-server

# Generate configs for the targets you care about
python plugins/chutes-ai/skills/chutes-mcp-portability/scripts/generate_agent_config.py \
  --target hermes,aider,system-prompt

# Health check
chutes-mcp-server --self-check
```

For Hermes specifically, the `--target hermes` path regenerates `other-agents/hermes/chutes-provider.yml` from a template that stays in sync with whatever the current Chutes inference API shape is. Run it again whenever this repo is updated.

## MCP tool surface

See `plugins/chutes-ai/skills/chutes-mcp-portability/references/mcp-tool-map.md` for the full list. Summary:

- **Read tools** — `chutes_list_models`, `chutes_list_chutes`, `chutes_list_aliases`, `chutes_get_usage`, `chutes_get_quota`, `chutes_get_discounts`, `chutes_get_evidence`, `chutes_oauth_introspect`, `chutes_list_api_keys`, `chutes_chat_complete`.
- **Write tools (permanent BETA)** — `chutes_deploy_vllm`, `chutes_deploy_diffusion`, `chutes_teeify`, `chutes_set_alias`, `chutes_delete_alias`, `chutes_create_api_key`. Each prepends `[BETA] ` to its tool description so MCP clients display the label.

## Deep references

- `plugins/chutes-ai/skills/chutes-mcp-portability/SKILL.md`
- `plugins/chutes-ai/skills/chutes-mcp-portability/references/mcp-tool-map.md`
- `plugins/chutes-ai/skills/chutes-mcp-portability/references/{cursor,cline,aider,openrouter-style}.md`
- `other-agents/hermes/README.md`
- `other-agents/hermes/config-examples/*.yaml`

## Safety rules

- Never bake a raw `cpk_` into a generated config file. Use `${CHUTES_API_KEY}` references wherever the target client supports them.
- MCP tools never return `cpk_` through tool results.
- Write tools keep their `[BETA] ` prefix until the deploy-features policy changes.
- A health check is not optional — skill completion without it stays BETA.

## Related Hermes skills

- `chutes-ai` (Hermes hub) — API key + base provider setup.
- `chutes-deploy` **[BETA]** — the write MCP tools are equivalents of the `chutes-deploy` scripts, intended for programmatic use from another agent instead of an interactive walkthrough.
- `chutes-sign-in` **[BETA]** — `chutes_oauth_introspect` is the MCP-exposed form of the SIWC verify step.
