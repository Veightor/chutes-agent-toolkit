# Hermes + Chutes Toolkit Guide

This is the local, repo-owned Hermes guide for the Chutes Agent Toolkit. It is written for this repository's current skills, config examples, scripts, and live Chutes/Hermes behavior.

## Mental model

```text
Hermes Agent
  -> named provider: custom:chutes
  -> https://llm.chutes.ai/v1
  -> CHUTES_API_KEY from ~/.hermes/.env
  -> routing aliases or concrete model IDs from /v1/models

Hermes Agent
  -> MCP server: chutes-mcp-server
  -> Chutes management/read tools
  -> shared scripts under plugins/chutes-ai/skills/
```

Use the provider path when Hermes should run on Chutes models. Use the MCP path when Hermes needs Chutes tools such as model listing, quota/usage reads, aliases, chutes, API-key reads, or attestation evidence.

## 1. Install and verify Hermes

macOS/Linux:

```bash
curl -fsSL https://raw.githubusercontent.com/NousResearch/hermes-agent/main/scripts/install.sh | bash
hermes setup
hermes doctor
```

Windows PowerShell:

```powershell
iex (irm https://raw.githubusercontent.com/NousResearch/hermes-agent/main/scripts/install.ps1)
```

After a Windows install, open a new terminal so the PATH update is visible, then run:

```powershell
hermes --version
hermes setup
hermes doctor
```

Useful Hermes commands on every platform:

```bash
hermes config path
hermes config env-path
hermes model
hermes status --all
hermes tools list
hermes mcp --help
hermes skills --help
```

## 2. Store the Chutes key outside config

Chutes API keys start with `cpk_`. Never commit a real key to this repo, screenshots, config examples, or chat transcripts.

Find the Hermes env file:

```bash
hermes config env-path
```

Add the key to that file:

```bash
CHUTES_API_KEY=***
```

Default locations:

| Platform | Hermes env file |
|---|---|
| macOS/Linux | `~/.hermes/.env` |
| Windows native | `%USERPROFILE%\.hermes\.env` |

Restart Hermes or open a fresh Hermes session after changing env/config files.

## 3. Install or mount the Hermes skills

The Hermes-specific skill mirror lives at:

```text
other-agents/hermes/skills/
```

Those skills are thin Hermes entry points. Shared scripts and deep references remain under:

```text
plugins/chutes-ai/skills/
```

Copy the skills into your active Hermes profile:

```bash
cp -R other-agents/hermes/skills/* ~/.hermes/skills/
hermes skills list
```

Or mount this repo as an external skill directory:

```yaml
# ~/.hermes/config.yaml
skills:
  external_dirs:
    - /absolute/path/to/chutes-agent-toolkit/other-agents/hermes/skills
```

Restart Hermes so the skill catalog is reloaded.

## 4. Discover live Chutes models

Model inventory is dynamic. Always query the live endpoint when availability, context, pricing, tool support, JSON support, or TEE status matters:

```text
GET https://llm.chutes.ai/v1/models
```

Quick dependency-free Python:

```bash
python3 - <<'PY'
import json, urllib.request
with urllib.request.urlopen('https://llm.chutes.ai/v1/models', timeout=30) as r:
    payload = json.load(r)
for model in payload['data'][:20]:
    print(model['id'], model.get('context_length'), model.get('pricing', {}), 'tee=', model.get('confidential_compute'))
PY
```

Model fields to inspect defensively:

- `id` — model string used in Hermes config or API requests.
- `context_length` / `max_model_len` — context window signals.
- `max_output_length` — output cap when exposed.
- `pricing.prompt`, `pricing.completion`, `pricing.input_cache_read` — USD per 1M tokens when present.
- `supported_features` — `tools`, `json_mode`, `structured_outputs`, reasoning features, etc.
- `supported_sampling_parameters` — `temperature`, `top_p`, `max_tokens`, and related sampling controls.
- `input_modalities`, `output_modalities` — modality support.
- `confidential_compute` — authoritative TEE/privacy flag.

Decision tree:

