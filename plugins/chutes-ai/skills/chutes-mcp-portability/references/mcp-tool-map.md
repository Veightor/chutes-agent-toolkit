# MCP Tool Map

> Source of truth: `mcp-server/server.py` in this skill. Update both sides when you add a tool.
>
> **Live verification status (2026-04-13):** 7 read tools verified live; see `docs/chutes-maxi-wave-2.md` Track C.2 + C.6 for the exercise records. Write tools stay permanent BETA under the deploy-features policy.

## Why this map exists

MCP clients discover tools dynamically, but agents benefit from a flat human-readable map when deciding which tool to call. This doc mirrors the server's `@app.tool()` decorators so humans and LLMs can pick the right one without reading Python.

## Read tools

| Tool | Endpoint | Status | Typical use |
|---|---|---|---|
| `chutes_list_models` | `GET https://llm.chutes.ai/v1/models` | VERIFIED | "What models are available?" |
| `chutes_chat_complete` | `POST https://llm.chutes.ai/v1/chat/completions` | **[BETA]** (paid; unverified) | Single-shot chat call |
| `chutes_list_chutes` | `GET /chutes/` | VERIFIED | "What have I deployed?" |
| `chutes_list_aliases` | `GET /model_aliases/` | VERIFIED | "What stable handles exist?" |
| `chutes_get_usage` | `GET /invocations/usage` | VERIFIED | "How much has the network spent?" |
| `chutes_get_quota` | `GET /users/me/quotas` | VERIFIED | "What are my quotas?" |
| `chutes_get_discounts` | `GET /users/me/discounts` | VERIFIED | "Am I getting a discount?" |
| `chutes_get_evidence` | `GET /chutes/{id}/evidence` | **[BETA]** (needs a chute_id) | "Show me TEE evidence for this chute" |
| `chutes_oauth_introspect` | `POST /idp/token/introspect` | **[BETA]** (needs a live token) | "Is this SIWC token active?" |
| `chutes_list_api_keys` | `GET /api_keys/` | VERIFIED | "What API keys exist on my account?" |

## Write tools (permanent BETA under deploy-features policy)

All write tools prepend `[BETA] ` to their tool description string so MCP clients display the label prominently.

| Tool | Endpoint | Why BETA |
|---|---|---|
| `chutes_deploy_vllm` | `POST /chutes/vllm` | Deploy — consumes paid compute. Wave 2 found the endpoint is also platform-gated: returns 403 "Easy deployment is currently disabled!" on some accounts. |
| `chutes_deploy_diffusion` | `POST /chutes/diffusion` | Deploy — consumes paid compute. Same platform gate as vLLM. |
| `chutes_teeify` | `PUT /chutes/{id}/teeify` | Creates a new TEE variant — hard to reverse |
| `chutes_set_alias` | `POST /model_aliases/` | Mutates team routing policy. **Functionally verified live in wave 2** (alias round-trip passed); stays BETA per policy. Wave-2 fix: body shape is `{alias, chute_ids: [uuid, ...]}`, not `{alias, model}`. |
| `chutes_delete_alias` | `DELETE /model_aliases/{alias}` | Removes team routing policy. **Functionally verified live in wave 2.** Read-after-delete is eventually consistent; retry or add a 1-2s delay for verification. |
| `chutes_create_api_key` | `POST /api_keys/` | Secret material creation |

## Graduation rule

A read tool loses its BETA label only after a commit that:

1. References a recorded verified call (transcript, test output, or eval pass).
2. Updates this file to remove `[BETA]` from its row.
3. Updates the `BETA_PREFIX` logic in `server.py` if the graduation requires changing the tool description.

Write tools stay BETA until the broader deploy-features policy changes — they do not graduate individually.
