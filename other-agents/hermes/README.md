# Hermes + Chutes Quickstart

This guide shows how to use Chutes with Hermes today.

Important distinction:
- Chutes is not yet a built-in Hermes provider in upstream Hermes
- but Hermes already supports named custom OpenAI-compatible providers
- that means Chutes works now with a clean config-based setup

When live model inventory, pricing, capabilities, or TEE status matter, always use:

`https://llm.chutes.ai/v1/models`

as the source of truth.

## What you need

- Hermes installed and working
- a Chutes API key (`cpk_...`)
- access to your Hermes config and env files

Useful commands:

```bash
hermes config path
hermes config env-path
hermes status --all
```

## Recommended setup

Add Chutes as a named custom provider in `~/.hermes/config.yaml`.

Important live-auth caveat (verified 2026-04-15): Hermes custom providers usually send an Authorization Bearer header. Chutes inference succeeded in live tests with X-API-Key using a `cpk_...` key, while Bearer `cpk_...` returned 401. So this config shape is structurally correct, but may not work end-to-end until Chutes accepts Bearer `cpk_...` on the inference surface or Hermes supports overriding the auth header.

Example:

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

Then add your API key to `~/.hermes/.env`:

```bash
CHUTES_API_KEY=cpk_...
```

After that:

```bash
hermes model
```

and select the saved custom provider.

If requests fail with 401, the issue is likely the current auth-header mismatch rather than the provider YAML itself.

## Why use two named providers?

### Chutes
Use for normal inference:
- standard endpoint
- no research recording tradeoff
- safest default for private or sensitive prompts

### Chutes Research
Use when the user explicitly accepts the tradeoff:
- lower cost via research endpoint
- prompts and responses may be recorded for research
- do not use for private/sensitive data unless the user clearly opts in

## Recommended defaults

### Good starter model values

For the standard Chutes provider:
- `default`

For an interactive/chat-oriented profile:
- `default:latency`

For long generations / throughput-oriented use:
- `default:throughput`

## Delegation example

You can use a stronger premium model for the main Hermes session and point delegated tasks at Chutes.

Example config pattern:

```yaml
delegation:
  provider: custom:chutes
  model: default:throughput
  reasoning_effort: medium
```

Note: exact provider naming can depend on how Hermes resolves named custom providers in your installed version. If needed, select Chutes interactively with `hermes model` first, then inspect the saved config.

## Smart routing example

If you want Hermes to route very simple turns to Chutes while keeping a stronger main model for complex work:

```yaml
smart_model_routing:
  enabled: true
  cheap_model:
    provider: custom:chutes
    model: default:latency
```

Again, confirm the exact saved provider key in your Hermes build/version.

## TEE / privacy usage

When recommending Chutes models for privacy-sensitive use, do not rely on the `-TEE` suffix alone.

Use the live models endpoint and filter for:
- `confidential_compute: true`

That is the canonical source of truth for TEE availability.

## Suggested workflow for Hermes users

1. Configure Chutes as a named custom provider
2. Keep a normal Chutes endpoint and a research endpoint as separate saved profiles
3. Use Chutes for:
   - open-model experimentation
   - bulk/background tasks
   - privacy-sensitive TEE model flows
   - cost-efficient delegated work
4. Keep your main premium model for orchestration if desired
5. Use the live models endpoint whenever model recommendations need to be current

## Current limitations

Until Chutes becomes a first-class Hermes provider, expect these tradeoffs:
- setup is config-driven rather than a built-in provider preset
- Chutes-specific docs/skills may live in this repo rather than Hermes core
- provider picker UX may show Chutes under saved custom providers rather than built-ins

## Recommended next step

After basic setup works, pair this doc with:
- `docs/hermes-integration-spec.md`
- `docs/llms-txt-review.md`
- `docs/credential-store.md`

Those docs define the path from “works now as custom provider” to “should become first-class Hermes support.”