1. Need latest availability? Query `/v1/models`.
2. Need privacy? Require `confidential_compute == true`.
3. Need tool/function calls? Require `tools` in `supported_features`.
4. Need JSON or structured output? Look for `json_mode` or `structured_outputs`.
5. Need long context? Sort/filter by `context_length` or `max_model_len`.
6. Need cheap batch work? Sort/filter by prompt/completion pricing.
7. Need interactive speed? Start with `default:latency` or a live low-latency recommendation.
8. Need background/delegated throughput? Start with `default:throughput`.

## 4a. Run the Hermes + Chutes doctor

Before editing user config, run the repo-local smoke test:

```bash
python3 scripts/hermes_chutes_doctor.py
python3 scripts/hermes_chutes_doctor.py --emit-config
```

It checks the local Hermes CLI, finds whether `CHUTES_API_KEY` is configured without printing the raw key, fetches the live public model catalog, summarizes Hermes-relevant capabilities, and can emit the provider YAML used in this guide. Auth validation is intentionally opt-in:

```bash
python3 scripts/hermes_chutes_doctor.py --check-auth
```

Use `--json` when wiring the same checks into a Chutes-site widget or CI helper.

## 5. Configure Chutes as a Hermes provider

Edit the Hermes config:

```bash
hermes config edit
```

Preferred current shape:

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
      default: {}
      "default:latency": {}
      "default:throughput": {}

model:
  provider: custom:chutes
  default: default:latency
```

Legacy-compatible shape for older Hermes configs:

```yaml
custom_providers:
  - name: chutes
    base_url: https://llm.chutes.ai/v1
    key_env: CHUTES_API_KEY
    api_mode: chat_completions
    model: default:latency
    discover_models: true
    models:
      default: {}
      "default:latency": {}
      "default:throughput": {}

model:
  provider: custom:chutes
  default: default:latency
```

Do not put the raw API key in either block. Use `key_env: CHUTES_API_KEY`.

Refresh this repo's checked-in examples with:

```bash
python3 plugins/chutes-ai/skills/chutes-mcp-portability/scripts/generate_agent_config.py --target hermes
```

The generated examples live in:

```text
other-agents/hermes/config-examples/
```

## 6. Use one key with many models

Use one `providers.chutes` entry when the base URL and API key are the same and only the model changes.

You can keep the base routing aliases plus concrete live model IDs:

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
      default: {}
      "default:latency": {}
      "default:throughput": {}
      Qwen/Qwen3-32B-TEE: {}
      google/gemma-4-31B-turbo-TEE: {}
      deepseek-ai/DeepSeek-V3.2-TEE: {}
```

Use multiple provider entries only when something materially differs, such as:

- normal endpoint vs research opt-in endpoint;
- different API keys for teams, budgets, or environments;
- different base URL, auth, transport, or policy.

## 7. Keep research opt-in separate

The research endpoint has different privacy tradeoffs. Keep it as a separate named provider so users do not accidentally route private prompts there.

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
      default: {}
      "default:latency": {}
      "default:throughput": {}

  chutes-research:
    name: Chutes Research Opt-In
    base_url: https://research-data-opt-in-proxy.chutes.ai/v1
    key_env: CHUTES_API_KEY
    transport: chat_completions
    default_model: default:latency
    discover_models: true
    models:
      default: {}
      "default:latency": {}
      "default:throughput": {}
```

Use `chutes-research` only when the user explicitly accepts prompt/response recording for research. Do not use it for private, sensitive, or regulated data.

## 8. Select and test in Hermes

After editing config/env, start a fresh Hermes session and run:

```bash
hermes model
```

Select the saved Chutes custom provider and one of its models.

If your Hermes build supports one-off provider/model overrides, test with:

```bash
hermes chat --provider custom:chutes --model default:latency -q "Say hello from Chutes."
```

If the provider slug differs, choose Chutes interactively with `hermes model`, then inspect what Hermes saved in `hermes config path`.

## 9. Add Chutes MCP tools to Hermes

Install the local stdio MCP server from this repo:

```bash
uv tool install chutes-mcp-server \
  --from plugins/chutes-ai/skills/chutes-mcp-portability/mcp-server
