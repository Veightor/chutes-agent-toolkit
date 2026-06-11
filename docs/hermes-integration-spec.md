# Hermes Integration Spec for Chutes Agent Toolkit

This document defines the current Hermes-facing Chutes assets in this repo and the target state for cleaner Chutes support in Hermes.

## Current state checked against Hermes v0.16.0

As of Hermes Agent v0.16.0, the installed upstream provider registry does not expose a first-class `chutes` provider. Chutes works through:

1. Hermes named-provider configuration for OpenAI-compatible model backends (`providers:` preferred; `custom_providers:` legacy-compatible).
2. Hermes `mcp_servers` / `hermes mcp add` for tool-level Chutes access through the local stdio MCP server.
3. The Hermes skill mirror under `other-agents/hermes/skills/`, with shared scripts still single-sourced under `plugins/chutes-ai/skills/`.

Do not describe first-class Chutes provider support as upstream-shipped unless the target Hermes install actually shows it in `hermes model` / the provider registry.

## Goal

Make Chutes feel natural in Hermes while keeping this toolkit repo as the canonical source for Chutes-specific docs, skill content, examples, MCP tooling, and integration guidance.

## Principles

1. Chutes should work in Hermes immediately via named custom provider config and/or MCP.
2. A future first-class provider should be a narrow Hermes change; Chutes-specific operational docs stay here.
3. Live model inventory and metadata must come from:

`https://llm.chutes.ai/v1/models`

Static lists in this repo are convenience references only.

4. Hermes docs should distinguish model-provider setup from MCP/tool setup.

## Integration paths

1. **Custom provider YAML** — works today. See `other-agents/hermes/config-examples/`. Generated/refreshed by:

```bash
python plugins/chutes-ai/skills/chutes-mcp-portability/scripts/generate_agent_config.py --target hermes
```

2. **Hermes skill mirror** — `other-agents/hermes/skills/` has thin Hermes entry points for the full Chutes skill suite:
   - `chutes-ai`
   - `chutes-sign-in`
   - `chutes-routing`
   - `chutes-usage-and-billing`
   - `chutes-platform-ops`
   - `chutes-deploy`
   - `chutes-mcp-portability`
   - `chutes-agent-registration`
   - `chutes-tee`

3. **MCP server** — `chutes-mcp-server` (stdio, from `plugins/chutes-ai/skills/chutes-mcp-portability/mcp-server/`) gives any MCP-aware Hermes build tool-level access to Chutes without touching provider config. Use it alongside custom-provider YAML, not instead of it, when you want management/read tools.

4. **Local toolkit guide** — `docs/hermes-chutes-toolkit-guide.md` is the repo-owned handoff guide for beginners and agents. It includes install notes, env handling, live model discovery, one-key/many-model provider patterns, normal vs research endpoint separation, MCP setup, delegation examples, Windows notes, and maintainer verification commands.

## Layer 1: Works today in Hermes via custom provider

Recommended user-facing config pattern:

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

Legacy Hermes configs can use `custom_providers:` with equivalent `name`, `base_url`, `key_env`, `api_mode`, and `model` fields.

Recommended environment variable in `~/.hermes/.env`:

```bash
CHUTES_API_KEY=cpk_...
```

Optional research endpoint:

```yaml
providers:
  chutes-research:
    name: Chutes Research Opt-In
    base_url: https://research-data-opt-in-proxy.chutes.ai/v1
    key_env: CHUTES_API_KEY
    transport: chat_completions
    default_model: default:latency
```

Research endpoint caveat: prompts and responses may be recorded for research; use only with explicit user consent.

### Auth note

Chutes auth was re-verified in the shared Chutes skills on 2026-06-11. Use standard bearer authorization semantics (`Authorization: Bearer` plus the `cpk_...` value) for configured providers. `GET /v1/models` is public and should not be used as proof that a specific auth header works. Older April notes about `X-API-Key` are superseded for Hermes-facing setup.

## Layer 2: Works today in Hermes via MCP

Install the MCP server:

```bash
uv tool install chutes-mcp-server \
  --from plugins/chutes-ai/skills/chutes-mcp-portability/mcp-server
```

Register and test it in Hermes:

```bash
hermes mcp add chutes --command chutes-mcp-server --env CHUTES_API_KEY=${CHUTES_API_KEY}
hermes mcp test chutes
hermes mcp list
```

Run the server self-check too:

```bash
chutes-mcp-server --self-check
```

MCP read tools verified live 2026-04-13:
- `chutes_list_models`
- `chutes_get_quota`
- `chutes_list_aliases`
- `chutes_list_chutes`
- `chutes_get_usage`
- `chutes_get_discounts`
- `chutes_list_api_keys`

Unexercised read tools and all write/deploy tools retain BETA labels according to the deploy-features policy.

## Chutes-specific ergonomics to document

1. Model routing aliases:
- `default`
- `default:latency`
- `default:throughput`

2. Inline routing strings:
- `modelA,modelB,modelC`
- `modelA,modelB,modelC:latency`
- `modelA,modelB,modelC:throughput`

3. Privacy-sensitive routing:
- users should filter for `confidential_compute: true`
- canonical live discovery source is `https://llm.chutes.ai/v1/models`
- stronger claims require evidence inspection via `chutes-tee`

4. Research endpoint tradeoff:
- `https://research-data-opt-in-proxy.chutes.ai/v1`
- same API key, lower cost, but prompt/response data may be recorded for research

## Future native Hermes provider scope

Files likely to change in a Hermes fork:
- `hermes_cli/auth.py`
- `hermes_cli/models.py`
- `hermes_cli/main.py`
- `hermes_cli/config.py`
- `hermes_cli/runtime_provider.py`
- docs and tests relevant to provider selection and auth resolution

Minimum acceptable implementation:
1. Add Chutes to provider registry.
2. Wire `CHUTES_API_KEY`.
3. Set base URL and `chat_completions` API mode defaults.
4. Make it selectable in `hermes model`.
5. Add tests for provider resolution and runtime config.
6. Add user docs that keep live model inventory tied to `/v1/models`.

Non-goals for first provider PR:
- custom Chutes MCP server support in Hermes core
- Chutes-specific model browser UX
- Chutes-specific smart-routing logic in Hermes core
- duplicating this repo's operational skills into Hermes core

## Testing requirements in this toolkit repo

- YAML examples parse and use current Hermes keys.
- `generate_agent_config.py --target hermes` refreshes `other-agents/hermes/config-examples/*.yaml`.
- Hermes skill mirror includes all current Chutes skills and points to single-sourced scripts.
- MCP docs use current `hermes mcp add/test/list` commands.
- Static docs continue to state that live model metadata comes from `/v1/models`.

## Open questions

1. Should Hermes eventually ship a bundled Chutes skill, or should it reference this repo as the install source?
2. Is `default:latency` the right starter model alias for interactive Hermes use?
3. Does Hermes need a separate first-class research endpoint, or is documented custom-provider config enough?
4. Should native provider support expose any Chutes-specific auth or model-discovery ergonomics beyond the generic OpenAI-compatible provider path?
