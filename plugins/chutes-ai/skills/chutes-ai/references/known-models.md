# Known Chutes.ai Models (Auto-Refreshed Snapshot)

This file is generated from the public Chutes OpenAI-compatible model endpoint. Do not edit it by hand; run `python3 scripts/update_chutes_models.py` instead.

Source: `GET https://llm.chutes.ai/v1/models` (no auth headers sent)
Last updated: 2026-10-29 16:09 UTC

## Summary

- Models returned: **17**
- TEE/confidential-compute models: **10/17**
- Models advertising `tools`: **10**
- Models advertising `json_mode`: **10**
- Models advertising `structured_outputs`: **10**
- The models endpoint carries pricing and capability metadata, but not TTFT/TPS latency stats. For live latency/throughput data, use `GET https://api.chutes.ai/invocations/stats/llm` or the `default:latency` / `default:throughput` routing aliases.

## Live model table (USD per 1M tokens)

| Model ID | $ in | $ out | Cache read | Context | Quant | Engine | TEE | Modalities | Features |
|---|---:|---:|---:|---:|---|---|---|---|---|
| `moonshotai/Kimi-K3-TEE` | 1.85 | 9.5 | 0.185 | 1049k | mxfp4 | sglang | yes | text+image+video | json_mode, structured_outputs, tools, reasoning |
| `zai-org/GLM-5.2-TEE` | 1.25 | 3.95 | 0.125 | 1049k | fp4 | sglang | yes | text | json_mode, structured_outputs, tools, reasoning |
| `Qwen/Qwen3.5-397B-A17B-TEE` | 0.45 | 3 | 0.045 | 262k | fp8 | sglang | yes | text+image | json_mode, tools, structured_outputs, reasoning |
| `zai-org/GLM-5.1-TEE` | 0.9 | 2.9 | 0.09 | 203k | fp8 | sglang | yes | text | json_mode, structured_outputs, tools, reasoning |
| `Qwen/Qwen3.6-27B-TEE` | 0.25 | 2 | 0.025 | 262k | fp8 | sglang | yes | text+image | json_mode, tools, structured_outputs, reasoning |
| `moonshotai/Kimi-K2.6-TEE` | 0.39 | 1.8 | 0.039 | 262k | int4 | vllm | yes | text+image+video | json_mode, structured_outputs, tools, reasoning |
| `deepseek-ai/DeepSeek-V4-Flash-0731-TEE` | 0.44 | 1.32 | 0.044 | 1049k | fp8 | sglang | yes | text | json_mode, structured_outputs, tools, reasoning |
| `Qwen/Qwen3.8-27B-TEE` | 0.039 | 1.25 | 0.0039 | 262k | fp8 | vllm | yes | text+image | json_mode, tools, structured_outputs, reasoning |
| `deepseek-ai/DeepSeek-V3.2-TEE` | 1 | 1 | 0.1 | 131k | fp8 | sglang | yes | text | json_mode, tools, reasoning, structured_outputs |
| `google/gemma-4-31B-turbo-TEE` | 0.12 | 0.37 | 0.012 | 131k | fp4 | sglang | yes | text+image | json_mode, tools, structured_outputs, reasoning |
| `Qwen/Qwen3.8-2.4T-A95B` | — | — | — | — | — | chutes | no | text | — |
| `Qwen/Qwen3.8-Max-0902` | — | — | — | — | — | chutes | no | text | — |
| `deepseek-ai/DeepSeek-V4-Pro-0813` | — | — | — | — | — | chutes | no | text | — |
| `deepseek-ai/DeepSeek-V4.1-Flash-1017` | — | — | — | — | — | chutes | no | text | — |
| `moonshotai/Kimi-K2.7-Code` | — | — | — | — | — | chutes | no | text | — |
| `zai-org/GLM-5.2-Fast` | — | — | — | — | — | chutes | no | text | — |
| `zai-org/GLM-5.3` | — | — | — | — | — | chutes | no | text | — |

## Quick picks generated from the live snapshot

### Cheapest listed models

- `Qwen/Qwen3.8-27B-TEE` ($0.039/$1.25, context 262k, text+image)
- `google/gemma-4-31B-turbo-TEE` ($0.12/$0.37, context 131k, text+image)
- `Qwen/Qwen3.6-27B-TEE` ($0.25/$2, context 262k, text+image)

### Cheapest image-capable models

- `Qwen/Qwen3.8-27B-TEE` ($0.039/$1.25, context 262k, text+image)
- `google/gemma-4-31B-turbo-TEE` ($0.12/$0.37, context 131k, text+image)
- `Qwen/Qwen3.6-27B-TEE` ($0.25/$2, context 262k, text+image)

### Largest context windows

- `deepseek-ai/DeepSeek-V4-Flash-0731-TEE` ($0.44/$1.32, context 1049k, text)
- `moonshotai/Kimi-K3-TEE` ($1.85/$9.5, context 1049k, text+image+video)
- `zai-org/GLM-5.2-TEE` ($1.25/$3.95, context 1049k, text)

### Tool-capable examples

- `Qwen/Qwen3.8-27B-TEE` ($0.039/$1.25, context 262k, text+image)
- `google/gemma-4-31B-turbo-TEE` ($0.12/$0.37, context 131k, text+image)
- `deepseek-ai/DeepSeek-V3.2-TEE` ($1/$1, context 131k, text)
- `zai-org/GLM-5.1-TEE` ($0.9/$2.9, context 203k, text)
- `moonshotai/Kimi-K2.6-TEE` ($0.39/$1.8, context 262k, text+image+video)

## Routing aliases

Chutes supports routing aliases that can be used as model values:

- `default`
- `default:latency`
- `default:throughput`

Use concrete model IDs when you need a specific model, context window, capability set, or price. Use routing aliases when you want Chutes to choose from the live pool.

## Defensive usage notes

- Treat this file as a convenience snapshot; the source of truth is always the live `/v1/models` endpoint.
- Check `confidential_compute` for privacy-sensitive tasks; do not rely only on a `-TEE` suffix.
- Check `supported_features` before promising tools, JSON mode, structured outputs, or reasoning behavior.
- Check `supported_sampling_parameters` before sending advanced sampling controls.
- Prompt-cache pricing, when present, is in `pricing.input_cache_read`.
