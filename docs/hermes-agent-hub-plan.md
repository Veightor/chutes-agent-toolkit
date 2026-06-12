# Hermes Agent Hub Contribution Plan

> Scope: Hermes-first additions for `chutes-agent-toolkit`, designed to give the Chutes site team concrete pages, proof points, and a runnable local diagnostic for agent builders.

## What this repo already does

- Provides a Claude plugin plus mirrored Hermes skills for Chutes account setup, model discovery, routing, usage/billing, TEE evidence, MCP portability, and deploy/agent-registration beta flows.
- Documents the universal OpenAI-compatible Chutes endpoint in `docs/endpoint-guide.md`.
- Keeps live model inventory grounded in `GET https://llm.chutes.ai/v1/models`, with daily snapshots under `data/` and `docs/known-models.md`.
- Ships Hermes config examples under `other-agents/hermes/config-examples/` and a full Hermes guide under `docs/hermes-chutes-toolkit-guide.md`.

## Gaps worth filling

1. **No Hermes-specific site copy.** The repo has strong technical docs, but no polished Chutes-site page that tells a Hermes user why Chutes matters: private TEE inference, OpenAI compatibility, delegation, MCP tools, and live model routing.
2. **No self-check command for Hermes users.** A user can copy YAML, but there was no one-command way to verify Hermes presence, key discovery, public model metadata, and safe config output without leaking secrets.
3. **No page-ready recipe pack.** Hermes has several powerful patterns — provider, MCP, delegation, cheap routing, research endpoint, TEE evidence — but they are scattered across repo docs instead of staged as website sections.
4. **No clear Chutes Hub CTA for agents.** The site should not just say "OpenAI-compatible"; it should position Chutes as an agent runtime: live model discovery, routing aliases, privacy defaults, and tools through MCP.

## Contributions in this branch

### 1. Hermes doctor script

Path: `scripts/hermes_chutes_doctor.py`

Purpose:
- Fetches the public Chutes model catalog.
- Counts Hermes-relevant capabilities: tools, JSON mode, structured outputs, vision, reasoning, and TEE coverage.
- Detects Hermes CLI and `CHUTES_API_KEY` without printing raw secrets.
- Emits a ready-to-paste Hermes provider config using `key_env: CHUTES_API_KEY`.
- Auth validation is explicit opt-in via `--check-auth`; default run has no authenticated Chutes account call.

Example:

```bash
python3 scripts/hermes_chutes_doctor.py
python3 scripts/hermes_chutes_doctor.py --emit-config --include-research
python3 scripts/hermes_chutes_doctor.py --json
```

### 2. Hermes site page draft

Path: `site/pages/hermes.md`

Job:
- Proposed Chutes site page at `chutes.ai/agents/hermes`.
- Landing-page copy for Hermes users: hero, quickstart, provider YAML, MCP setup, delegation, privacy, and CTAs.
- Includes build notes for live data widgets so model/pricing claims stay tied to `/v1/models`.

### 3. Hermes recipes page draft

Path: `site/pages/hermes-recipes.md`

Job:
- Proposed Chutes site page at `chutes.ai/agents/hermes/recipes`.
- Short, shippable recipes for provider mode, MCP mode, delegation, cheap routing, research opt-in, TEE evidence, and troubleshooting.
- Designed as cards/accordion content rather than a long technical manual.

### 4. README and Hermes guide links

Paths:
- `README.md`
- `other-agents/hermes/README.md`
- `docs/hermes-chutes-toolkit-guide.md`

Job:
- Surface the new doctor script and site drafts where maintainers and Hermes users will find them.

## Chutes site structure proposal

```text
/agents
  General agent-builder landing page.
/agents/connect
  Tabs for Claude, Hermes, Cursor/Cline/Aider, OpenClaw, LiteLLM, Vercel AI SDK, MCP.
/agents/hermes
  Hermes-specific landing page from this branch.
/agents/hermes/recipes
  Practical Hermes recipes from this branch.
/agents/private
  TEE/confidential-compute page.
```

The Hermes page should link back to this repo, not duplicate every deep instruction. The repo remains the canonical implementation package; the site is the conversion layer.

## Site widget ideas

- **Live model strip:** count models, TEE coverage, tool-capable count, vision-capable count. Source: `GET https://llm.chutes.ai/v1/models`.
- **Hermes config generator:** form toggles for normal endpoint, research endpoint, delegation, and direct model pin; output YAML equivalent to `scripts/hermes_chutes_doctor.py --emit-config`.
- **Agent runtime selector:** cards for "private coding", "cheap delegation", "vision review", "tool-calling agent", each populated from live metadata.
- **Copy-safe key handling note:** tell users to put `CHUTES_API_KEY` in `~/.hermes/.env`, never in YAML or chat.

## Acceptance checklist

- Site copy does not hardcode model count/pricing without a dated source.
- Site snippets use Bearer/OpenAI SDK auth semantics, not `X-API-Key`.
- Hermes config uses `providers:` with `key_env: CHUTES_API_KEY` and `transport: chat_completions`.
- Research endpoint is always explicitly opt-in and labeled as prompt/response recording.
- TEE claims say `confidential_compute: true`; cryptographic attestation claims require `chutes-tee` evidence verification.
- The doctor script never prints raw keys and keeps authenticated checks opt-in.

## Later high-value follow-ups

1. Port `scripts/hermes_chutes_doctor.py --json` into a small Chutes site widget that renders live Hermes recommendations.
2. Add a `hermes mcp test` transcript once a clean Chutes key is available in a disposable environment.
3. Add a one-minute screen-recording script: install skills, run doctor, paste config, ask Hermes to call Chutes.
4. Consider upstream Hermes PR for first-class Chutes provider only after this repo's custom-provider path is stable and current.
