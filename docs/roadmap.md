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

### Phase 8: Sign in with Chutes + MCP surface (wave 1, 2026-04-13) — DELIVERED

Completed in wave 1:

- `chutes-sign-in` skill — register OAuth app, vendor upstream Next.js package, verify, rotate client secret.
- `chutes-deploy` skill — vLLM / diffusion / custom CDK deploy, teeify, rolling updates, alias pinning.
- `chutes-mcp-portability` skill — stdio MCP server exposing Chutes management + inference, `generate_agent_config.py` for Cursor / Cline / Aider / Hermes / system-prompt.
- Symmetric `other-agents/hermes/skills/` mirror so Hermes has parity with Claude.
- Hub `chutes-ai/SKILL.md` slim-down + sibling router.
- Wave-2 stubs scaffolded to reserve trigger territory.

### Phase 9: Live verification + wave-2 skill buildout (wave 2, 2026-04-13) — DELIVERED

Track C — live verification against a real Chutes account (credentials from the local keychain) and BETA graduation:
- Environment sanity, MCP self-check, credential round-trip.
- SIWC end-to-end against a scratch Next.js project (caught + fixed 2 real wave-1 bugs: wrong upstream source paths; `rotate_secret.py` using `client_id` instead of `app_id` UUID).
- Deploy lane attempted: platform-side gate found (HTTP 403 "Easy deployment is currently disabled!"), bugs fixed (`--revision main` → SHA auto-resolve), `chutes-deploy` stays permanent BETA per policy.
- MCP alias round-trip: caught + fixed wave-1 schema bug (`{alias, chute_ids: []}` not `{alias, model}`).
- 7 MCP read tools graduated out of BETA with recorded verified calls.

Track A — wave-2 stubs fleshed out as full live-verified skills:
- `chutes-routing` — intent-driven pool builder + audit with 5 recipes, alias-packs reference. Verified live.
- `chutes-usage-and-billing` — spend dashboard + time-bucketed breakdown + quota guard + CSV export. Verified live; discovered that `/invocations/*` and `/payments*` are platform-wide aggregates (clearly labeled in the skill).
- `chutes-platform-ops` — OAuth fleet management across the 16 real OAuth apps on the test account. `list_apps.py`, `audit_stale_apps.py`, `rotate_all.py --dry-run`, `alias_crud.py` verified live. Token introspect/revoke stay BETA pending a real OAuth token.
- `chutes-agent-registration` — dry-run verified. Stays BETA because registering a real Bittensor-backed agent account has on-chain implications.

Track B — new `chutes-tee` skill (not a stub):
- TDX v4 quote parser, NVIDIA Hopper GPU attestation parser, shape-only verdict.
- Verified live against a real TEE chute (`Qwen/Qwen3-32B-TEE`, 7 instances, 56 Hopper GPUs).
- Ships `shape-valid` by default; cryptographic validation requires Intel DCAP tooling.

Hermes native provider — delivered in a sibling repo; phase 6/7 marked complete.

### Phase 10: wave 3 brainstorm (not yet scoped)

- Graduate `chutes-sign-in:verify_siwc.py` step 4 (dev server hit) via a scripted Playwright run.
- Graduate `chutes-platform-ops:introspect_token.py` / `revoke_token.py` via a completed live SIWC flow.
- Graduate `chutes-mcp-portability:chutes_chat_complete` / `chutes_get_evidence` / `chutes_oauth_introspect` — the three unexercised read tools.
- Graduate `chutes-tee` from `shape-valid` to `verified` by wiring in Intel DCAP on a Linux CI runner.
- Automated alerting loops for `quota_guard.py` and `audit_pool.py` (promote from read-only scripts to scheduled background jobs).
- Parquet + DuckDB pipeline for `/invocations/exports/*` (mentioned in wave-2 usage skill).
- Cost-aware router daemon that rebalances aliases nightly based on live pricing + discounts.
- TEE compliance mode that forces all inference through verified-attestation chutes and refuses otherwise.
- Upstream framework adapters (Express, FastAPI) for `chutes-sign-in` when the SIWC repo ships them.

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
