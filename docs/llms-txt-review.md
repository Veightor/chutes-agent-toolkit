# Review Notes: chutes.ai/llms.txt

This document captures concrete suggestions for improving `https://chutes.ai/llms.txt` based on a live review.

## Overall assessment

`llms.txt` is already strong.

What it does well:
- explains the two-base-URL split clearly
- includes high-value account, billing, routing, and TEE guidance
- exposes machine interfaces (`openapi.json`, plugin manifest, models endpoint)
- is genuinely useful to agentic systems instead of being a thin marketing stub

The main opportunities are around consistency, small correctness fixes, and making it even easier for agent frameworks to treat it as a canonical operational document.

## High-priority fixes

### 1. Fix malformed authentication sentence near the top

Current text in the Agent Instructions section reads like this:

`Authenticate every request with Authorization: Bearer *** All POST/PATCH requests require Content-Type: application/json.`

Issue:
- missing closing backtick / punctuation separation
- reduces readability for parsers and humans

Suggested rewrite:

`Authenticate every request with \`Authorization: Bearer <token>\`. All POST/PATCH requests require \`Content-Type: application/json\`.`

### 2. Resolve TEE evidence endpoint inconsistency

There appears to be an inconsistency:
- TEE section says attestation evidence is available at:
  - `GET https://api.chutes.ai/chutes/{chute_id}/evidence`
- API reference table later lists:
  - `GET https://api.chutes.ai/instances/{id}/evidence`

Issue:
- an agent or developer cannot tell which endpoint is authoritative

Recommendation:
- verify the correct endpoint(s)
- if both are valid, document the difference explicitly:
  - chute-level evidence vs instance-level evidence
- if only one is valid, remove the other reference

### 3. Mark `https://llm.chutes.ai/v1/models` as the live source of truth more explicitly

The file already exposes the models endpoint, but it should more strongly state:
- static examples can drift
- model inventory, pricing, supported features, TTFT/TPS, and TEE flags should be fetched live from `/v1/models`

Suggested addition near Model Discovery and again near Machine Interfaces:

`When current model availability, pricing, routing candidates, or capability metadata matter, always use https://llm.chutes.ai/v1/models as the source of truth.`

## Medium-priority improvements

### 4. Add a short “Quick recipes for agents” section near the top

Right now the file is rich, but it makes agents scan a lot before getting to common workflows.

Suggested short recipes section:
- get current user info
- list models
- call a model
- use TEE models only
- use research endpoint
- use routing aliases

This would help both human readers and agents that want fast operational guidance.

### 5. Add a minimal routing cheat sheet with concrete examples

The current routing coverage is good, but `llms.txt` would benefit from an explicit compact block like:

- `default` → failover in configured order
- `default:latency` → choose lowest TTFT now
- `default:throughput` → choose highest TPS now
- `modelA,modelB,modelC` → inline failover
- `modelA,modelB,modelC:latency` → inline latency routing
- `modelA,modelB,modelC:throughput` → inline throughput routing

Why:
- routing is one of Chutes’s strongest agent-facing features
- surfacing it earlier increases the odds agents actually use it well

### 6. Annotate OAuth-only endpoints more consistently

The file already notes that `/idp/userinfo` requires OAuth access tokens, not `cpk_` API keys. That’s great.

Suggestion:
- mark OAuth-only endpoints directly in the API reference table as well
- add a short note like `OAuth token required; not usable with cpk_ API keys`

This helps agents avoid dead-end API calls.

### 7. Add response-shape hints for the most important endpoints

The doc often explains responses in prose, but a few short canonical response-shape snippets would help a lot.

Most valuable candidates:
- `/users/me`
- `/v1/models`
- `/users/me/discounts`
- `/invocations/stats/llm`
- `/model_aliases/`

Why:
- agents can reason more accurately when field shapes are visible
- reduces the need to inspect Swagger/OpenAPI for common tasks

### 8. Add an explicit “safe/default endpoint selection” note

The file should make the default endpoint decision very easy:
- use `https://llm.chutes.ai/v1` unless the user explicitly opts into research recording
- use `https://research-data-opt-in-proxy.chutes.ai/v1` only when cost savings justify sending data for research

This is already implied, but it would be useful to say more bluntly.

## Nice-to-have improvements

### 9. Add “agent do/don’t” guidance

A short operational guidance block could be valuable:

Do:
- fetch `/v1/models` live before making pricing/capability recommendations
- use `confidential_compute` instead of suffix matching for TEE selection
- null-check optional arrays like `quotas` and `netuids`

Don’t:
- assume static model names remain available forever
- send private data to the research endpoint without explicit consent
- treat platform-wide usage endpoints as user-only usage

### 10. Add a “common misconceptions” section

Examples:
- `-TEE` suffix is not the source of truth; `confidential_compute` is
- `/invocations/usage` is platform-wide, not just user usage
- `GET /idp/userinfo` is not for `cpk_` keys
- list endpoints are 0-indexed

This would reduce repeated integration mistakes.

### 11. Consider surfacing OpenAI-compatibility caveats more explicitly

For example:
- model-specific supported parameters vary
- agents should inspect `supported_features` and `supported_sampling_parameters`
- not all models support tools / JSON mode / structured outputs

That guidance exists, but a more explicit “compatibility checklist” would help framework authors.

### 12. Add “last updated” metadata to llms.txt

Even if live endpoints are canonical, it helps to include:
- last updated date
- docs version or generation timestamp
- maybe a note that `/v1/models` is live while `llms.txt` is operational guidance

## Proposed structural revision

Suggested high-level order:
1. What Chutes is
2. Quick recipes for agents
3. Base URLs and auth rules
4. Model discovery + source-of-truth note
5. Routing
6. TEE / privacy
7. Billing / usage
8. Account and key management
9. Deployment / SDK
10. API reference table
11. Machine interfaces
12. Full docs / repos / products

Reason:
- puts highest-frequency agent tasks earlier
- moves less frequently used reference material later
- reduces time-to-first-use for automated systems

## Suggested copy additions

### Suggested source-of-truth line

`For live model availability, pricing, capabilities, routing candidates, and TEE status, always use https://llm.chutes.ai/v1/models as the source of truth.`

### Suggested endpoint safety line

`Default to https://llm.chutes.ai/v1 for normal inference. Only use https://research-data-opt-in-proxy.chutes.ai/v1 when the user explicitly accepts that prompts and responses may be recorded for research in exchange for lower cost.`

### Suggested TEE clarification line

`Use the model field confidential_compute=true as the canonical indicator for TEE availability; the -TEE suffix is only a naming convention and should not be treated as authoritative.`

## Summary

Top 3 changes I’d make first:
1. fix the malformed auth sentence
2. resolve the TEE evidence endpoint inconsistency
3. make `/v1/models` the explicitly repeated source of truth for live model data

If those are fixed first, `llms.txt` becomes even more reliable as an agent-facing operational reference.
