# Page draft: `chutes.ai/agents/hermes/recipes` — "Hermes + Chutes recipes"

> Status: draft copy for the Chutes site. Use as cards, accordions, or short docs beneath the Hermes landing page. Keep deep implementation details in the GitHub toolkit.

---

## Intro

# Recipes for running Hermes on Chutes

Use these when you want more than a basic completion: private coding loops, delegated workers, MCP tools, cost-aware routing, research opt-in, and TEE evidence.

Each recipe follows the same rule: Chutes is OpenAI-compatible at `https://llm.chutes.ai/v1`, and Hermes should read the key from `CHUTES_API_KEY`.

---

## Recipe 1: Make Chutes the active Hermes model backend

**Use when:** You want the whole Hermes session to answer from Chutes.

```yaml
providers:
  chutes:
    name: Chutes
    base_url: https://llm.chutes.ai/v1
    key_env: CHUTES_API_KEY
    transport: chat_completions
    default_model: default:latency
    discover_models: true
    models:
      "default": {}
      "default:latency": {}
      "default:throughput": {}

model:
  provider: custom:chutes
  default: default:latency
```

**Verify:**

```bash
python3 scripts/hermes_chutes_doctor.py --emit-config
hermes model
```

**Site note:** render a "copy config" button, but never ask users to paste the raw key into YAML.

---

## Recipe 2: Use Chutes as a private delegation lane

**Use when:** Your main model should orchestrate, but delegated subtasks should run on Chutes.

```yaml
providers:
  chutes:
    name: Chutes
    base_url: https://llm.chutes.ai/v1
    key_env: CHUTES_API_KEY
    transport: chat_completions
    default_model: default:throughput
    discover_models: true
    models:
      "default": {}
      "default:latency": {}
      "default:throughput": {}

delegation:
  provider: custom:chutes
  model: default:throughput
  reasoning_effort: medium
```

**Good for:** summarization, issue triage, data extraction, build-log analysis, low-risk code review, nightly reports.

**Caveat:** delegated agents need the same tool boundaries and secret hygiene as the parent session.

---

## Recipe 3: Add Chutes tools through MCP

**Use when:** Hermes should inspect Chutes resources, not just call Chutes as a model.

```bash
uv tool install chutes-mcp-server \
  --from plugins/chutes-ai/skills/chutes-mcp-portability/mcp-server

hermes mcp add chutes --command chutes-mcp-server --env CHUTES_API_KEY=${CHUTES_API_KEY}
hermes mcp test chutes
hermes mcp list
```

**What this unlocks:** model listing, quota reads, usage reads, alias reads, chute listing, API key reads, and TEE evidence tools. Some write/deploy tools stay beta; keep those labels visible.

---

## Recipe 4: Let Hermes route simple work cheaply

**Use when:** Another provider remains primary, but cheap/simple tasks should go to Chutes.

```yaml
smart_model_routing:
  enabled: true
  cheap_model:
    provider: custom:chutes
    model: default:latency
```

**Copy block:**

> "Keep your premium model for hard decisions; route low-risk helper turns to Chutes."

---

## Recipe 5: Use research opt-in only for safe workloads

**Use when:** You want the lower-cost research endpoint and the workload contains no private, sensitive, or regulated data.

```yaml
providers:
  chutes-research:
    name: Chutes Research Opt-In
    base_url: https://research-data-opt-in-proxy.chutes.ai/v1
    key_env: CHUTES_API_KEY
    transport: chat_completions
    default_model: default:latency
    discover_models: true
    models:
      "default": {}
      "default:latency": {}
      "default:throughput": {}
```

**Warning copy:** prompts and responses may be recorded for research. Use this for public-data evals, synthetic data, and non-sensitive batch work. Do not make it the silent default.

---

## Recipe 6: Build a privacy-first Hermes workflow

**Use when:** The user asks for private agent execution or TEE-backed inference.

1. Query the live model list.
2. Filter for `confidential_compute: true`.
3. Prefer routing aliases only when the alias policy is known to stay TEE-only.
4. If the answer needs evidence, load the `chutes-tee` skill and fetch evidence.
5. State the verification level: metadata-only, shape-valid evidence, or cryptographic verification.

**Site widget idea:** a privacy checklist that turns green only when the selected model has `confidential_compute: true` and links to the evidence docs.

---

## Recipe 7: Pick a model from live metadata

**Use when:** The user needs a concrete model for tools, JSON, vision, or long context.

Decision tree:

1. Need latest availability? `GET https://llm.chutes.ai/v1/models`.
2. Need tools? Prefer models whose `supported_features` includes `tools`; verify with a minimal tool-call request for critical paths.
3. Need JSON/schema? Prefer `json_mode` or `structured_outputs`.
4. Need vision? Require `image` in `input_modalities`.
5. Need private? Require `confidential_compute: true`.
6. Need cheap loops? Sort by `pricing.prompt + pricing.completion`.
7. Need broad context? Sort by `context_length` or `max_model_len`.

**Local helper:**

```bash
python3 scripts/hermes_chutes_doctor.py --json
```

---

## Troubleshooting card

| Symptom | Likely cause | Fix |
|---|---|---|
| `200` from `/v1/models`, completions fail | `/v1/models` is public and did not validate your key | Run `python3 scripts/hermes_chutes_doctor.py --check-auth` |
| Hermes config works but model choice fails | Stale concrete model ID | Use `default:latency` or refresh from `/v1/models` |
| Tool call ignored | Model metadata does not advertise tools, or feature support needs live verification | Pick a tool-capable model and run a minimal tool-call test |
| Private-data concern | Research endpoint or non-TEE assumption | Use normal endpoint and require `confidential_compute: true` |
| MCP command not found | MCP server not installed in PATH | Run the `uv tool install ... --from .../mcp-server` command from this repo |

---

## Build notes, not page copy

- Turn each recipe into a card with a "copy" button and a "deep guide" link.
- Keep the warning language on research opt-in visible near any lower-cost claim.
- Put live model facts behind an API-driven component; do not bake current model count/prices into page HTML.
- Link to `scripts/hermes_chutes_doctor.py` as the page's proof artifact.
- Keep beta labels for deploy/write MCP flows until the repo verification policy graduates them.
