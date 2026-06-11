---
name: chutes-mcp-portability
description: "Make Chutes.ai available to any agent via MCP or OpenAI-compatible configs. Use this skill when the user wants to plug Chutes into Cursor, Cline, Aider, Claude Desktop, Hermes, or another agent. The skill installs the Chutes MCP server (stdio), writes per-agent config snippets, and runs a health check. Triggers on: MCP chutes, chutes MCP server, cursor chutes, cline chutes, aider chutes, claude desktop chutes, hermes chutes provider, openai-compatible chutes, drop-in chutes config, portable chutes, chutes for my agent."
---

# chutes-mcp-portability

> **Status: VERIFIED LIVE 2026-04-13** via `docs/chutes-maxi-wave-2.md` Track C.2 + C.6. `chutes-mcp-server --self-check` passed, and 7 read tools were exercised against a real `cpk_` with non-empty responses.
>
> **Refresh 2026-06-11:** auth headers re-verified live — `Authorization: Bearer cpk_...` now returns 200 on `llm.chutes.ai/v1/models`, on a real paid `POST /v1/chat/completions` (live completion returned), and on `api.chutes.ai/users/me` (the April finding is inverted; see auth note below). The server's inference calls now send Bearer. Catalog re-verified: 13 models, all `-TEE` / `confidential_compute: true`. `chutes-mcp-server --self-check` passed live on 2026-06-11 (run via `uvx` from the local path). That run also caught and fixed a pre-existing packaging bug: `pyproject.toml` declared `readme = "README.md"` which didn't exist, so every `uv tool install --from` build failed with "Readme file does not exist" — `mcp-server/README.md` now exists and the install builds.
>
> **Read tools graduated out of BETA (verified):** `chutes_list_models`, `chutes_get_quota`, `chutes_list_aliases`, `chutes_list_chutes`, `chutes_get_usage`, `chutes_get_discounts`, `chutes_list_api_keys`.
>
> **Read tools still BETA (not exercised through the MCP path):** `chutes_chat_complete` (paid — the underlying `POST /v1/chat/completions` + Bearer auth were live-verified 2026-06-11 via direct curl, but the tool itself has not been exercised through MCP, so the label stays), `chutes_get_evidence` (needs a specific chute_id), `chutes_oauth_introspect` (needs a live OAuth token).
>
> **Write tools — permanent BETA** under the deploy-features policy: `chutes_deploy_vllm`, `chutes_deploy_diffusion`, `chutes_teeify`, `chutes_set_alias`, `chutes_delete_alias`, `chutes_create_api_key`. The `set`/`delete` alias pair was functionally exercised live during wave 2 (round-trip passed) but stays BETA per policy — deploy-side writes always keep the label. MCP tool descriptions prepend `[BETA] ` so clients display it.

## What this skill does

Makes Chutes usable from **any** agent environment with one of two mechanisms:

1. **MCP server** (`mcp-server/server.py`). Stdio transport. Exposes Chutes management + inference as MCP tools. Any MCP-aware client (Claude Desktop, Cursor, Cline, Claude Code itself) can load it.
2. **Config snippets** (`scripts/generate_agent_config.py`). For clients that don't speak MCP but do speak OpenAI-like HTTP. These are now true drop-ins auth-wise — Bearer on a paid `POST /chat/completions` was live-verified 2026-06-11 — but each snippet stays [BETA] until a completion round-trip is exercised through that specific client.

Both paths read secrets from the keychain via `manage_credentials.py` and never echo `cpk_` into transcripts.

Live auth finding (re-verified 2026-06-11 — this **inverts** the wave-3 2026-04-15 finding):
- `Authorization: Bearer cpk_...` → 200 on `GET llm.chutes.ai/v1/models`, on a real paid `POST llm.chutes.ai/v1/chat/completions` (live completion returned), AND on `GET api.chutes.ai/users/me`. Bearer is the platform-recommended header per chutes.ai's own `ai-plugin.json` and `llms.txt`.
- `X-API-Key: cpk_...` → 200 on `GET /v1/models` (which is now public, so this proves little) but **401 on `api.chutes.ai/users/me`**. On the inference surface it is **confirmed silently ignored** (live 2026-06-11): a completion POST with it got the anonymous nginx 429, byte-identical to a fully unauthenticated POST, while Bearer succeeded in the same minute. Do not use it.
- `GET /v1/models` requires no auth at all.
- The fingerprint→JWT flow (`POST /users/login`) is still what the MCP server uses for management writes; Bearer-cpk behavior on management writes is unverified as of 2026-06-11.

The MCP server in this repo now sends Bearer on the inference surface and keeps the fingerprint→JWT path for management tools.

## Supported targets

| Target | Mechanism | Notes |
|---|---|---|
| Claude Desktop | MCP | Writes to `~/Library/Application Support/Claude/claude_desktop_config.json` (macOS path; shown for other OSes). Claude Desktop also supports one-click MCP Bundles (`.mcpb`) for local servers — not packaged here yet (unverified as of 2026-06-11) |
| Claude Code | MCP | `claude mcp add` equivalent or direct config snippet |
| Cursor | MCP | `.cursor/mcp.json` at the workspace root (or `~/.cursor/mcp.json` for global) |
| Cline | MCP | Global `cline_mcp_settings.json` via Cline's MCP Servers → Configure UI (not VS Code `settings.json`) |
| Aider | OpenAI-compat | `~/.aider.conf.yml` with `openai-api-base` + model allowlist |
| Hermes | OpenAI-compat + MCP | Refreshes `other-agents/hermes/config-examples/*.yaml`; Hermes can also add the stdio MCP server with `hermes mcp add chutes --command chutes-mcp-server` |
| Generic OpenAI SDK | OpenAI-compat | Prints an env var block |
| System-prompt agents | prompt | Writes a paste-able instruction block to `other-agents/system-prompt/` |

