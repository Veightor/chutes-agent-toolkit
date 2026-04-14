# Hermes Integration Spec for Chutes Agent Toolkit

This document defines the target state for integrating Chutes cleanly with Hermes.

## Goal

Make Chutes feel like a first-class Hermes provider while keeping this toolkit repo as the canonical source for Chutes-specific docs, skill content, examples, and integration guidance.

## Principles

1. Chutes should work in Hermes immediately via named custom provider config.
2. A future Hermes fork/PR should add first-class provider UX without duplicating all Chutes docs into Hermes core.
3. Live model inventory and metadata must come from:

`https://llm.chutes.ai/v1/models`

Static lists in this repo are convenience references only.

4. The first upstream Hermes PR should be narrow, mergeable, and low-risk.

## Integration paths (updated 2026-04-13, wave 2)

There are now **four** integration paths for Hermes, and the fourth has already been delivered in a sibling repo (out of scope for this toolkit):

1. **Custom provider YAML** (layer 1 — works today). See `other-agents/hermes/config-examples/`. Generated/refreshed by `plugins/chutes-ai/skills/chutes-mcp-portability/scripts/generate_agent_config.py --target hermes`.
2. **Symmetric skill tree** (wave 1). `other-agents/hermes/skills/{chutes-ai,chutes-sign-in,chutes-deploy,chutes-mcp-portability}/` mirrors the Claude plugin tree so Hermes loads the same four-lane skill set. Scripts live once in the Claude plugin tree and are invoked from the repo root by either agent.
3. **MCP server** (wave 1). `chutes-mcp-server` (stdio, from `plugins/chutes-ai/skills/chutes-mcp-portability/mcp-server/`) gives any MCP-aware Hermes build tool-level access to Chutes without touching the provider config. Use it alongside the custom-provider YAML, not instead of it. Wave-2 Track C.2 verified the server end-to-end with `--self-check` + 7 read tools.
4. **Native Hermes provider** — **DELIVERED IN A SIBLING REPO.** The first-class Chutes provider PR for Hermes / Nous has already shipped from a separate repository (not this toolkit). This toolkit no longer tracks phase-6 Hermes fork work as a pending goal. See the legacy "Layer 2" section below for the original spec (retained as historical context; the implementation is elsewhere).

## Integration layers

### Layer 1: Works today in Hermes via custom provider

Users should be able to configure Chutes in Hermes today with a named custom provider.

Recommended user-facing config pattern:

```yaml
custom_providers:
  - name: Chutes
    base_url: https://llm.chutes.ai/v1
    key_env: CHUTES_API_KEY
    api_mode: chat_completions
    model: default

  - name: Chutes Research
    base_url: https://research-data-opt-in-proxy.chutes.ai/v1
    key_env: CHUTES_API_KEY
    api_mode: chat_completions
    model: default:latency
```

Recommended environment variable:

```bash
CHUTES_API_KEY=cpk_...
```

### Layer 2: First-class Hermes provider (historical — now delivered elsewhere)

> **Update 2026-04-13:** The native Hermes provider described in this section has already been delivered in a separate repository. This toolkit does not track the phase-6 fork work anymore. Everything below is retained for historical reference and to document what the native provider looks like.

A Hermes fork/PR makes Chutes appear in the provider picker and runtime provider logic as a built-in provider.

Expected user experience:
- Chutes appears in `hermes model`
- Hermes status/doctor can identify whether Chutes auth is configured
- docs/setup flow mention Chutes explicitly
- Chutes remains OpenAI-compatible under the hood using chat completions

## Provider design target

### Provider identity

Proposed provider slug:
- `chutes`

Optional future variants:
- keep research endpoint as documentation-only at first
- or later consider `chutes-research` only if UX justifies it

Recommendation:
- first PR should add only `chutes`
- research endpoint should initially remain a documented alternate base URL / custom-provider pattern

### Runtime behavior

Expected defaults:
- base URL: `https://llm.chutes.ai/v1`
- auth env var: `CHUTES_API_KEY`
- api mode: `chat_completions`
- model: configurable by user

Reasoning:
- Chutes is OpenAI-compatible
- the simpler the implementation, the easier to upstream

## Chutes-specific ergonomics to document

These should be documented even if not encoded as special Hermes logic initially:

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

4. Research endpoint tradeoff:
- `https://research-data-opt-in-proxy.chutes.ai/v1`
- same auth, lower cost, but prompt/response data is recorded for research

## Hermes fork scope: phase 1

Files likely to change in Hermes fork:
- `hermes_cli/auth.py`
- `hermes_cli/models.py`
- `hermes_cli/main.py`
- `hermes_cli/config.py`
- `hermes_cli/runtime_provider.py`
- docs and tests relevant to provider selection and auth resolution

Minimum acceptable implementation:
1. Add Chutes to provider registry
2. Wire `CHUTES_API_KEY`
3. Set base URL and API mode defaults
4. Make it selectable in CLI provider picker
5. Add tests for provider resolution and runtime config
6. Add user docs

Non-goals for first PR:
- custom Chutes MCP server support
- Chutes-specific model browser UX
- Chutes-specific smart-routing logic in Hermes core
- over-optimizing the setup wizard before provider basics land

## Hermes fork scope: phase 2

After first-class provider support lands or stabilizes:
1. add stronger docs/examples for routing presets
2. bundle or recommend a Hermes-ready Chutes skill
3. improve setup wizard copy
4. optionally improve doctor/status output for Chutes-specific hints

## Testing requirements

### In this toolkit repo
- docs examples for Hermes custom provider config must be coherent
- Chutes skill guidance should reflect Hermes-specific usage where relevant
- evals should include Hermes setup scenarios

### In Hermes fork
- provider selection works from CLI
- env var auth loads correctly
- runtime provider resolution yields Chutes base URL and chat-completions mode
- no regressions to generic custom provider support

## Open questions

1. Should Hermes ship a built-in Chutes skill, or should it reference this repo as the install source?
2. Is `default` the right starter model alias, or should docs prefer `default:latency` for interactive use?
3. Does Hermes need a separate first-class research endpoint, or is documented custom-provider config enough?
4. Should Chutes provider docs include explicit TEE selection recipes from day one?

## Recommended next step

Before touching a Hermes fork, finish the toolkit-side work here:
- roadmap/docs cleanup
- credential-tooling hardening
- eval expansion
- Hermes quickstart examples

That will make the eventual Hermes PR far easier to write, test, and justify.
