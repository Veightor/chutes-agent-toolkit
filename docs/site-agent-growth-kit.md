# Chutes Agent Growth Kit

This page is source material for Chutes site builders. It is not the website repo. Use it to publish "Run agents on Chutes" pages backed by checked-in docs, structured data, and demo prompts from this toolkit.

Source assets:

- Site/demo data: `data/agent-use-cases.json`
- Generator: `scripts/build_agent_site_pack.py`
- Site page drafts: `site/README.md` and `site/pages/`
- Runnable examples: `cookbook/README.md`
- Model picker logic: `scripts/pick_model.py`
- Flagship Codex guide: `other-agents/codex/README.md`
- Universal endpoint guide: `docs/endpoint-guide.md`
- Live catalog source: `https://llm.chutes.ai/v1/models`

Generate the site pack:

```bash
python3 scripts/build_agent_site_pack.py --format markdown
python3 scripts/build_agent_site_pack.py --focus codex --format json
```

## Run Codex on Chutes

Page angle: coding agents already speak the OpenAI API. Chutes gives those agents an OpenAI-compatible inference endpoint for open-source models, with Bearer auth and routing in the `model` field.

Copy block:

Codex-style coding agents can use Chutes anywhere the runtime accepts an OpenAI-compatible chat-completions base URL. Store the key in `CHUTES_API_KEY`, set the base URL to `https://llm.chutes.ai/v1`, and pick either a routing alias such as `default:latency` or a concrete model ID from the live `/v1/models` catalog.

Recommended demo:

```text
Audit this repository for failing tests, propose the smallest fix, and run the relevant test command. Use Chutes for model calls and keep credentials in CHUTES_API_KEY.
```

Do not claim that every upstream Codex build has a built-in Chutes provider. The repo-supported claim is narrower: Chutes works through the OpenAI-compatible configuration surface used by Codex-style agents and SDK-backed tools.

Proof links:

- `other-agents/codex/README.md`
- `docs/endpoint-guide.md`
- `docs/known-models.md`
- `cookbook/README.md`
- `scripts/pick_model.py`

## Open-source TEE inference for agents

Page angle: agents handle code, credentials, internal tickets, user messages, and long task traces. Chutes gives agent builders a way to route that inference to open-source models running in hardware-isolated confidential compute.

Copy block:

Chutes hosts open-source LLMs behind an OpenAI-compatible endpoint. As of the 2026-06-11 live verification recorded in this repo, every hosted LLM in the public catalog reports `confidential_compute: true`. Treat `https://llm.chutes.ai/v1/models` as the source of truth and filter on the boolean field, not the `-TEE` suffix.

Honest boundaries:

- TEE evidence can support hardware-isolation claims, but cryptographic verification requires DCAP tooling to run and pass.
- TEE does not solve prompt injection, tool misuse, application logging, user-approved data sharing, or secrets placed in prompts.
- Model availability and prices change. Site pages should cite the live model endpoint or this repo's generated snapshot, not stale model lists.

Proof links:

- `plugins/chutes-ai/skills/chutes-tee/SKILL.md`
- `plugins/chutes-ai/skills/chutes-tee/references/what-tee-does-not-protect.md`
- `docs/known-models.md`

## One OpenAI-compatible endpoint, many agent stacks

Page angle: Chutes is not a one-agent integration. It is a single inference plane and toolkit that can feed coding agents, editor agents, channel agents, Claude skills, Hermes, and SDK-backed custom loops.

Copy block:

Use one base URL, one Bearer key, and one live model catalog across agent stacks:

- Codex-style coding agents: `other-agents/codex/README.md`
- Claude skills: `plugins/chutes-ai/skills/`
- Hermes providers and skills: `other-agents/hermes/README.md`
- Cursor, Cline, Aider, and MCP clients: `plugins/chutes-ai/skills/chutes-mcp-portability/SKILL.md`
- OpenClaw channel agents: `other-agents/openclaw/README.md`
- Generic OpenAI SDK agents: `other-agents/openai-compatible/README.md`

The setup shape stays stable:

