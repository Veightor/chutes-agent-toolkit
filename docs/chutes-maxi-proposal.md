# Proposal: Make This Repo a True Chutes Maxi Toolkit

## Executive Summary

This repo is already a strong Chutes integration toolkit, but today it is weighted heavily toward one core story:
- help an agent use Chutes as an inference backend

That story is good, but it is not yet the biggest possible version of the project.

The strongest path forward is to evolve the repo from:
- a Chutes inference/plugin integration repo

into:
- the canonical Chutes toolkit for agents, app builders, and operator workflows across Claude, Hermes, and other OpenAI-compatible systems

In practical terms, that means expanding the repo across four product lanes:

1. Use Chutes
- account setup
- API keys
- model discovery
- inference
- routing
- TEE/privacy selection

2. Build on Chutes
- Sign in with Chutes
- OAuth app lifecycle
- scope selection
- framework integration guides
- secure storage of OAuth client credentials

3. Operate on Chutes
- model aliases
- token introspection/revocation
- usage, quotas, discounts, billing
- app secret rotation
- TEE evidence verification

4. Run agents with Chutes
- Claude skill/plugin support
- Hermes support
- Codex/openai-compatible agent docs
- agent registration / agent-native onboarding
- cheap delegation and routing patterns

My recommendation is to keep this repo as the source-of-truth integration layer for Chutes and flesh it out with a family of focused skills, docs, templates, and evals instead of growing one monolithic skill.

---

## Current State Assessment

## What is already strong

The repo already has several high-value assets:

- `README.md`
  - clear top-level positioning
  - good install guidance
  - already points toward Claude, Hermes, and generic OpenAI-compatible clients

- `plugins/chutes-ai/skills/chutes-ai/SKILL.md`
  - strong main skill covering account creation, API keys, model discovery, routing, billing, and inference

- `plugins/chutes-ai/skills/chutes-ai/scripts/manage_credentials.py`
  - a genuinely strong credential story
  - supports secure storage for:
    - `api_key`
    - `fingerprint`
    - `client_id`
    - `client_secret`
  - this is a major asset for future OAuth and app-builder workflows

- `other-agents/hermes/README.md`
  - strong “works today” Hermes setup path via custom providers

- `docs/hermes-integration-spec.md`
  - already frames a path toward first-class Hermes support

- `docs/api-reference.md`
  - useful extended operational reference

- `evals/evals.json`
  - decent early eval coverage for core Chutes usage and Hermes setup

## What feels underdeveloped

The repo still has a few strategic gaps:

1. OAuth / “Sign in with Chutes” is underrepresented
- this is one of the strongest expansion paths for the ecosystem story
- it is currently not treated like a first-class workflow in this repo

2. The repo still centers inference more than platform capability
- Chutes is being presented mainly as an OpenAI-compatible LLM provider
- the API surface suggests a much broader platform story

3. There is too much packed into one core skill
- better decomposition would make the system easier to maintain and easier for agents to invoke correctly

4. The builder persona is weak compared to the operator persona
- there is not yet a clear “I want to add Chutes to my app” path

5. The operator/power-user story is not fully surfaced
- model aliases
- token lifecycle
- app lifecycle
- usage diagnostics
- TEE verification
- secret rotation
- agent-native registration

6. Non-Claude / non-Hermes expansion is still light
- Hermes is ahead, which is good
- but there is room for more examples and packaging for other agents and tool ecosystems

---

## Why “Sign in with Chutes” Should Be a Core Pillar

The `Sign-in-with-Chutes` repo is strategically important because it changes the positioning of Chutes from:
- inference endpoint

into:
- developer platform and application identity layer

That is a much bigger opportunity.

## What the Sign-in-with-Chutes repo contributes

The repo contains a concrete OAuth application story with:
- OAuth app registration
- PKCE auth flow
- user-authorized AI usage
- Next.js integration assets
- setup/registration/verification scripts
- scope modeling
- architecture docs

