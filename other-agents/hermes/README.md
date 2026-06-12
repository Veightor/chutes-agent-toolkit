# Hermes + Chutes Quickstart

> New to the Chutes API itself? Read the one-page [**Chutes Endpoint Guide**](../../docs/endpoint-guide.md) first — base URLs, `Bearer cpk_` auth, routing, the live model list, and the 25% research endpoint all live there. This page is the Hermes-specific wiring on top of it.

This guide shows the current Hermes-facing Chutes setup in this repo.

Important distinction:
- Hermes upstream v0.16.0 does not ship a first-class `chutes` provider in the installed provider registry.
- Hermes supports named OpenAI-compatible endpoints through the keyed `providers:` config shape and the legacy `custom_providers:` list.
- Hermes also supports stdio/HTTP MCP servers via `hermes mcp add`, so the Chutes MCP server can be used directly as a tool surface.

When live model inventory, pricing, capabilities, or TEE status matter, always use:

`https://llm.chutes.ai/v1/models`

as the source of truth.

## What you need

- Hermes installed and working (`hermes --version`, `hermes doctor`).
- A Chutes API key (`cpk_...`).
- Access to your Hermes config and env files.

Useful commands:

```bash
hermes config path
hermes config env-path
hermes status --all
hermes mcp --help
hermes skills --help
```

Repo-local smoke test:

```bash
python3 scripts/hermes_chutes_doctor.py --emit-config
```

Run it from the repository root before changing a user's Hermes config. It fetches the live public Chutes model catalog, detects Hermes, checks whether `CHUTES_API_KEY` is available without printing the raw key, and emits a safe provider block. Add `--check-auth` only when you intentionally want a read-only `GET /users/me` auth validation.

## Install the Hermes skills

The Hermes skills live in `other-agents/hermes/skills/` and are thin entry points that call the shared scripts under `plugins/chutes-ai/skills/`.

Option A — copy into the active Hermes profile:

```bash
cp -R other-agents/hermes/skills/* ~/.hermes/skills/
hermes skills list
```

Option B — keep this repo as an external skill directory:

```yaml
# ~/.hermes/config.yaml
skills:
  external_dirs:
    - /absolute/path/to/chutes-agent-toolkit/other-agents/hermes/skills
```

Then restart Hermes or start a new session so the skill catalog is reloaded.

Current Hermes skill mirror:

| Skill | Purpose | Status |
|---|---|---|
| `chutes-ai` | Hub: account, API key, model discovery, inference/routing guidance | active |
| `chutes-sign-in` | OAuth 2.0/OIDC/PKCE, OAuth app registration, SIWC vendor flow | BETA for dev-server verification |
| `chutes-routing` | Live model pools, routing strings, aliases, TEE filters | verified live |
| `chutes-usage-and-billing` | Read-only spend, quotas, discounts, exports | verified live |
| `chutes-platform-ops` | OAuth fleet ops, alias ops, token scripts | mixed; token scripts BETA |
| `chutes-deploy` | vLLM/diffusion/custom deploy, teeify, rolling updates | permanent BETA for deploy-side writes |
| `chutes-mcp-portability` | Chutes MCP server and agent config generation | read tools verified; write tools BETA |
| `chutes-agent-registration` | Bittensor-backed Chutes agent registration prep | BETA |
| `chutes-tee` | Evidence fetch, TDX/GPU attestation parsing | shape-valid |

## Configure Chutes as a Hermes custom provider

Put the API key in `~/.hermes/.env`:

```bash
CHUTES_API_KEY=cpk_...
```

Add a named custom provider to `~/.hermes/config.yaml`:

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

Legacy Hermes configs can use the older `custom_providers:` list shape. The local `docs/hermes-chutes-toolkit-guide.md` has the side-by-side config, dynamic model discovery workflow, multi-model provider pattern, Windows install notes, and maintainer verification checklist.

