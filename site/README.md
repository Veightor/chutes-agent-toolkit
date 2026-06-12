# Site content pack — pages that promote agent use of Chutes

Draft copy and build notes for new pages on [chutes.ai](https://chutes.ai), aimed at one audience: **people (and agents) wiring AI agents to Chutes**. Everything here is lifted from the live-verified facts in this repo, so the site team can copy it without re-deriving anything.

Sibling asset: [`docs/site-agent-growth-kit.md`](../docs/site-agent-growth-kit.md) + [`data/agent-use-cases.json`](../data/agent-use-cases.json) provide structured use-case data and a generator (`scripts/build_agent_site_pack.py`) that complement these page drafts — drafts here are the copy, the growth kit is the data feed.

## The pages

| Draft | Proposed URL | Job |
|---|---|---|
| [`pages/agents.md`](pages/agents.md) | `chutes.ai/agents` | Landing page. Convince an agent builder in 30 seconds, get them to a working call in 60. |
| [`pages/connect-your-agent.md`](pages/connect-your-agent.md) | `chutes.ai/agents/connect` | Per-client recipes: Claude Code, Cursor, Cline, Aider, Codex, Hermes, OpenClaw, LangChain, LiteLLM, Vercel AI SDK. |
| [`pages/private-inference.md`](pages/private-inference.md) | `chutes.ai/agents/private` | The TEE story: 100% confidential-compute catalog, attestation you can fetch yourself. |
| [`pages/hermes.md`](pages/hermes.md) | `chutes.ai/agents/hermes` | Hermes deep-dive: provider YAML, skill mirror, doctor script. |
| [`pages/hermes-recipes.md`](pages/hermes-recipes.md) | `chutes.ai/agents/hermes/recipes` | Copy-paste Hermes configs: routing, delegation, dual endpoints, troubleshooting. |

Each draft contains the page copy plus a **Build notes** section (data sources, components, what must stay live-driven vs. static).

## Rules the drafts follow

1. **Pricing and the model list are never hardcoded in page copy.** Tables render from `GET https://llm.chutes.ai/v1/models` (public, no auth) at build time or client side. Snapshot numbers in the drafts are placeholders stamped with their fetch date.
2. **Claims match the toolkit's verification log.** Auth is `Authorization: Bearer $CHUTES_API_KEY` everywhere; `GET /v1/models` is public; the catalog is currently 100% TEE. If the platform changes, the drafts cite where the fact came from so it can be re-checked.
3. **Every code block is runnable.** Snippets are copies of files in [`../cookbook/`](../cookbook/), which keeps the site honest: if a cookbook script breaks, its page snippet is broken too.

## Widget specs

Two interactive components referenced by the drafts:

- **Model picker** — "I need tools + vision under $1/M" → recommended model + routing string. The exact filtering/scoring logic ships in this repo as [`scripts/pick_model.py`](../scripts/pick_model.py); port it, don't reinvent it.
- **Live pricing table** — render `id`, `context_length`, `pricing.prompt`, `pricing.completion`, `supported_features`, `input_modalities` from `/v1/models`. The daily snapshot at [`data/chutes-models.json`](../data/chutes-models.json) shows the exact shape.
