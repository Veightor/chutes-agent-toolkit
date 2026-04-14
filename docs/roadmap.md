# Chutes Agent Toolkit Roadmap

This repository is the source-of-truth toolkit for helping agents and agent frameworks integrate with Chutes.ai.

## Mission

Provide reusable Chutes integration assets that work across multiple agent environments:
- Claude plugins and skills
- Hermes skills and provider docs
- generic OpenAI-compatible agent setups
- future MCP, SDK, or framework-specific integrations

The repository should remain useful even if a specific downstream integration takes time to land.

## Product pillars

### 1. Canonical Chutes documentation for agents

This repo should contain the best agent-oriented documentation for:
- account lifecycle
- API keys and credential handling
- model discovery
- model routing
- TEE / confidential compute
- billing, usage, and quotas
- framework integration patterns

Important: static model snapshots are only convenience references. When live model inventory, pricing, or metadata is required, agents should use:

`https://llm.chutes.ai/v1/models`

as the source of truth.

### 2. Secure credential tooling

This repo should provide a reliable, auditable way for agents to store and retrieve Chutes credentials without leaking secrets into plaintext files, command histories, or transcripts.

Near-term target:
- harden and test `manage_credentials.py`
- document invocation patterns for agents
- make multi-profile workflows easy

### 3. Evaluated agent workflows

This repo should include scenario-driven evals that verify agents can correctly:
- onboard users
- manage API keys
- recommend models
- configure routing
- explain TEE/privacy tradeoffs
- integrate Chutes with popular agent stacks

### 4. Hermes-ready integration assets

This repo should become the staging ground for Hermes integration by providing:
- Hermes config examples
- Hermes-ready Chutes skill packaging
- implementation notes for a native Hermes provider
- test cases and docs that can be reused in a Hermes fork/PR

### 5. Upstreamability

Work produced here should make it easier to upstream Chutes support into Hermes and other agent projects.

That means:
- keep docs clean and reusable
- keep examples realistic and tested
- prefer narrow, mergeable downstream PRs over giant platform-specific dumps

## Four product lanes (adopted 2026-04-13)

All skill work is organized around four lanes, matching the Hermes `docs/chutes-maxi-proposal.md`:

1. **Use Chutes** — account, keys, models, inference, TEE selection, billing basics. Skill: `chutes-ai` (hub).
2. **Build on Chutes** — Sign in with Chutes, OAuth apps, framework adapters, client secret lifecycle. Skill: `chutes-sign-in` **[BETA]**.
3. **Operate on Chutes** — model aliases, usage/quota/billing, token lifecycle. Wave-2 stubs: `chutes-routing`, `chutes-usage-and-billing`, `chutes-platform-ops`.
4. **Run agents with Chutes** — Claude/Hermes/Cursor/Cline/Aider/MCP/agent-native registration. Skills: `chutes-deploy` **[BETA]**, `chutes-mcp-portability` **[BETA]**, wave-2 stub `chutes-agent-registration`.

## Beta labeling policy

Deploy-side features and anything not exercised against a live Chutes account before the commit that introduced it ship labeled **BETA**. A BETA label is removed only by a commit that references a concrete verification run. See `README.md` → "Beta features" and `docs/chutes-maxi-proposal.md`.

## Execution phases

### Phase 1: Foundation
- clean up repo docs and boundaries
- write Hermes integration spec
- document roadmap and ownership boundaries

### Phase 2: Credential tooling
- add tests for `manage_credentials.py`
- improve docs and edge-case handling
- finalize deprecation story for `save_credentials.py`

### Phase 3: Shared docs and routing patterns
- consolidate canonical docs under `docs/`
- add routing and Hermes-specific guides
- reduce duplication across README, Claude plugin docs, and generic-agent docs

### Phase 4: Evals
- expand `evals/evals.json`
- add an eval runner and fixtures
- separate live-API checks from static-doc correctness checks

### Phase 5: Hermes-facing assets in this repo
- add Hermes quickstart docs
- add named custom provider examples
- add a Hermes-oriented Chutes skill export/package layout

### Phase 6: Hermes fork work — **DELIVERED (sibling repo, 2026-04-13)**
- ~~add first-class Chutes provider support in a Hermes fork~~ ✓ shipped from a separate repository
- ~~add docs/tests for provider resolution and setup UX~~ ✓ shipped alongside
- ~~keep initial PR scope tight and upstreamable~~ ✓
- this toolkit no longer tracks phase-6 work; see `docs/hermes-integration-spec.md` for historical context

### Phase 7: Upstreaming and polish — **DELIVERED (sibling repo, 2026-04-13)**
- ~~propose upstream merge to Hermes/Nous~~ ✓ handled in the sibling repo
- follow-up routing ergonomics remain open as a wave-3 idea

### Phase 8: Sign in with Chutes + MCP surface (wave 1, 2026-04-13)

Completed in wave 1 (all [BETA] until verified):

- `chutes-sign-in` skill — register OAuth app, vendor upstream Next.js package, verify, rotate client secret.
- `chutes-deploy` skill — vLLM / diffusion / custom CDK deploy, teeify, rolling updates, alias pinning.
- `chutes-mcp-portability` skill — stdio MCP server exposing Chutes management + inference, `generate_agent_config.py` for Cursor / Cline / Aider / Hermes / system-prompt.
- Symmetric `other-agents/hermes/skills/` mirror so Hermes has parity with Claude.
- Hub `chutes-ai/SKILL.md` slim-down + sibling router.
- Wave-2 stubs scaffolded to reserve trigger territory.

Wave 2 (future):

- Flesh out `chutes-routing`, `chutes-usage-and-billing`, `chutes-platform-ops`, `chutes-agent-registration`.
- TEE attestation verification skill (`chutes-tee`) that parses TDX quotes.
- Upstream framework adapters (Express, FastAPI) for `chutes-sign-in` when the SIWC repo ships them.
- Hermes native provider PR (phase 6) using the wave-1 MCP server as one integration path.

## Non-goals right now

These may happen later, but they are not the immediate focus:
- ~~building a full Chutes MCP server in this repo~~ (shipped in wave 1 as `chutes-mcp-portability` **[BETA]**)
- replacing the Chutes official docs
- hardcoding static model lists as authoritative data
- tightly coupling the toolkit to only one agent platform

## Definition of success

This repo is successful when:
- a new agent user can integrate Chutes quickly and correctly
- credential handling is secure and tested
- docs point to live sources where appropriate
- Hermes users have a clean path today via custom provider config
- Hermes maintainers can review a future first-class provider PR with minimal ambiguity