This unlocks a stronger project narrative:
- not just “use Chutes for your agent”
- but “build apps that let users sign in with Chutes and invoke Chutes on their own behalf”

That is exactly the kind of move that makes this repo feel “maxi.”

## Recommendation for how to integrate it

Do not simply copy the entire repo into this one.

Instead:
- add a dedicated Sign in with Chutes skill and documentation track here
- use the Sign-in-with-Chutes repo as a canonical implementation source and example library
- selectively adapt or vendor the best pieces where agent usability improves

This keeps the toolkit focused while still making OAuth/app-builder workflows first-class.

---

## Strategic Direction

The best long-term shape for this repo is:

- canonical Chutes agent toolkit
- canonical Chutes app-integration toolkit
- canonical Chutes operator workflow toolkit
- canonical documentation source for Hermes/Claude/other-agent Chutes integration patterns

The repo should become the place a user lands when they want to do any of the following:

- use Chutes from an agent
- wire Chutes into Claude or Hermes
- add Sign in with Chutes to an app
- securely manage Chutes credentials and OAuth secrets
- discover and route models intelligently
- inspect costs, usage, discounts, and quotas
- set up private/TEE-backed workflows
- define durable model aliases
- bootstrap more agent-native Chutes workflows

---

## Proposed Product Architecture

## Four product lanes

### 1. Use Chutes
Audience:
- end users
- agent users
- developers just trying to call models

Core topics:
- registration
- fingerprint handling
- API key creation
- model discovery
- OpenAI-compatible inference
- routing
- TEE selection
- billing basics

### 2. Build on Chutes
Audience:
- application developers
- startup/product teams
- framework users

Core topics:
- Sign in with Chutes
- OAuth app creation
- scope selection
- redirect URI design
- PKCE
- user session handling
- server-side token use
- framework adapters
- secure storage of OAuth app credentials

### 3. Operate on Chutes
Audience:
- advanced users
- technical operators
- internal teams
- developers maintaining production apps or agents

Core topics:
- model aliases
- usage analytics
- discounts
- quotas
- payment summaries
- secret rotation
- token introspection/revocation
- app authorization management
- TEE evidence verification

### 4. Run Agents with Chutes
Audience:
- Hermes users
- Claude users
- users of Codex or similar agent tools

Core topics:
- Hermes provider setup
- cheap delegation
- research endpoint tradeoffs
- agent-native onboarding
- cost-aware routing
- TEE-aware workflows
- future first-class provider stories

---

## Proposed Skill Taxonomy

The current single-skill approach should evolve into a family of targeted skills.

## Recommended skill split

### 1. `chutes-core`
Use when the user wants:
- account creation
- API keys
- inference setup
- model discovery
- basic Chutes overview

Responsibilities:
- register/login guidance
- API key lifecycle
- basic `/users/me`
- `/v1/models`
- OpenAI-compatible examples
- secure storage with `manage_credentials.py`

### 2. `chutes-routing`
Use when the user wants:
- model routing
- failover pools
- latency or throughput optimization
- TEE filtering
- capability-aware model recommendations

Responsibilities:
- `default`, `default:latency`, `default:throughput`
- inline routing strings
- TEE-only routing recipes
- filtering from the live `/v1/models` endpoint
- supported feature inspection (`tools`, `json_mode`, etc.)

### 3. `sign-in-with-chutes`
Use when the user wants:
- to add Chutes login to an app
- to register or manage an OAuth app
- to implement Sign in with Chutes in a framework

Responsibilities:
- `/idp/apps`
- `/idp/scopes`
- PKCE flow
- redirect URI guidance
- scope recommendations
- token usage patterns
- `client_id` / `client_secret` storage
- framework integration checklists

### 4. `chutes-usage-and-billing`
Use when the user wants:
- balance and top-up guidance
- discounts
- quotas
- usage stats
- billing diagnostics