## Walkthrough

### Step 1 — pick targets

Ask the user which targets to configure. Multi-select is normal ("Cursor and Aider").

### Step 2 — install the MCP server (for MCP targets only)

```bash
uv tool install chutes-mcp-server --from plugins/chutes-ai/skills/chutes-mcp-portability/mcp-server
# or:
pipx install plugins/chutes-ai/skills/chutes-mcp-portability/mcp-server
```

This gives the user a `chutes-mcp-server` command on PATH. **Local-path install only:** `chutes-mcp-server` is NOT published on PyPI (404 verified 2026-06-11), so the `--from <local path>` form is required — a bare `uv tool install chutes-mcp-server` will fail. (Fixed 2026-06-11: the `--from` build itself used to fail with "Readme file does not exist" because `pyproject.toml` declared a `README.md` that wasn't checked in; the README now exists.) The command reads `CHUTES_API_KEY` from env or falls back to `manage_credentials.py get --field api_key` for inference (sent as `Authorization: Bearer`). For management tools, it uses `CHUTES_FINGERPRINT` or the stored fingerprint to mint a short-lived JWT via `POST /users/login`.

### Step 3 — generate configs

```bash
python <skill-scripts-dir>/generate_agent_config.py --target cursor,aider,hermes
```

`--target` accepts a comma-separated list. For each target, the script:

- Reads `cpk_` from the keychain to inject into env-var-style targets.
- Writes config files to each target's conventional location or, for Hermes, refreshes the checked-in examples in `other-agents/hermes/config-examples/`.
- Prints next-step commands (restart the client, reload window, etc.).

### Step 4 — health check

For MCP targets:

```bash
chutes-mcp-server --self-check
```

Runs `chutes_list_models` with `limit=1` against the live Chutes API over stdio transport. Prints OK + the first model id on success. This is the verification step that graduates read-only MCP tools out of BETA. Last passed live 2026-06-11 (via `uvx` from the local path).

For OpenAI-compat targets, the script prints a one-liner `curl https://llm.chutes.ai/v1/models` that the user can run themselves.

## MCP tool surface

| Tool | Endpoint | Label |
|---|---|---|
| `chutes_list_models` | `GET https://llm.chutes.ai/v1/models` | read |
| `chutes_chat_complete` | `POST https://llm.chutes.ai/v1/chat/completions` (streaming) | read |
| `chutes_list_chutes` | `GET /chutes/` | read |
| `chutes_deploy_vllm` | `POST /chutes/vllm` | **[BETA]** write |
| `chutes_deploy_diffusion` | `POST /chutes/diffusion` | **[BETA]** write |
| `chutes_teeify` | `PUT /chutes/{id}/teeify` | **[BETA]** write — endpoint GONE from openapi as of 2026-06-11; use `tee=True` at deploy time instead |
| `chutes_list_aliases` | `GET /model_aliases/` | read |
| `chutes_set_alias` | `POST /model_aliases/` | **[BETA]** write |
| `chutes_delete_alias` | `DELETE /model_aliases/{alias}` | **[BETA]** write |
| `chutes_get_usage` | `GET /invocations/usage` | read |
| `chutes_get_quota` | `GET /users/me/quotas` | read |
| `chutes_get_discounts` | `GET /users/me/discounts` | read |
| `chutes_get_evidence` | `GET /chutes/{id}/evidence?nonce=<64 hex chars>` (nonce required; auto-generated) | read |
| `chutes_oauth_introspect` | `POST /idp/token/introspect` | read |
| `chutes_list_api_keys` | `GET /api_keys/` | read |
| `chutes_create_api_key` | `POST /api_keys/` | **[BETA]** write |

Write tools prepend `[BETA] ` to the tool description string so the MCP client shows the label in the tool picker.

## Files in this skill

```
chutes-mcp-portability/
├── SKILL.md                          (this file)
├── references/
│   ├── mcp-tool-map.md               endpoint → MCP tool mapping
│   ├── cursor-setup.md
│   ├── cline-setup.md
│   ├── aider-setup.md
│   └── openrouter-style.md
├── mcp-server/
│   ├── server.py                     FastMCP stdio server
│   └── pyproject.toml                uv / pipx install manifest
└── scripts/
    └── generate_agent_config.py      per-target config emitter
```

## Safety rules

- **Never write a raw `cpk_` into a generated config file.** Prefer env-var references (`${CHUTES_API_KEY}`) that the client resolves at runtime. If a target absolutely requires an inline key, warn loudly.
- **MCP tools never return `cpk_` through results.** The server reads the key at boot and uses it internally only.
- **Write tools require BETA label.** Do not remove the `[BETA] ` prefix from a write tool's description without a recorded verification run that exercised it.
- **Health check is not optional.** A skill completion without a successful health check stays BETA.

## Related skills

- `chutes-ai` (hub) — prerequisite credential setup.
- `chutes-deploy` **[BETA]** — write tools map 1:1 to deploy scripts; use the skill when the user wants an interactive walkthrough, use MCP when another agent needs programmatic access.
- `chutes-sign-in` **[BETA]** — `chutes_oauth_introspect` is the MCP-exposed form of the SIWC verify step.