```text
base_url = https://llm.chutes.ai/v1
api_key = read CHUTES_API_KEY from the environment or keychain
model = routing alias or live model ID from /v1/models
```

Companion proof assets:

- Use `cookbook/` for snippets on marketing pages and docs. The examples cover first call, streaming, tool calling, structured output, routing failover, vision, and a small tool-calling agent loop.
- Use `scripts/pick_model.py` as the reference implementation for model-picker widgets and "which model should my agent use?" demos.
- Use `site/pages/` for page drafts, but keep Codex as the first coding-agent path when this kit is the source of truth.

## Routing, cost control, and private inference

Page angle: agent traffic is mixed. Interactive coding, review, planning, summarization, and background tasks should not all use the same static model ID.

Copy block:

Chutes routing lets agents choose a policy in the `model` string. Use `default:latency` for interactive work, `default:throughput` for longer background generations, or a comma-separated pool with a strategy suffix for explicit failover. When a workflow needs a specific context window, modality, tool support, JSON mode, or price point, fetch `https://llm.chutes.ai/v1/models` and choose from current metadata.

Cost-control patterns:

- Use routing aliases for uptime-sensitive workflows instead of hardcoding one model.
- Use the live `pricing` object before recommending a "cheap" background model.
- Use `pricing.input_cache_read` when explaining prompt-cache economics.
- Check account spend and caps through the usage/billing skills before scaling background agents.
- Use the research endpoint only when the user explicitly accepts that prompts and responses may be recorded for research. Do not use it for private workflows by default.

Private-inference pattern:

```text
1. Fetch /v1/models.
2. Filter for confidential_compute == true.
3. Confirm required capabilities such as tools or json_mode.
4. Choose a routing alias or concrete model.
5. For stronger proof, fetch and parse TEE evidence before making cryptographic claims.
```

## Agent demos worth showing

Use demos that prove agent value and Chutes-specific behavior without needing live writes, paid deploys, or credential reads.

### Codex repository repair

Prompt:

```text
Find the smallest failing test path in this repo, patch the bug, and rerun only the relevant test command. Use CHUTES_API_KEY from the environment for model calls.
```

Why it works: shows coding-agent workflow, Chutes as OpenAI-compatible inference, and secret-safe setup.

### Routing preset picker

Prompt:

```text
Given an interactive coding agent, a review agent, and a nightly documentation agent, choose Chutes model values and explain when to use default:latency, default:throughput, or a concrete live model ID.
```

Why it works: shows routing, cost control, and avoiding stale model claims.

### TEE-safe copy audit

Prompt:

```text
Rewrite this landing-page section so it explains Chutes TEE benefits for agents without claiming cryptographic attestation unless verification was actually run.
```

Why it works: demonstrates accurate privacy messaging and avoids overclaiming.

### MCP editor-agent setup

Prompt:

```text
Generate a Cursor MCP config for Chutes, run the MCP self-check, and label which tools are read-only versus beta write tools.
```

Why it works: shows editor-agent distribution through a concrete toolkit path.

### Channel agent provider swap

Prompt:

```text
Add Chutes as an OpenClaw provider for channel agents and explain why the research endpoint should not be the default for private conversations.
```

Why it works: connects OpenAI-compatible setup, routing, and privacy tradeoffs.

## Publishing Checklist

- Keep Codex as the headline integration, with other agents as supporting ecosystem paths.
- Use `data/agent-use-cases.json` for page cards and demo prompts.
- Generate Markdown or JSON with `scripts/build_agent_site_pack.py` rather than hand-copying tables.
- Keep `site/pages/connect-your-agent.md` aligned with the Codex-first positioning in this kit.
- Keep code snippets backed by `cookbook/` examples and model-choice UI backed by `scripts/pick_model.py`.
- Link to `https://llm.chutes.ai/v1/models` for current model facts.
- Avoid raw credential-looking values in page copy. Use `CHUTES_API_KEY` or redacted placeholders.
- Label beta and doc-derived integrations clearly.
- Do not imply live Chutes writes, paid deploy calls, or credential reads happened unless a verification record says they did.