Responsibilities:
- `/users/me`
- `/users/me/discounts`
- `/users/me/quotas`
- `/users/me/subscription_usage`
- `/invocations/stats/llm`
- `/payments`
- `/payments/summary/tao`

### 5. `chutes-platform-ops`
Use when the user wants:
- model aliases
- app secret rotation
- token introspection
- token revocation
- app authorization management
- app sharing/admin workflows

Responsibilities:
- `/model_aliases/`
- `/idp/token/introspect`
- `/idp/token/revoke`
- `/idp/authorizations`
- `/idp/apps/{app_id}/regenerate-secret`
- app lifecycle hygiene

### 6. `chutes-hermes`
Use when the user wants:
- Hermes setup
- Chutes as custom provider
- cheap delegation to Chutes
- research endpoint profiles
- TEE-aware Hermes patterns

Responsibilities:
- Hermes custom provider setup
- config examples
- delegation examples
- smart routing examples
- transition story toward first-class provider support

### 7. `chutes-agent-registration`
Use when the user wants:
- agent-native onboarding
- hotkey/coldkey registration flows
- programmatic agent bootstrap

Responsibilities:
- `/users/agent_registration`
- `/users/{user_id}/agent_setup`
- signatures and setup flow
- agent-specific bootstrap patterns

## Why this split is better

Benefits:
- easier triggering
- less stale content per skill
- better maintainability
- better agent behavior for specialized tasks
- easier to reuse across Claude/Hermes/other systems

---

## API Surface Areas That Deserve More Attention

The API docs show several underexposed capabilities that should become first-class docs and skills.

## 1. OAuth app management
Relevant endpoints:
- `GET /idp/apps`
- `POST /idp/apps`
- `GET /idp/apps/{app_id}`
- `PATCH /idp/apps/{app_id}`
- `DELETE /idp/apps/{app_id}`
- `POST /idp/apps/{app_id}/regenerate-secret`
- `GET /idp/scopes`
- `GET /idp/authorizations`
- `DELETE /idp/authorizations/{app_id}`
- `POST /idp/token/introspect`
- `POST /idp/token/revoke`
- `GET /idp/userinfo`

Why it matters:
- turns Chutes into an app platform story
- creates a builder ecosystem angle
- supports a proper “Sign in with Chutes” workflow

## 2. Model aliases
Relevant endpoints:
- `GET /model_aliases/`
- `POST /model_aliases/`
- `DELETE /model_aliases/{alias}`

Why it matters:
- lets users define stable semantic routing handles
- reduces hardcoding of volatile model IDs
- is especially useful for agents and teams

This is a sleeper feature that deserves much more documentation and recipe coverage.

## 3. Agent registration
Relevant endpoints:
- `POST /users/agent_registration`
- `GET /users/agent_registration/{hotkey}`
- `POST /users/{user_id}/agent_setup`

Why it matters:
- differentiates Chutes from ordinary LLM providers
- suggests a richer agent-native ecosystem story
- provides a unique on-ramp for more autonomous tooling

## 4. Usage, discounts, billing, and diagnostics
Relevant endpoints:
- `GET /users/me/discounts`
- `GET /users/me/quotas`
- `GET /users/me/subscription_usage`
- `GET /invocations/stats/llm`
- `GET /invocations/usage`
- `GET /payments`
- `GET /payments/summary/tao`

Why it matters:
- makes the toolkit useful for ongoing operations, not just onboarding
- enables “doctor” style workflows
- gives teams confidence around production use

## 5. TEE verification and evidence
Relevant endpoints:
- `GET /chutes/{chute_id_or_name}/evidence`
- plus `confidential_compute` in live model metadata

Why it matters:
- privacy-sensitive use is a key Chutes differentiator
- the toolkit should help users verify, not just trust naming conventions

---

## Recommended Documentation Additions

## New top-level docs

### 1. `docs/sign-in-with-chutes.md`
Purpose:
- primary overview page for adding Chutes login to an app

