# Page draft: `chutes.ai/agents/hermes` — "Run Hermes on Chutes"

> Status: draft copy for the Chutes site. Facts should be refreshed from `GET https://llm.chutes.ai/v1/models` before publication. This page is Hermes-specific and links back to the implementation package in `chutes-agent-toolkit`.

---

## Hero

# Give Hermes a private open-model backend.

Hermes already knows how to run tools, skills, MCP servers, cron jobs, and delegated agents. Chutes gives it OpenAI-compatible inference on frontier open-source models, with the current hosted catalog running under `confidential_compute: true` inside TEEs.

Change the base URL, keep the OpenAI API, and let Hermes route work across Chutes models.

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

**Primary CTA:** Get a Chutes key  
**Secondary CTA:** Open the Hermes toolkit on GitHub

---

## Why Hermes builders should care

### 1. Hermes can use Chutes today

No fork required. Hermes supports named OpenAI-compatible providers. Put `CHUTES_API_KEY` in `~/.hermes/.env`, add a `providers.chutes` entry, and choose `custom:chutes` in Hermes.

### 2. Keep orchestration premium; move loops to Chutes

Use your usual primary model for planning and high-stakes orchestration, then send delegated/background work to Chutes:

```yaml
delegation:
  provider: custom:chutes
  model: default:throughput
  reasoning_effort: medium
```

That gives Hermes a cheap, private worker lane for summarization, extraction, classification, batch code review, and long-running cron reports.

### 3. Chutes is also a Hermes tool surface

Provider mode answers with Chutes models. MCP mode gives Hermes Chutes tools: list models, inspect quotas, read usage, list aliases, fetch TEE evidence, and more.

```bash
uv tool install chutes-mcp-server \
  --from plugins/chutes-ai/skills/chutes-mcp-portability/mcp-server

hermes mcp add chutes --command chutes-mcp-server --env CHUTES_API_KEY=${CHUTES_API_KEY}
hermes mcp test chutes
```

### 4. Privacy is a default, not an add-on

The live model object exposes `confidential_compute`. For private tasks, filter on that boolean, not just the `-TEE` suffix. For stronger claims, use the toolkit's `chutes-tee` skill to fetch and parse evidence. Do not claim cryptographic attestation unless the verification path actually ran and passed.

---

## 60-second setup

```bash
# 1. Install/check Hermes
hermes --version
hermes doctor

# 2. Store the key outside config
hermes config env-path
$EDITOR "$(hermes config env-path)"  # add CHUTES_API_KEY on its own line

# 3. Run the local smoke test from this repo
python3 scripts/hermes_chutes_doctor.py --emit-config

# 4. Paste the provider block into ~/.hermes/config.yaml
hermes model
```

The doctor script fetches the live model catalog, detects Hermes, finds whether a Chutes key is configured, and prints a safe config block. It never prints the raw key. Auth validation is opt-in with `--check-auth`.

---

## Live model strip

Render this from `GET https://llm.chutes.ai/v1/models` at build time or client side:

- models returned
- `confidential_compute=true` count
- models advertising `tools`
- models advertising `json_mode`
- models advertising `structured_outputs`
- image-capable models
- cheapest model advertising tools
- longest-context model

Copy suggestion:

> "Hermes can discover the Chutes catalog live. Today's catalog is TEE-backed, OpenAI-compatible, and routeable through `default:latency` or `default:throughput`."

If `supported_features` is null on a model, do not treat that as a hard negative for every capability. For production claims, verify critical features with a minimal request.

---

## Demo prompts for Hermes

After setup, these are good first-run prompts:

- "Use the Chutes model list to recommend a private tool-calling model for a Hermes coding agent."
- "Set up Chutes as my Hermes cheap_model for simple delegated tasks."
- "Create a TEE-only routing pool for interactive Hermes chat and explain the privacy tradeoffs."
- "Check my Chutes quota and summarize whether I can run a nightly extraction cron job."
- "Fetch Chutes TEE evidence and tell me whether the result is shape-valid or cryptographically verified."

---

## Page sections for design

1. Hero with YAML provider block.
2. Three cards: Provider, MCP, Delegation.
3. Live model strip from `/v1/models`.
4. Doctor script terminal output mock.
5. Privacy/TEE explanation with a link to `/agents/private`.
6. Recipe cards linking to `/agents/hermes/recipes`.
7. CTA: GitHub toolkit, endpoint guide, Hermes docs.

---

## Links

- Hermes toolkit guide: `docs/hermes-chutes-toolkit-guide.md`
- Hermes quickstart: `other-agents/hermes/README.md`
- Config examples: `other-agents/hermes/config-examples/`
- Local doctor: `scripts/hermes_chutes_doctor.py`
- Universal endpoint guide: `docs/endpoint-guide.md`

---

## Build notes, not page copy

- Never put a raw `cpk_` key in page snippets. Use `CHUTES_API_KEY` and `key_env`.
- Keep normal endpoint and research endpoint as separate providers.
- Render live model facts from `/v1/models`; do not let model counts or prices drift into stale copy.
- The provider config shown here matches the repo's Hermes v0.16 custom-provider path. Re-check `other-agents/hermes/README.md` before shipping.
- If the Chutes site adds a config generator, reuse the same shape emitted by `scripts/hermes_chutes_doctor.py --emit-config`.
