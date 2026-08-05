# Known Chutes.ai Models (Auto-Refreshed Snapshot)

This file is generated from the public Chutes OpenAI-compatible model endpoint. Do not edit it by hand; run `python3 scripts/update_chutes_models.py` instead.

Source: `GET https://llm.chutes.ai/v1/models` (no auth headers sent)
Last updated: 2026-08-05 11:30 UTC

## Summary

- Models returned: **13**
- TEE/confidential-compute models: **13/13** — the hosted gateway is currently TEE-only.
- Models advertising `tools`: **11**
- Models advertising `json_mode`: **11**
- Models advertising `structured_outputs`: **11**
- The models endpoint carries pricing and capability metadata, but not TTFT/TPS latency stats. For live latency/throughput data, use `GET https://api.chutes.ai/invocations/stats/llm` or the `default:latency` / `default:throughput` routing aliases.

## Live model table (USD per 1M tokens)

| Model ID | $ in | $ out | Cache read | Context | Quant | Engine | TEE | Modalities | Features |
|---|---:|---:|---:|---:|---|---|---|---|---|
| `moonshotai/Kimi-K3-TEE` | 3 | 15 | 0.3 | 1049k | mxfp4 | sglang | yes | text+image+video | json_mode, structured_outputs, tools, reasoning |
| `zai-org/GLM-5.2-TEE` | 1.25 | 3.95 | 0.125 | 1049k | fp4 | sglang | yes | text | json_mode, structured_outputs, tools, reasoning |
| `moonshotai/Kimi-K2.6-TEE` | 0.58 | 3.4 | 0.058 | 262k | int4 | vllm | yes | text+image+video | json_mode, structured_outputs, tools, reasoning |
| `zai-org/GLM-5.1-TEE` | 0.98 | 3.08 | 0.098 | 203k | fp8 | sglang | yes | text | json_mode, structured_outputs, tools, reasoning |
| `Qwen/Qwen3.5-397B-A17B-TEE` | 0.45 | 3 | 0.045 | 262k | fp8 | sglang | yes | text+image | json_mode, tools, structured_outputs, reasoning |
| `Qwen/Qwen3.6-27B-TEE` | 0.3 | 2 | 0.03 | 262k | fp8 | sglang | yes | text+image | json_mode, tools, structured_outputs, reasoning |
| `Qwen/Qwen3-235B-A22B-Thinking-2507-TEE` | 0.2989 | 1.1957 | 0.02989 | 262k | bf16 | vllm | yes | text | json_mode, structured_outputs, tools, reasoning |
| `deepseek-ai/DeepSeek-V3.2-TEE` | 1 | 1 | 0.1 | 131k | fp8 | sglang | yes | text | json_mode, tools, reasoning, structured_outputs |
| `Qwen/Qwen3-32B-TEE` | 0.104 | 0.416 | 0.0104 | 41k | fp8 | sglang | yes | text | json_mode, tools, structured_outputs, reasoning |
| `google/gemma-4-31B-turbo-TEE` | 0.12 | 0.37 | 0.012 | 131k | fp4 | sglang | yes | text+image | json_mode, tools, structured_outputs, reasoning |
| `deepseek-ai/DeepSeek-V4-Flash-0731-TEE` | 0.14 | 0.28 | 0.014 | 1049k | fp8 | sglang | yes | text | json_mode, structured_outputs, tools, reasoning |
| `Nemotron-3-Nano-Omni-30B-TEE` | 0.0245 | 0.0978 | 0.00245 | 131k | — | sglang | yes | text | — |
| `unsloth/Mistral-Nemo-Instruct-2407-TEE` | 0.0245 | 0.0978 | 0.00245 | 131k | — | sglang | yes | text | — |

## Quick picks generated from the live snapshot

### Cheapest listed models

- `Nemotron-3-Nano-Omni-30B-TEE` ($0.0245/$0.0978, context 131k, text)
- `unsloth/Mistral-Nemo-Instruct-2407-TEE` ($0.0245/$0.0978, context 131k, text)
- `Qwen/Qwen3-32B-TEE` ($0.104/$0.416, context 41k, text)

### Cheapest image-capable models

- `google/gemma-4-31B-turbo-TEE` ($0.12/$0.37, context 131k, text+image)
- `Qwen/Qwen3.6-27B-TEE` ($0.3/$2, context 262k, text+image)
- `Qwen/Qwen3.5-397B-A17B-TEE` ($0.45/$3, context 262k, text+image)

### Largest context windows

- `deepseek-ai/DeepSeek-V4-Flash-0731-TEE` ($0.14/$0.28, context 1049k, text)
- `moonshotai/Kimi-K3-TEE` ($3/$15, context 1049k, text+image+video)
- `zai-org/GLM-5.2-TEE` ($1.25/$3.95, context 1049k, text)

### Tool-capable examples

- `Qwen/Qwen3-32B-TEE` ($0.104/$0.416, context 41k, text)
- `google/gemma-4-31B-turbo-TEE` ($0.12/$0.37, context 131k, text+image)
- `Qwen/Qwen3.5-397B-A17B-TEE` ($0.45/$3, context 262k, text+image)
- `zai-org/GLM-5.1-TEE` ($0.98/$3.08, context 203k, text)
- `deepseek-ai/DeepSeek-V4-Flash-0731-TEE` ($0.14/$0.28, context 1049k, text)

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