Should cover:
- what Sign in with Chutes is
- when to use OAuth vs API keys
- high-level app flow
- key endpoints
- supported scopes
- where to go next by framework

### 2. `docs/oauth-app-management.md`
Purpose:
- operational guide for creating and maintaining OAuth apps

Should cover:
- create/update/delete app
- app metadata
- redirect URIs
- public vs non-public app settings
- secret rotation
- authorization management

### 3. `docs/oauth-scope-cookbook.md`
Purpose:
- opinionated scope guidance

Should cover:
- minimal auth-only scopes
- user-inference scopes
- account display scopes
- billing-read scopes
- least-privilege recommendations

### 4. `docs/model-aliases.md`
Purpose:
- operational guide for alias-driven routing

Should cover:
- alias lifecycle
- team conventions
- suggested alias packs
- examples by workload

### 5. `docs/routing-recipes.md`
Purpose:
- practical routing examples

Should cover:
- `default`
- `default:latency`
- `default:throughput`
- inline model groups
- TEE-only routing
- cost-aware routing

### 6. `docs/tee-verification.md`
Purpose:
- clarify how to actually verify privacy-sensitive paths

Should cover:
- `confidential_compute` as source of truth
- evidence endpoint usage
- how to avoid relying only on `-TEE` naming

### 7. `docs/usage-and-spend-diagnostics.md`
Purpose:
- operator guide for understanding costs and limits

Should cover:
- balance
- discounts
- quotas
- usage stats
- payment history
- common spend-debugging questions

### 8. `docs/agent-registration.md`
Purpose:
- explain agent-native onboarding path

Should cover:
- registration flow
- hotkey/coldkey/signature requirements
- setup flow
- returned assets/config patterns

### 9. `docs/frameworks/nextjs-sign-in-with-chutes.md`
Purpose:
- direct framework guide for Next.js based on the separate repo

Should cover:
- app registration
- env vars
- route wiring
- session patterns
- using access tokens server-side

### 10. `docs/frameworks/express-sign-in-with-chutes.md`
### 11. `docs/frameworks/fastapi-sign-in-with-chutes.md`
Purpose:
- broaden the builder story beyond Next.js

---

## Recommended Agent/Platform Packaging Additions

## Claude
Current status:
- strongest integration path today

Recommended additions:
- split the single skill into the family above
- keep a strong umbrella `chutes-ai` entry if desired, but make it a router to specialized skills
- add references for OAuth/app-builder workflows

## Hermes
Current status:
- good docs path via custom providers

Recommended additions:
- add a dedicated Hermes Chutes skill family or subskills
- add richer docs for:
  - delegation to Chutes
  - routing presets
  - alias usage
  - privacy-safe endpoint selection
  - TEE guidance
- keep `https://llm.chutes.ai/v1/models` explicit as live source of truth for all recommendations

## Other agents
Recommended additions:
- `other-agents/codex/README.md`
- `other-agents/cursor/README.md`
- `other-agents/generic-openai-clients/README.md`
- optionally more examples for agentic OpenAI-compatible clients

These do not all need deep custom integrations, but examples matter for adoption.

---

## Recommended Eval Expansion

Current evals are solid but still weighted toward inference and Hermes basics.

## New eval categories to add

### OAuth / app-builder evals
- registering an OAuth app
- choosing appropriate scopes
- integrating Sign in with Chutes into a Next.js app
- rotating a client secret safely
- introspecting a token to decide whether re-auth is needed
- revoking a token or authorization

### Routing / alias evals
- create a workload-specific alias pack
- recommend routing pools for low-latency TEE chat
- choose models that support tools and structured outputs
- explain when aliases are better than hardcoded model names

### Operator / billing evals
- explain why usage is spiking
- confirm whether a discount is active
- audit per-model LLM invocation stats
- explain quota behavior and subscription usage