```

Register and test it:

```bash
hermes mcp add chutes --command chutes-mcp-server --env CHUTES_API_KEY=${CHUTES_API_KEY}
hermes mcp test chutes
hermes mcp list
chutes-mcp-server --self-check
```

Use MCP tools alongside provider config. Provider config answers with Chutes models; MCP tools inspect or operate Chutes resources.

## 10. Delegation and cheap routing patterns

Use your normal primary model for orchestration and Chutes for delegated/background tasks:

```yaml
delegation:
  provider: custom:chutes
  model: default:throughput
  reasoning_effort: medium
```

Use Chutes for cheap/simple routing while keeping another primary model:

```yaml
smart_model_routing:
  enabled: true
  cheap_model:
    provider: custom:chutes
    model: default:latency
```

The full examples are:

- `other-agents/hermes/config-examples/chutes-delegation.yaml`
- `other-agents/hermes/config-examples/chutes-cheap-routing.yaml`

## 11. Agent rules for this toolkit

When an agent works on Hermes + Chutes in this repo, it should follow these rules:

1. Use Hermes docs/CLI for Hermes mechanics, but keep Chutes-specific reusable docs in this repo.
2. Treat `https://llm.chutes.ai/v1/models` as the source of truth for model inventory and metadata.
3. Never commit real `cpk_...`, `cid_...`, or `csc_...` secrets.
4. Prefer `CHUTES_API_KEY` in `~/.hermes/.env` and `key_env: CHUTES_API_KEY` in YAML.
5. Keep normal and research endpoints as separate providers.
6. For privacy-sensitive tasks, require `confidential_compute: true`; do not rely only on a `-TEE` suffix.
7. For cryptographic TEE claims, use the `chutes-tee` skill and state whether verification was only shape-valid or fully cryptographic.
8. Do not hardcode stale model recommendations when the live endpoint can be queried.
9. Verify edited YAML parses and that Hermes can parse the provider entries.
10. Use `uv run --with pytest --with cryptography pytest ...` if local `pytest` is unavailable.

## 12. Troubleshooting

| Symptom | Check |
|---|---|
| `hermes` not found on Windows after install | Open a new terminal, or run `%LOCALAPPDATA%\hermes\bin\hermes.cmd` once. |
| Chutes provider not shown | Restart Hermes, run `hermes model`, inspect `hermes config path`, and verify the provider key is `chutes`. |
| Model ID fails | Query `/v1/models`; model names and availability change. |
| Need private routing | Filter live models for `confidential_compute: true`, then use `chutes-tee` if evidence matters. |
| Need tools/function calling | Filter `supported_features` for `tools`; don't assume every model supports tools. |
| Need JSON/structured outputs | Inspect `supported_features` and `supported_sampling_parameters` first. |
| MCP server not found | Install with `uv tool install chutes-mcp-server --from plugins/chutes-ai/skills/chutes-mcp-portability/mcp-server` from this repo. |
| `pytest` missing | Run `uv run --with pytest --with cryptography pytest ...`. |

## 13. Verification commands for maintainers

Run these before claiming Hermes assets are current:

```bash
python3 scripts/hermes_chutes_doctor.py
python3 plugins/chutes-ai/skills/chutes-mcp-portability/scripts/generate_agent_config.py --target hermes

python3 - <<'PY'
from pathlib import Path
import yaml
for p in Path('other-agents/hermes/config-examples').glob('*.yaml'):
    yaml.safe_load(p.read_text())
for p in Path('other-agents/hermes/skills').glob('*/SKILL.md'):
    text = p.read_text()
    end = text.find('\n---\n', 4)
    yaml.safe_load(text[4:end])
print('Hermes YAML and skill frontmatter OK')
PY

PYTHONPATH=$HOME/.hermes/hermes-agent $HOME/.hermes/hermes-agent/venv/bin/python - <<'PY'
from pathlib import Path
import yaml
from hermes_cli.config import get_compatible_custom_providers
for p in sorted(Path('other-agents/hermes/config-examples').glob('*.yaml')):
    cfg = yaml.safe_load(p.read_text()) or {}
    providers = get_compatible_custom_providers(cfg)
    if not providers:
        raise SystemExit(f'no Hermes providers parsed from {p}')
    print('hermes parsed', p.name, [x.get('provider_key') for x in providers])
PY

uv run --with pytest --with cryptography pytest tests/test_run_evals.py tests/test_manage_credentials.py
git diff --check
```
