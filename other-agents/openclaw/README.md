# OpenClaw + Chutes 🦞

Wire [Chutes.ai](https://chutes.ai) — decentralized, all-TEE, OpenAI-compatible inference — into [OpenClaw](https://openclaw.ai), the self-hosted gateway that connects your chat apps (Discord, Slack, Telegram, iMessage, WhatsApp, Teams, Signal, Matrix, and more) to AI coding agents.

From OpenClaw's point of view, Chutes is just another **OpenAI-compatible provider**. You add one provider block to `openclaw.json`, point your agent at a Chutes model, and your messaging-channel agents now run on open-source TEE models for a fraction of frontier-model cost.

> **Big news (2026-10-07):** OpenClaw now ships an **official bundled Chutes provider** — [`@openclaw/chutes-provider`](https://docs.openclaw.ai/providers/chutes) — with OAuth or API-key onboarding. That is the recommended path (section 1 below); the manual `models.providers` config further down remains the customization/fallback path.
>
> **[BETA]** Both paths are written against OpenClaw's official docs (re-checked 2026-10-07 against `openclaw@2026.9.8`) and the live-verified Chutes endpoint behavior, but have not yet been exercised end-to-end against a live OpenClaw install from this repo. Confirm field names against your installed version's docs and please open an issue if anything drifts.

> New to the Chutes API itself? Read the one-page [**Chutes Endpoint Guide**](../../docs/endpoint-guide.md) first — base URLs, auth, routing, and the model list all live there.

---

## What you need

- OpenClaw installed and onboarded:
  ```bash
  npm install -g openclaw@latest
  openclaw onboard
  ```
- A Chutes API key (`cpk_...`). Get one at [chutes.ai/auth/start](https://chutes.ai/auth/start) → [dashboard](https://chutes.ai/app), or programmatically via the [endpoint guide](../../docs/endpoint-guide.md#3-get-a-key-in-60-seconds).
- Your `openclaw.json` config file (OpenClaw uses **JSON5** — comments and trailing commas allowed).

---

## 1. The official provider plugin (recommended)

OpenClaw bundles an official Chutes provider — install it, restart the gateway, and onboard:

```bash
openclaw plugins install @openclaw/chutes-provider
openclaw gateway restart

# Browser OAuth:
openclaw onboard --auth-choice chutes
# …or API key:
openclaw onboard --auth-choice chutes-api-key
```

What you get (per the [official provider page](https://docs.openclaw.ai/providers/chutes)):

- Provider id `chutes`, base URL `https://llm.chutes.ai/v1`, OpenAI-compatible.
- Default model after onboarding: `chutes/zai-org/GLM-5.2-TEE`. Registered aliases: `chutes-pro` → `chutes/deepseek-ai/DeepSeek-V3.2-TEE`, `chutes-vision` → `chutes/moonshotai/Kimi-K2.6-TEE`.
- Env vars: `CHUTES_API_KEY` or `CHUTES_OAUTH_TOKEN` (plus `CHUTES_CLIENT_ID` / `CHUTES_CLIENT_SECRET` / `CHUTES_OAUTH_REDIRECT_URI` / `CHUTES_OAUTH_SCOPES` for custom OAuth apps).
- Quirks documented upstream: Chutes doesn't report token usage while streaming (`supportsUsageInStreaming: false`); model discovery is cached 5 minutes per credential; `openclaw models list --all --provider chutes` shows the catalog.

If the plugin covers your needs, you're done. The sections below are the **manual custom-provider path** — useful for pinning your own model list, costs, or a routing-pool model id.

---

## 2. Manual path: set your API key

OpenClaw resolves `${ENV_VAR}` references in config from the environment. Export your key (add it to your shell profile or OpenClaw's env file so the daemon sees it):

```bash
export CHUTES_API_KEY="cpk_..."
```

---

## 3. Manual path: add Chutes as a provider in `openclaw.json`

Chutes uses the `openai-completions` API shape. Add a `chutes` provider under `models.providers` and point your agent's primary model at it:

```json5
{
  agents: {
    defaults: {
      // provider-id/model-id
      model: { primary: "chutes/deepseek-ai/DeepSeek-V3.2-TEE" },
    },
  },

  models: {
    providers: {
      chutes: {
        baseUrl: "https://llm.chutes.ai/v1",
        apiKey: "${CHUTES_API_KEY}",        // Bearer cpk_ auth, sent automatically
        api: "openai-completions",
        timeoutSeconds: 300,                  // open-source models can be slower under load
        models: [
          {
            id: "deepseek-ai/DeepSeek-V3.2-TEE",
            name: "DeepSeek V3.2 (TEE)",
            reasoning: true,
            input: ["text"],
            contextWindow: 131072,
            maxTokens: 65536,
            // USD per 1M tokens, from GET https://llm.chutes.ai/v1/models
            cost: { input: 1.0, output: 1.0, cacheRead: 0.5, cacheWrite: 0 },
          },
          {
            id: "Qwen/Qwen3.5-397B-A17B-TEE",
            name: "Qwen3.5 397B (TEE)",
            reasoning: true,
            input: ["text", "image"],
            contextWindow: 262144,
            maxTokens: 65536,
            cost: { input: 0.45, output: 3.0, cacheRead: 0.225, cacheWrite: 0 },
          },
        ],
      },
    },
  },
}
```

Then activate and verify:

```bash
openclaw models list
openclaw models set chutes/deepseek-ai/DeepSeek-V3.2-TEE
```

That's the whole integration. Your channel agents now run on Chutes.

> 📋 **The model IDs, context windows, and costs above are a snapshot.** The catalog changes — always reconcile against the live list: `curl https://llm.chutes.ai/v1/models`. A daily-refreshed copy lives at [`data/chutes-models.json`](../../data/chutes-models.json).

---

## 4. Manual path: use routing instead of a single model

A single model ID is a single point of failure. Chutes accepts a comma-separated **pool** with a strategy suffix right in the model ID — and because OpenClaw passes the `id` straight through, you can use that here too. Define the pool as a model entry:

```json5
models: {
  providers: {
    chutes: {
      baseUrl: "https://llm.chutes.ai/v1",
      apiKey: "${CHUTES_API_KEY}",
      api: "openai-completions",
      models: [
        {
          // Lowest-latency-first failover pool — great for interactive chat ops
          id: "zai-org/GLM-5.2-TEE,deepseek-ai/DeepSeek-V3.2-TEE,Qwen/Qwen3.5-397B-A17B-TEE:latency",
          name: "Chutes (latency pool)",
          input: ["text"],
          contextWindow: 131072,
          maxTokens: 65536,
        },
      ],
    },
  },
},

agents: {
  defaults: {
    model: { primary: "chutes/zai-org/GLM-5.2-TEE,deepseek-ai/DeepSeek-V3.2-TEE,Qwen/Qwen3.5-397B-A17B-TEE:latency" },
  },
},
```

Strategy suffixes: omit for sequential failover, `:latency` for fastest first token, `:throughput` for most tokens/sec. If you've saved a pool in the [dashboard](https://chutes.ai/app), the aliases `default`, `default:latency`, and `default:throughput` work as model IDs too. Full recipes: [Chutes Endpoint Guide → routing](../../docs/endpoint-guide.md#6-smart-routing-one-request-many-models).

---

## 5. Picking a model for your channels

| Use case | Suggested model | Why |
|---|---|---|
| Interactive chat ops (fast, cheap) | `google/gemma-4-31B-turbo-TEE` or `Qwen/Qwen3.8-27B-TEE` | Lowest cost, low latency (both tool-call verified live 2026-10-07) |
| General coding agent | `deepseek-ai/DeepSeek-V3.2-TEE` | Strong reasoning, flat $1/$1 pricing |
| Hard reasoning / planning | `zai-org/GLM-5.2-TEE`, `Qwen/Qwen3-235B-A22B-Thinking-2507-TEE` | Frontier-class reasoning |
| Vision (screenshots, images in chat) | `google/gemma-4-31B-turbo-TEE`, `Qwen/Qwen3.6-27B-TEE`, `moonshotai/Kimi-K2.6-TEE` | `input` includes `image` |
| Huge context (long threads / repos) | `zai-org/GLM-5.2-TEE`, `deepseek-ai/DeepSeek-V4-Flash-0731-TEE`, `moonshotai/Kimi-K3-TEE` | 1M context |

Every hosted model is TEE-backed (`confidential_compute: true`) — a good fit for a gateway that handles real conversations across personal channels. See [privacy](../../docs/endpoint-guide.md#8-privacy-every-model-is-a-tee).

---

## 6. Optional: vendor-specific request fields

Need to pass a Chutes/engine-specific field (e.g. a sampling knob not in the standard schema)? OpenClaw merges extra JSON into the request body via per-model `params.extra_body`:

```json5
agents: {
  defaults: {
    models: {
      "chutes/deepseek-ai/DeepSeek-V3.2-TEE": {
        params: {
          extra_body: { top_k: 40, repetition_penalty: 1.05 },
        },
      },
    },
  },
}
```

Check each model's `supported_sampling_parameters` (from `/v1/models`) before sending advanced knobs — `sglang` and `vllm` engines accept different ones.

---

## 7. Research endpoint — defunct

Earlier versions of this guide documented a 25%-cheaper research opt-in endpoint (`research-data-opt-in-proxy.chutes.ai`). It is **gone** — verified 2026-10-07: the host returns 404 `DEPLOYMENT_NOT_FOUND` and the offer is no longer advertised on chutes.ai. Use the standard endpoint (`https://llm.chutes.ai/v1`) for everything; per-account discounts, if any, show up in `GET https://api.chutes.ai/users/me/discounts`.

---

## Config examples

Ready-to-copy files live in [`config-examples/`](config-examples/):

- [`openclaw.json`](config-examples/openclaw.json) — minimal single-model Chutes setup.
- [`openclaw-routing.json`](config-examples/openclaw-routing.json) — latency-optimized routing pool + a vision model.

---

## Troubleshooting

| Symptom | Fix |
|---|---|
| `429` even though the key is set | Make sure `api: "openai-completions"` so Bearer auth is sent. `X-API-Key` is ignored by Chutes. |
| `model not found` | The ID changed — re-check `curl https://llm.chutes.ai/v1/models`. |
| Requests time out | Bump `timeoutSeconds` (open-source models can be slower under load). |
| Param rejected | Move it to `params.extra_body` and confirm it's in the model's `supported_sampling_parameters`. |

More: the [Chutes Endpoint Guide → errors & gotchas](../../docs/endpoint-guide.md#10-errors--gotchas).

---

## Links

- OpenClaw docs: <https://docs.openclaw.ai> · Chutes provider: <https://docs.openclaw.ai/providers/chutes> · Custom providers: <https://docs.openclaw.ai/concepts/model-providers/custom-providers>
- Chutes endpoint guide (this repo): [`docs/endpoint-guide.md`](../../docs/endpoint-guide.md)
- Live model list: <https://llm.chutes.ai/v1/models>
- Chutes dashboard: <https://chutes.ai/app>

*OpenClaw is open-source (core gateway MIT-licensed). Chutes model IDs and pricing change — `GET https://llm.chutes.ai/v1/models` is always the source of truth.*