Then start a new Hermes session or run:

```bash
hermes model
```

and select the saved custom provider if you prefer the picker.

Auth note: Chutes auth was re-verified in the shared Chutes skills on 2026-06-11. Use standard bearer authorization semantics (`Authorization: Bearer` plus the `cpk_...` value) for configured providers; `/v1/models` is public and does not prove an auth header works. Older April notes about `X-API-Key` are superseded for Hermes-facing setup.

## Config examples

Checked-in snippets live in `other-agents/hermes/config-examples/`:

- `chutes-basic.yaml` — make Chutes the active model backend.
- `chutes-dual-endpoints.yaml` — normal endpoint plus opt-in research endpoint.
- `chutes-cheap-routing.yaml` — use Chutes as Hermes `smart_model_routing.cheap_model`.
- `chutes-delegation.yaml` — use Chutes for delegated/background subtasks.

Refresh them from the generator:

```bash
python plugins/chutes-ai/skills/chutes-mcp-portability/scripts/generate_agent_config.py \
  --target hermes
```

## Add the Chutes MCP server to Hermes

Install the local stdio MCP server:

```bash
uv tool install chutes-mcp-server \
  --from plugins/chutes-ai/skills/chutes-mcp-portability/mcp-server
```

Register it with Hermes:

```bash
hermes mcp add chutes --command chutes-mcp-server --env CHUTES_API_KEY=${CHUTES_API_KEY}
hermes mcp test chutes
hermes mcp list
```

For MCP targets, also run:

```bash
chutes-mcp-server --self-check
```

The MCP server is the preferred path when you want Chutes management/read tools inside Hermes without relying on the model-provider auth header path.

## Why use two named providers?

### `chutes`

Use for normal inference:
- standard endpoint
- no research recording tradeoff
- safest default for private or sensitive prompts

### `chutes-research`

Use only when the user explicitly accepts the tradeoff:
- lower-cost research endpoint
- prompts and responses may be recorded for research
- do not use for private/sensitive data unless the user clearly opts in

## Recommended model values

- `default:latency` for interactive chat.
- `default:throughput` for long generations, delegated tasks, or background work.
- Concrete model IDs discovered from `/v1/models` when you need a specific context window, feature set, price point, or named model.
- Inline pools like `modelA,modelB,modelC:latency` when a routing skill has built a live pool.

## TEE / privacy usage

When recommending Chutes models for privacy-sensitive use, do not rely on the `-TEE` suffix alone.

Use the live models endpoint and filter for:
- `confidential_compute: true`

For stronger claims, load `chutes-tee` and fetch/parse the chute evidence. Do not claim cryptographic attestation unless DCAP verification actually ran and passed.

## Suggested Hermes workflow

1. Install or externally mount `other-agents/hermes/skills/`.
2. Store `CHUTES_API_KEY` in `~/.hermes/.env` or this repo's keychain credential manager.
3. Add `providers:` config if you want Chutes as a model backend.
4. Add the MCP server if you want Chutes management tools inside Hermes.
5. Use the live models endpoint for current model recommendations.
6. Use `chutes-routing`, `chutes-usage-and-billing`, and `chutes-tee` for deeper work instead of hardcoded static docs.

## Current limitations

- Chutes-specific skills live in this repo, not Hermes core.
- Provider picker UX may show Chutes under saved custom providers rather than built-ins.
- Provider-mode inference may be blocked by auth-header behavior on some Hermes/Chutes combinations; MCP and direct scripts remain available.

## Related docs

- `site/pages/hermes.md` and `site/pages/hermes-recipes.md` — Chutes-site page drafts for promoting Hermes agent use
- `docs/hermes-chutes-toolkit-guide.md`
- `docs/hermes-integration-spec.md`
- `docs/llms-txt-review.md`
- `docs/credential-store.md`
- `plugins/chutes-ai/skills/chutes-mcp-portability/SKILL.md`
