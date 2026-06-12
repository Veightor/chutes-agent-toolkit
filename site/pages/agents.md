# Page draft: `chutes.ai/agents` — "Run your agents on Chutes"

> Status: draft copy, ready for design. Facts current as of the 2026-06-11 live verification pass in [chutes-agent-toolkit](https://github.com/Veightor/chutes-agent-toolkit). Snapshot pricing below is from 2026-06-11; the production page must render pricing live (see Build notes). Horizontal rules mark page-section boundaries for the designer, not paragraph breaks.

---

# Your agent already speaks our API.

Chutes serves the best open-source models (DeepSeek, Kimi, GLM, Qwen, MiniMax) through the OpenAI API, on decentralized GPUs, with every model inside a hardware-isolated TEE. Point your agent at one URL and it works.

```python
client = OpenAI(
    base_url="https://llm.chutes.ai/v1",   # ← the only change
    api_key=os.environ["CHUTES_API_KEY"],
)
```

**[Get an API key →](https://chutes.ai/auth/start)**  **[Connect your agent →](/agents/connect)**

---

## Why agent builders pick Chutes

### Zero integration cost

It's the OpenAI API: chat completions, streaming, tool calling, JSON mode, structured outputs, vision. Every OpenAI SDK and every framework that takes a `base_url` works unchanged. There is no proprietary SDK to adopt, so there is nothing to migrate away from later.

### Privacy you can verify

100% of the hosted catalog runs with `confidential_compute: true` inside Intel TDX enclaves, with attested GPUs behind them. Your agent's prompts and outputs are isolated from the node operator and from us. Every chute also serves live attestation evidence from a public endpoint, so you can check the hardware claim yourself instead of taking our word for it. [See how →](/agents/private)

### Frontier open-source at decentralized prices

Kimi K2.6, GLM-5.1, DeepSeek V3.2, and Qwen3.5-397B, served from a competitive GPU network powered by Bittensor. Prompt-cache discounts apply automatically, a [25% research discount](#research-discount) is one URL swap away, and you can pay with a card or with $TAO.

---

## From zero to first completion

```bash
# 1. Get a key at chutes.ai/auth/start, then export it from your secret store:
export CHUTES_API_KEY="<redacted>"

# 2. See what's live right now (public, no auth)
curl https://llm.chutes.ai/v1/models

# 3. Call it
curl https://llm.chutes.ai/v1/chat/completions \
  -H "Authorization: Bearer $CHUTES_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"model": "deepseek-ai/DeepSeek-V3.2-TEE",
       "messages": [{"role": "user", "content": "Say hello in one sentence."}]}'
```

[Full runnable examples, from streaming to a complete mini-agent →](https://github.com/Veightor/chutes-agent-toolkit/tree/main/cookbook)

---

## Built for the failure modes agents actually hit

One model going down shouldn't take your agent with it. Pass a pool and a strategy in the `model` field; no extra infrastructure needed:

```python
# Failover: try in order until one answers
model="zai-org/GLM-5-TEE,deepseek-ai/DeepSeek-V3.2-TEE,Qwen/Qwen3.5-397B-A17B-TEE"

# Or pick the fastest / highest-throughput model at request time
model="zai-org/GLM-5-TEE,deepseek-ai/DeepSeek-V3.2-TEE:latency"
model="zai-org/GLM-5-TEE,deepseek-ai/DeepSeek-V3.2-TEE:throughput"
```

Models churn faster than your release cycle, so save a pool in the dashboard and call it as `default`, or pin a semantic alias like `interactive-fast` that survives catalog changes.

Agents can also self-serve the whole lifecycle. Registration, key creation, model discovery, balance checks, and usage stats are plain REST, which means an agent can onboard itself end to end. The [agent toolkit](https://github.com/Veightor/chutes-agent-toolkit) ships skills for Claude, for Hermes, and for generic OpenAI-compatible clients that do exactly that.

---

## What's on the menu

*(Live table rendered from `/v1/models`. Snapshot 2026-06-11: 13 models, all TEE.)*

| Model | Context | $/1M in | $/1M out | Good at |
|---|---|---|---|---|
| moonshotai/Kimi-K2.6-TEE | 256K | $0.74 | $3.50 | agentic work, vision + video |
| zai-org/GLM-5.1-TEE | 198K | $1.20 | $4.00 | flagship reasoning |
| deepseek-ai/DeepSeek-V3.2-TEE | 128K | $1.00 | $1.00 | balanced default |
| Qwen/Qwen3.5-397B-A17B-TEE | 256K | $0.45 | $3.00 | scale + vision |
| MiniMaxAI/MiniMax-M2.5-TEE | 192K | $0.15 | $1.20 | cheap agentic loops |
| unsloth/Mistral-Nemo-Instruct-2407-TEE | — | $0.02 | $0.10 | high-volume simple tasks |

Nearly every model supports tool calling, JSON mode, structured outputs, and reasoning (two small models advertise no feature flags; check `supported_features` on the live list). Discovery is public: `GET https://llm.chutes.ai/v1/models`, no key needed.

---

## <a name="research-discount"></a>Cut the bill 25% (if your data isn't sensitive)

Swap the base URL for `https://research-data-opt-in-proxy.chutes.ai/v1`: same models, same key, 25% cheaper. The trade is that prompts and responses are recorded for joint caching research with Harvard. Good for evals, synthetic data, and public-data workloads. Never for user PII.

---

## CTA band

**Ship your agent on open models tonight.**
[Create account](https://chutes.ai/auth/start) · [Connect your agent](/agents/connect) · [Browse live models](https://llm.chutes.ai/v1/models) · [Agent toolkit on GitHub](https://github.com/Veightor/chutes-agent-toolkit)

---

## Build notes (not page copy)

- **Live data**: the model table MUST render from `GET https://llm.chutes.ai/v1/models` (public). Columns map to `id`, `context_length`, `pricing.prompt`, `pricing.completion`. The "Good at" column needs a small curated map keyed by model family; keep it in the CMS so catalog churn doesn't require a deploy.
- **Model picker widget** goes between "What's on the menu" and the discount section. Logic: port [`scripts/pick_model.py`](../../scripts/pick_model.py).
- **Code snippets** come from [`cookbook/`](../../cookbook/) (all live-verified 2026-06-11); keep them in sync.
- The feature-support caveat matters: `unsloth/Mistral-Nemo-Instruct-2407-TEE` and `nvidia/NVIDIA-Nemotron-3-Ultra-550B-A55B-TEE` currently report empty `supported_features`. Don't blanket-claim tool support if those rows are shown.
- Auth fact to preserve in any snippet review: Bearer everywhere. `X-API-Key` is silently ignored on inference and lands on the anonymous 429 path (verified live 2026-06-11).
