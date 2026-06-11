# Known Chutes.ai Models (Reference Snapshot)

This is a point-in-time snapshot of models available on Chutes.ai. For the live, authoritative list, always query `GET https://llm.chutes.ai/v1/models` (public endpoint — no auth required). Use this file as a quick reference for model names, pricing, and capabilities.

Last updated: 2026-06-11 (verified against the live endpoint)

## The catalog is now TEE-only

As of 2026-06-11 the hosted LLM gateway serves exactly **13 models, all with `confidential_compute: true`** (Intel TDX Trusted Execution Environments) and `-TEE` suffixed IDs. The entire non-TEE chat tier that existed in April 2026 (unsloth Llama/gemma, Qwen2.5, GLM-4.x, Hermes, DeepSeek-R1, etc.) has been removed from the gateway. There are **zero Llama-family models** on the platform.

All 13 models advertise `json_mode`, `tools`, `structured_outputs`, and `reasoning` in `supported_features` (the two models with sparse metadata — Nemotron-3-Ultra and Mistral-Nemo — return `null` for features/modalities), and all expose `pricing.input_cache_read` at 50% of the input price for prompt-cache hits.

## Live model table (USD per 1M tokens, verified 2026-06-11)

| Model ID | $ in | $ out | Context | Quant | Engine | Modalities |
|---|---|---|---|---|---|---|
| `moonshotai/Kimi-K2.6-TEE` | 0.74 | 3.50 | 262k | int4 | vllm | text+image+video |
| `moonshotai/Kimi-K2.5-TEE` | 0.44 | 2.00 | 262k | int4 | vllm | text+image+video |
| `zai-org/GLM-5.1-TEE` | 1.20 | 4.00 | 202k | fp8 | sglang | text |
| `zai-org/GLM-5-TEE` | 0.95 | 2.55 | 202k | fp8 | sglang | text |
| `Qwen/Qwen3.5-397B-A17B-TEE` | 0.45 | 3.00 | 262k | fp8 | sglang | text+image |
| `Qwen/Qwen3.6-27B-TEE` | 0.30 | 2.00 | 262k | fp8 | vllm | text+image |
| `Qwen/Qwen3-235B-A22B-Thinking-2507-TEE` | 0.2989 | 1.1957 | 262k | bf16 | vllm | text |
| `Qwen/Qwen3-32B-TEE` | 0.104 | 0.416 | 41k | fp8 | sglang | text |
| `nvidia/NVIDIA-Nemotron-3-Ultra-550B-A55B-TEE` | 1.50 | 4.00 | — | — | vllm | text |
| `deepseek-ai/DeepSeek-V3.2-TEE` | 1.00 | 1.00 | 131k | fp8 | sglang | text |
| `MiniMaxAI/MiniMax-M2.5-TEE` | 0.15 | 1.20 | 196k | fp8 | sglang | text |
| `google/gemma-4-31B-turbo-TEE` | 0.15 | 0.42 | 131k | fp4 | vllm | text+image |
| `unsloth/Mistral-Nemo-Instruct-2407-TEE` | 0.0245 | 0.0978 | — | — | sglang | text |

Note: the models endpoint carries **no TTFT/TPS metadata** (verified 2026-06-11). For live latency/throughput numbers use `GET https://api.chutes.ai/invocations/stats/llm`, or let the `:latency` / `:throughput` routing suffixes pick for you.

## Quick Picks by Use Case

**Cheap-fast chat:**
- `google/gemma-4-31B-turbo-TEE` ($0.15/$0.42, vision-capable)
- `unsloth/Mistral-Nemo-Instruct-2407-TEE` ($0.0245/$0.0978 — cheapest on the platform)

**Frontier coding / agentic:**
- `moonshotai/Kimi-K2.6-TEE` (1T MoE, long-horizon agentic coding)
- `zai-org/GLM-5.1-TEE` (frontier coding/reasoning)
- Budget: `MiniMaxAI/MiniMax-M2.5-TEE` ($0.15/$1.20)

**Reasoning:**
- `zai-org/GLM-5.1-TEE` or `nvidia/NVIDIA-Nemotron-3-Ultra-550B-A55B-TEE` (long-horizon agent orchestration)
- Budget: `Qwen/Qwen3-235B-A22B-Thinking-2507-TEE` ($0.2989/$1.1957)

**Vision / multimodal:**
- `moonshotai/Kimi-K2.6-TEE` or `moonshotai/Kimi-K2.5-TEE` (only text+image+video models)
- Cheaper: `Qwen/Qwen3.5-397B-A17B-TEE`, `Qwen/Qwen3.6-27B-TEE`, `google/gemma-4-31B-turbo-TEE` (text+image)

**Privacy / confidential compute:**
- All of them — every hosted LLM is `confidential_compute: true` now.

## Beyond the LLM gateway

The wider chute catalog (`GET https://api.chutes.ai/chutes/?include_public=true`, ~497 public chutes) also includes, outside the OpenAI-compatible gateway:

- **Embeddings:** `Qwen/Qwen3-Embedding-8B-TEE` (invoke path/pricing unverified as of 2026-06-11)
- **Image:** `z-image-turbo`, `Qwen-Image-2512`, `Qwen-Image-Edit-2511`
- **Video:** `turbowani2v`
- **Audio/music/TTS:** `ACE-Step-15-Music-Generator`, `AudioDojo`, `kokoro`
- **Moderation/segmentation:** `halo-guard`, `nsfw-classifier`, `sam3`
- Hundreds of Bittensor Affine miner chutes (`*/Affine-*`)

## Removed since the April 2026 snapshot

If you see these IDs in old configs, they no longer exist on `/v1/models`: all non-TEE models (`unsloth/Llama-3.2-*`, `unsloth/gemma-3-*`, `Qwen/Qwen2.5-*`, `Qwen/Qwen3-30B-A3B`, `zai-org/GLM-4.6-FP8`, `zai-org/GLM-4.7-FP8`, `zai-org/GLM-5-Turbo`, `NousResearch/Hermes-4-14B`, `deepseek-ai/DeepSeek-R1-Distill-Llama-70B`, `rednote-hilab/dots.ocr`, ...) and many former TEE models (`Qwen/Qwen3-Coder-Next-TEE`, `deepseek-ai/DeepSeek-V3.1-TEE`, `deepseek-ai/DeepSeek-V3.1-Terminus-TEE`, `deepseek-ai/DeepSeek-R1-0528-TEE`, `deepseek-ai/DeepSeek-V3-0324-TEE`, `openai/gpt-oss-20b-TEE`, `openai/gpt-oss-120b-TEE`, `zai-org/GLM-4.6-TEE`, `zai-org/GLM-4.7-TEE`, `tngtech/DeepSeek-TNG-R1T2-Chimera-TEE`, `XiaomiMiMo/MiMo-V2-Flash-TEE`, `chutesai/Mistral-Small-3.1-24B-Instruct-2503-TEE`, `Qwen/Qwen3-235B-A22B-Instruct-2507-TEE`). Point aliases and configs at the live table above instead.
