# Known Chutes.ai Models (Auto-Refreshed Snapshot)

This file is generated from the public Chutes OpenAI-compatible model endpoint. Do not edit it by hand; run `python3 scripts/update_chutes_models.py` instead.

Source: `GET https://llm.chutes.ai/v1/models` (no auth headers sent)
Last updated: 2026-07-14 10:56 UTC

## Summary

- Models returned: **13**
- TEE/confidential-compute models: **13/13** — the hosted gateway is currently TEE-only.
- Models advertising `tools`: **12**
- Models advertising `json_mode`: **12**
- Models advertising `structured_outputs`: **12**
- The models endpoint carries pricing and capability metadata, but not TTFT/TPS latency stats. For live latency/throughput data, use `GET https://api.chutes.ai/invocations/stats/llm` or the `default:latency` / `default:throughput` routing aliases.

## Live model table (USD per 1M tokens)

| Model ID | $ in | $ out | Cache read | Context | Quant | Engine | TEE | Modalities | Features |
|---|---:|---:|---:|---:|---|---|---|---|---|
| `zai-org/GLM-5.2-TEE` | 1.4 | 4.4 | 0.7 | 1049k | fp4 | sglang | yes | text | json_mode, structured_outputs, tools, reasoning |
| `moonshotai/Kimi-K2.6-TEE` | 0.66 | 3.5 | 0.33 | 262k | int4 | vllm | yes | text+image+video | json_mode, structured_outputs, tools, reasoning |
| `zai-org/GLM-5.1-TEE` | 0.98 | 3.08 | 0.49 | 203k | fp8 | sglang | yes | text | json_mode, structured_outputs, tools, reasoning |
| `Qwen/Qwen3.5-397B-A17B-TEE` | 0.45 | 3 | 0.225 | 262k | fp8 | sglang | yes | text+image | json_mode, tools, structured_outputs, reasoning |
| `zai-org/GLM-5-TEE` | 0.95 | 2.55 | 0.475 | 203k | fp8 | sglang | yes | text | json_mode, structured_outputs, tools, reasoning |
| `moonshotai/Kimi-K2.5-TEE` | 0.44 | 2 | 0.22 | 262k | int4 | sglang | yes | text+image+video | json_mode, structured_outputs, tools, reasoning |
| `Qwen/Qwen3.6-27B-TEE` | 0.3 | 2 | 0.15 | 262k | fp8 | sglang | yes | text+image | json_mode, tools, structured_outputs, reasoning |
| `MiniMaxAI/MiniMax-M2.5-TEE` | 0.15 | 1.2 | 0.075 | 197k | fp8 | sglang | yes | text | json_mode, tools, structured_outputs, reasoning |
| `Qwen/Qwen3-235B-A22B-Thinking-2507-TEE` | 0.2989 | 1.1957 | 0.14945 | 262k | bf16 | vllm | yes | text | json_mode, structured_outputs, tools, reasoning |
| `deepseek-ai/DeepSeek-V3.2-TEE` | 1 | 1 | 0.5 | 131k | fp8 | sglang | yes | text | json_mode, tools, reasoning, structured_outputs |
| `Qwen/Qwen3-32B-TEE` | 0.104 | 0.416 | 0.052 | 41k | fp8 | sglang | yes | text | json_mode, tools, structured_outputs, reasoning |
| `google/gemma-4-31B-turbo-TEE` | 0.12 | 0.37 | 0.06 | 131k | fp4 | sglang | yes | text+image | json_mode, tools, structured_outputs, reasoning |
| `unsloth/Mistral-Nemo-Instruct-2407-TEE` | 0.0245 | 0.0978 | 0.01225 | 131k | — | sglang | yes | text | — |

## Quick picks generated from the live snapshot

### Cheapest listed models

- `unsloth/Mistral-Nemo-Instruct-2407-TEE` ($0.0245/$0.0978, context 131k, text)
- `Qwen/Qwen3-32B-TEE` ($0.104/$0.416, context 41k, text)
- `google/gemma-4-31B-turbo-TEE` ($0.12/$0.37, context 131k, text+image)

### Cheapest image-capable models

- `google/gemma-4-31B-turbo-TEE` ($0.12/$0.37, context 131k, text+image)
- `Qwen/Qwen3.6-27B-TEE` ($0.3/$2, context 262k, text+image)
- `moonshotai/Kimi-K2.5-TEE` ($0.44/$2, context 262k, text+image+video)

### Largest context windows

- `zai-org/GLM-5.2-TEE` ($1.4/$4.4, context 1049k, text)
- `Qwen/Qwen3-235B-A22B-Thinking-2507-TEE` ($0.2989/$1.1957, context 262k, text)
- `Qwen/Qwen3.5-397B-A17B-TEE` ($0.45/$3, context 262k, text+image)

### Tool-capable examples

- `Qwen/Qwen3-32B-TEE` ($0.104/$0.416, context 41k, text)
- `google/gemma-4-31B-turbo-TEE` ($0.12/$0.37, context 131k, text+image)
- `Qwen/Qwen3.6-27B-TEE` ($0.3/$2, context 262k, text+image)
- `zai-org/GLM-5.1-TEE` ($0.98/$3.08, context 203k, text)
- `deepseek-ai/DeepSeek-V3.2-TEE` ($1/$1, context 131k, text)

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
