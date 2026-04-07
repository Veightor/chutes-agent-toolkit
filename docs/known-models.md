# Known Chutes.ai Models (Reference Snapshot)

This is a point-in-time snapshot of models available on Chutes.ai. For the live, authoritative list, always query `GET https://llm.chutes.ai/v1/models`. Use this file as a quick reference for model names and approximate performance characteristics.

Last updated: April 2026

## TEE Models (Confidential Compute)
These run inside Intel TDX Trusted Execution Environments — hardware-isolated inference.

| Model | TTFT (ms) | TPS |
|-------|-----------|-----|
| Qwen/Qwen3-Coder-Next-TEE | 1387 | 55.2 |
| Qwen/Qwen3.5-397B-A17B-TEE | 1168 | 41.3 |
| MiniMaxAI/MiniMax-M2.5-TEE | 1558 | 43.1 |
| deepseek-ai/DeepSeek-V3.1-Terminus-TEE | 1012 | 39.9 |
| chutesai/Mistral-Small-3.1-24B-Instruct-2503-TEE | 1460 | 19.6 |
| openai/gpt-oss-20b-TEE | 1745 | 26.8 |
| tngtech/DeepSeek-TNG-R1T2-Chimera-TEE | 1823 | 22.5 |
| zai-org/GLM-4.7-TEE | 1864 | 26.5 |
| openai/gpt-oss-120b-TEE | 2129 | 6.2 |
| deepseek-ai/DeepSeek-R1-0528-TEE | 2150 | 27.1 |
| Qwen/Qwen3-235B-A22B-Instruct-2507-TEE | 2284 | 10.0 |
| XiaomiMiMo/MiMo-V2-Flash-TEE | 2346 | 37.5 |
| zai-org/GLM-4.6-TEE | 2635 | 28.0 |
| deepseek-ai/DeepSeek-V3.1-TEE | 2797 | 17.2 |
| deepseek-ai/DeepSeek-V3.2-TEE | 3887 | 6.8 |
| Qwen/Qwen3-32B-TEE | 4148 | 37.1 |
| moonshotai/Kimi-K2.5-TEE | 5885 | 46.3 |
| deepseek-ai/DeepSeek-V3-0324-TEE | 5998 | 10.0 |
| zai-org/GLM-5-TEE | 22447 | 32.5 |

## Non-TEE Models

| Model | TTFT (ms) | TPS |
|-------|-----------|-----|
| unsloth/Llama-3.2-1B-Instruct | 410 | 328.5 |
| Qwen/Qwen3Guard-Gen-0.6B | 303 | 309.3 |
| unsloth/gemma-3-4b-it | — | 81.9 |
| unsloth/Mistral-Nemo-Instruct-2407 | 399 | 94.9 |
| unsloth/gemma-3-12b-it | 475 | 78.3 |
| Qwen/Qwen2.5-Coder-32B-Instruct | 486 | 106.0 |
| zai-org/GLM-4.6V | 528 | 65.0 |
| Qwen/Qwen3-30B-A3B | 570 | 182.7 |
| rednote-hilab/dots.ocr | 557 | 126.2 |
| Qwen/Qwen3-235B-A22B-Thinking-2507 | 723 | 101.2 |
| unsloth/gemma-3-27b-it | 930 | 39.0 |
| unsloth/Mistral-Small-24B-Instruct-2501 | 1012 | 127.1 |
| NousResearch/Hermes-4-14B | 1093 | 85.4 |
| chutesai/Mistral-Small-3.2-24B-Instruct-2506 | 1526 | 1252.6 |
| zai-org/GLM-4.6-FP8 | 1573 | 54.5 |
| zai-org/GLM-4.7-FP8 | 1623 | 49.8 |
| Qwen/Qwen2.5-72B-Instruct | — | 92.3 |
| Qwen/Qwen3-Next-80B-A3B-Instruct | — | 69.2 |
| NousResearch/DeepHermes-3-Mistral-24B-Preview | — | 52.8 |
| zai-org/GLM-5-Turbo | 5871 | 13.2 |
| deepseek-ai/DeepSeek-R1-Distill-Llama-70B | 7890 | 38.9 |
| unsloth/Llama-3.2-3B-Instruct | 21379 | 129.5 |
| Qwen/Qwen2.5-VL-32B-Instruct | — | — |

## Quick Picks by Use Case

**Fastest TTFT (latency-critical):**
- Qwen/Qwen3Guard-Gen-0.6B (303ms) — tiny guard model
- unsloth/Mistral-Nemo-Instruct-2407 (399ms) — general purpose
- unsloth/Llama-3.2-1B-Instruct (410ms) — small but fast

**Highest TPS (throughput-critical):**
- chutesai/Mistral-Small-3.2-24B-Instruct-2506 (1252.6 t/s) — exceptional throughput
- unsloth/Llama-3.2-1B-Instruct (328.5 t/s) — tiny and fast
- Qwen/Qwen3Guard-Gen-0.6B (309.3 t/s) — guard model

**Best TEE models by latency:**
- deepseek-ai/DeepSeek-V3.1-Terminus-TEE (1012ms TTFT)
- Qwen/Qwen3.5-397B-A17B-TEE (1168ms TTFT)
- Qwen/Qwen3-Coder-Next-TEE (1387ms TTFT)

**Best TEE models by throughput:**
- Qwen/Qwen3-Coder-Next-TEE (55.2 t/s)
- moonshotai/Kimi-K2.5-TEE (46.3 t/s)
- MiniMaxAI/MiniMax-M2.5-TEE (43.1 t/s)

**Reasoning models:**
- deepseek-ai/DeepSeek-R1-0528-TEE (TEE, 27.1 t/s)
- deepseek-ai/DeepSeek-R1-Distill-Llama-70B (non-TEE, 38.9 t/s)
- Qwen/Qwen3-235B-A22B-Thinking-2507 (non-TEE, 101.2 t/s)

**Coding models:**
- Qwen/Qwen3-Coder-Next-TEE (TEE, 55.2 t/s)
- Qwen/Qwen2.5-Coder-32B-Instruct (non-TEE, 106.0 t/s)

**Vision/multimodal:**
- Qwen/Qwen2.5-VL-32B-Instruct
- zai-org/GLM-4.6V (65.0 t/s)
- rednote-hilab/dots.ocr (126.2 t/s — OCR specialized)
