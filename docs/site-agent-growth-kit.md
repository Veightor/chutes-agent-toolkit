# Chutes Agent Growth Kit

This page is source material for Chutes site builders. It is not the website repo. Use it to publish "Run agents on Chutes" pages backed by checked-in docs, structured data, and demo prompts from this toolkit.

Source assets:

- Site/demo data: `data/agent-use-cases.json`
- Generator: `scripts/build_agent_site_pack.py`
- Site page drafts: `site/README.md` and `site/pages/`
- Runnable examples: `cookbook/README.md`
- Model picker logic: `scripts/pick_model.py`
- Codex guide: `other-agents/codex/README.md`
- Universal endpoint guide: `docs/endpoint-guide.md`
- Live catalog source: `https://llm.chutes.ai/v1/models`

Generate the site pack:

```bash
python3 scripts/build_agent_site_pack.py --format markdown
python3 scripts/build_agent_site_pack.py --focus codex --format json
```

## Run Codex on Chutes

Page angle: coding agents already speak the OpenAI API. Chutes gives those agents an OpenAI-compatible inference endpoint for open-source models, with Bearer auth and routing in the `model` field.

Copy block and demo prompt: generate from `data/agent-use-cases.json` (id `codex`) via `scripts/build_agent_site_pack.py --focus codex` — do not hand-copy them here. Note that `default:*` routing aliases require a pool configured once at chutes.ai/app → Model Routing; a concrete model ID from the live `/v1/models` catalog works with zero setup.

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
- Use `site/pages/` for page drafts; order client paths by depth of in-repo support, and present every client with parity.

## Routing, cost control, and private inference

Page angle: agent traffic is mixed. Interactive coding, review, planning, summarization, and background tasks should not all use the same static model ID.

Copy block:

Chutes routing lets agents choose a policy in the `model` string. Use a comma-separated pool with a strategy suffix for explicit failover, or — after configuring a pool once at chutes.ai/app → Model Routing — `default:latency` for interactive work and `default:throughput` for longer background generations. When a workflow needs a specific context window, modality, tool support, JSON mode, or price point, fetch `https://llm.chutes.ai/v1/models` and choose from current metadata.

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

Use demos that prove agent value and Chutes-specific behavior without needing live writes, paid deploys, or credential reads. The canonical demo prompts are the `demo_prompt` fields in `data/agent-use-cases.json` — render them with `scripts/build_agent_site_pack.py` rather than copying them into page copy. Why each one earns its slot:

- **Repository repair** (`codex`): shows the coding-agent workflow, Chutes as OpenAI-compatible inference, and secret-safe setup.
- **SDK port** (`openai-sdk-agents`): shows that moving an existing OpenAI SDK agent to Chutes is a base-URL/key/model change, nothing more.
- **Skill-suite onboarding** (`claude`): shows install-to-routing-recommendation inside an assistant workflow.
- **MCP editor-agent setup** (`cursor-cline-aider-mcp`): shows editor-agent distribution through a concrete toolkit path.
- **Channel agent provider swap** (`openclaw-channel-agents`): connects OpenAI-compatible setup, routing, and privacy tradeoffs.

Two extra demo angles worth scripting that are not yet in the JSON: a routing preset picker (when to use `default:latency` vs `default:throughput` vs a concrete live ID) and a TEE-safe copy audit (explain `confidential_compute` benefits without claiming attestation unless DCAP verification ran).

## Publishing Checklist

- Present every client integration with parity; order by depth of in-repo support (Claude → Hermes → editor/MCP clients → OpenClaw → Codex/generic OpenAI-compatible).
- Use `data/agent-use-cases.json` for page cards and demo prompts.
- Generate Markdown or JSON with `scripts/build_agent_site_pack.py` rather than hand-copying tables.
- Keep `site/pages/connect-your-agent.md` aligned with the ordering rationale in its own build notes.
- Keep code snippets backed by `cookbook/` examples and model-choice UI backed by `scripts/pick_model.py`.
- Link to `https://llm.chutes.ai/v1/models` for current model facts.
- Avoid real-looking credentials in page copy. Use `CHUTES_API_KEY` or the `cpk_...` format placeholder.
- Label beta and doc-derived integrations clearly.
- Do not imply live Chutes writes, paid deploy calls, or credential reads happened unless a verification record says they did.