### Agent-native evals
- explain agent registration flow
- bootstrap an agent account and setup configuration
- recommend how Hermes should use Chutes for delegated work

## Why this matters

Expanded evals will:
- enforce broader project quality
- keep the skill family from drifting
- make it easier to compare Claude/Hermes/other agent outputs
- turn the repo into a more serious integration benchmark

---

## Concrete Repo Changes

## README and positioning changes

Update `README.md` to explicitly frame the repo around the four product lanes:
- Use Chutes
- Build on Chutes
- Operate on Chutes
- Run agents with Chutes

Recommended README additions:
- a “What this repo helps you do” section
- a “For app builders” section featuring Sign in with Chutes
- a “For operators” section featuring aliases, usage, and billing
- a “For agent users” section featuring Claude/Hermes/other agents
- a docs index by audience/job-to-be-done

## New docs tree

Recommended additions:

- `docs/sign-in-with-chutes.md`
- `docs/oauth-app-management.md`
- `docs/oauth-scope-cookbook.md`
- `docs/model-aliases.md`
- `docs/routing-recipes.md`
- `docs/tee-verification.md`
- `docs/usage-and-spend-diagnostics.md`
- `docs/agent-registration.md`
- `docs/frameworks/nextjs-sign-in-with-chutes.md`
- `docs/frameworks/express-sign-in-with-chutes.md`
- `docs/frameworks/fastapi-sign-in-with-chutes.md`

## Skill tree changes

Claude/plugin side:
- `plugins/chutes-ai/skills/chutes-core/SKILL.md`
- `plugins/chutes-ai/skills/chutes-routing/SKILL.md`
- `plugins/chutes-ai/skills/sign-in-with-chutes/SKILL.md`
- `plugins/chutes-ai/skills/chutes-usage-and-billing/SKILL.md`
- `plugins/chutes-ai/skills/chutes-platform-ops/SKILL.md`
- `plugins/chutes-ai/skills/chutes-hermes/SKILL.md`
- `plugins/chutes-ai/skills/chutes-agent-registration/SKILL.md`

Hermes side:
- `other-agents/hermes/skills/chutes-core/SKILL.md`
- `other-agents/hermes/skills/sign-in-with-chutes/SKILL.md`
- `other-agents/hermes/skills/chutes-hermes/SKILL.md`
- optionally other focused subskills as needed

## Other-agents additions

Recommended additions:
- `other-agents/codex/README.md`
- `other-agents/cursor/README.md`
- `other-agents/generic-openai-clients/README.md`

## Eval changes

Expand `evals/evals.json` with categories for:
- oauth-app-registration
- oauth-scope-selection
- sign-in-with-chutes-nextjs
- model-aliases
- token-introspection
- token-revocation
- usage-audit
- discount-checking
- agent-registration

---

## Why Model Aliases Should Become a Signature Feature

This deserves special emphasis.

The `model_aliases` API is one of the most interesting under-marketed features surfaced in the API.

A very strong “maxi” move would be to teach users to define stable semantic aliases such as:
- `interactive-fast`
- `private-reasoning`
- `cheap-background`
- `agent-coder`
- `tee-chat`

Benefits:
- avoids hardcoding unstable model IDs
- supports team-level operational patterns
- gives agents stable handles to use
- pairs naturally with Hermes and Claude workflows
- strengthens Chutes’ routing story with a layer of durable abstraction

This should be featured prominently in docs and evals.

---

## Why Agent Registration Should Become a Signature Feature

The agent registration endpoints suggest a distinctive Chutes-native onboarding path for more autonomous systems.

This is not just another API-key story.

This should be treated as:
- a differentiated “agent bootstrap” flow
- a possible future pillar of Chutes agent-native identity
- an area where this repo could become uniquely valuable

Even if this starts as documentation only, it is worth elevating now.

---

## Risks and Design Constraints

## 1. Do not overload the repo with duplicate framework code
The separate Sign-in-with-Chutes repo already serves as a good implementation source.

