# MCP Tool Map **[BETA]**

> Source of truth: `mcp-server/server.py` in this skill. Update both sides when you add a tool.

## Why this map exists

MCP clients discover tools dynamically, but agents benefit from a flat human-readable map when deciding which tool to call. This doc mirrors the server's `@app.tool()` decorators so humans and LLMs can pick the right one without reading Python.

## Read tools (graduate individually after verified calls)

| Tool | Endpoint | Typical use |
|---|---|---|
| `chutes_list_models` | `GET https://llm.chutes.ai/v1/models` | "What models are available?" |
| `chutes_chat_complete` | `POST https://llm.chutes.ai/v1/chat/completions` | Single-shot chat call |
| `chutes_list_chutes` | `GET /chutes/` | "What have I deployed?" |
| `chutes_list_aliases` | `GET /model_aliases/` | "What stable handles exist?" |
| `chutes_get_usage` | `GET /invocations/usage` | "How much have I spent?" |
| `chutes_get_quota` | `GET /users/me/quotas` | "What are my quotas?" |
| `chutes_get_discounts` | `GET /users/me/discounts` | "Am I getting a discount?" |
| `chutes_get_evidence` | `GET /chutes/{id}/evidence` | "Show me TEE evidence for this chute" |
| `chutes_oauth_introspect` | `POST /idp/token/introspect` | "Is this SIWC token active?" |
| `chutes_list_api_keys` | `GET /api_keys/` | "What API keys exist on my account?" |

## Write tools (permanent BETA under deploy-features policy)

All write tools prepend `[BETA] ` to their tool description string so MCP clients display the label prominently.

| Tool | Endpoint | Why BETA |
|---|---|---|
| `chutes_deploy_vllm` | `POST /chutes/vllm` | Deploy — consumes paid compute |
| `chutes_deploy_diffusion` | `POST /chutes/diffusion` | Deploy — consumes paid compute |
| `chutes_teeify` | `PUT /chutes/{id}/teeify` | Creates a new TEE variant — hard to reverse |
| `chutes_set_alias` | `POST /model_aliases/` | Mutates team routing policy |
| `chutes_delete_alias` | `DELETE /model_aliases/{alias}` | Removes team routing policy |
| `chutes_create_api_key` | `POST /api_keys/` | Secret material creation |

## Graduation rule

A read tool loses its BETA label only after a commit that:

1. References a recorded verified call (transcript, test output, or eval pass).
2. Updates this file to remove `[BETA]` from its row.
3. Updates the `BETA_PREFIX` logic in `server.py` if the graduation requires changing the tool description.

Write tools stay BETA until the broader deploy-features policy changes — they do not graduate individually.