This repo should prioritize:
- agent-oriented workflows
- docs and templates
- reusable operational guidance
- secure secret-handling patterns

not becoming an uncontrolled dumping ground for framework starter kits.

## 2. Avoid turning the main skill into a giant dumping ground
Skill decomposition matters.

Monolithic skills become:
- stale
- hard to trigger correctly
- difficult to maintain
- difficult to reuse across platforms

## 3. Keep the live models endpoint central
Any current model recommendations, pricing, features, or TEE status should continue to treat:
- `https://llm.chutes.ai/v1/models`

as the source of truth.

Static reference docs are convenience layers only.

## 4. Preserve the “works today” Hermes path
Do not block repo evolution on a future first-class Hermes provider.

The current custom-provider story is already valuable and should remain clearly documented.

---

## Prioritized Roadmap

## Phase 1: Positioning and architecture cleanup
Goal:
- reframe the repo as the canonical Chutes toolkit across the four product lanes

Tasks:
- update README positioning
- add docs index by use case
- define skill family direction in repo docs

## Phase 2: Make Sign in with Chutes first-class
Goal:
- establish Chutes app-builder workflows as a primary pillar

Tasks:
- add Sign in with Chutes docs
- add OAuth app management docs
- add scope cookbook
- add Sign in with Chutes skill
- integrate secure storage guidance for `cid_` / `csc_`

## Phase 3: Surface operator/power-user features
Goal:
- make the repo useful beyond initial setup

Tasks:
- add model aliases docs/skill
- add usage/billing docs/skill
- add token introspection/revocation docs/skill
- add TEE verification docs

## Phase 4: Expand agent-native coverage
Goal:
- strengthen Hermes and broader agent integration stories

Tasks:
- add agent registration docs/skill
- add richer Hermes routing/delegation docs
- add more examples for non-Claude agent tools

## Phase 5: Expand evals
Goal:
- validate broader coverage and prevent drift

Tasks:
- add OAuth evals
- add alias/routing evals
- add operator diagnostics evals
- add agent-registration evals

---

## Recommended Near-Term Deliverables

If only a handful of things get built first, these should be the top priorities:

### Priority 1
- `docs/sign-in-with-chutes.md`
- `docs/oauth-app-management.md`
- `plugins/chutes-ai/skills/sign-in-with-chutes/SKILL.md`

Why:
- biggest expansion of project scope
- strongest “maxi” signal
- leverages existing credential manager immediately

### Priority 2
- `docs/model-aliases.md`
- `docs/routing-recipes.md`
- `plugins/chutes-ai/skills/chutes-routing/SKILL.md`

Why:
- turns Chutes-specific routing strengths into a visible signature feature

### Priority 3
- `docs/usage-and-spend-diagnostics.md`
- `plugins/chutes-ai/skills/chutes-usage-and-billing/SKILL.md`

Why:
- upgrades the repo from onboarding guide to operational toolkit

### Priority 4
- `docs/agent-registration.md`
- `plugins/chutes-ai/skills/chutes-agent-registration/SKILL.md`

Why:
- creates a differentiated Chutes-native agent story

### Priority 5
- README restructuring across the four product lanes
- eval expansion to match the new scope

---

## Final Recommendation

The core strategic move is this:

Do not merely make the repo a better Chutes inference skill.

Make it the canonical Chutes toolkit for:
- using Chutes
- building on Chutes
- operating on Chutes
- running agents with Chutes

The single best unlock is to elevate “Sign in with Chutes” into a first-class workflow, because it transforms the repo from:
- “how to point models at Chutes”

into:
- “how to build agentic and user-facing products on top of the Chutes platform”

Paired with stronger coverage for:
- model aliases
- usage and billing operations
- token lifecycle management
- agent registration
- Hermes and other-agent recipes

this repo can become a much more complete, much more distinctive Chutes ecosystem toolkit.

That is the path to becoming a real Chutes maxi repo.
