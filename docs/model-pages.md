# Chutes Model Pages (Full-Modality Catalog)

This file is generated. Do not edit it by hand; run `python3 scripts/build_model_pages.py` instead. Source: the per-model `llms.txt` pages published on chutes.ai model pages, vendored under `data/model-pages/`.

Unlike [`known-models.md`](known-models.md) (auto-refreshed from `GET /v1/models`, which only lists **chat** LLMs), this catalog also covers embedding, image, video, audio, guard-classifier, and segmentation chutes that the OpenAI-compatible models endpoint never returns.

## Summary

- Model pages catalogued: **31**
- Chat LLMs (also in `known-models.md`): **13**
- Non-chat / full-modality chutes: **18**

Every model exposes an agent-facing `llms.txt` at `https://chutes.ai/app/chute/<slug>/llms.txt` and a callable OpenAPI spec at `.../openapi.json`.

## Chat / multimodal LLMs on the OpenAI-compatible gateway (also in known-models.md)

| Model | Owner | Modalities | What it is |
|---|---|---|---|
| [`deepseek-ai/DeepSeek-V3.2-TEE`](https://chutes.ai/app/chute/chutes-deepseek-ai-deepseek-v3-2-tee) | chutes | text in → text out | DeepSeek-V3.2 is an open-source LLM optimized for efficient reasoning and agent tasks t... |
| [`google/gemma-4-31B-turbo-TEE`](https://chutes.ai/app/chute/chutes-google-gemma-4-31b-turbo-tee) | chutes | text, image in → text out | Gemma-4-31B-IT NVFP4 with DFlash speculative decoding |
| [`MiniMaxAI/MiniMax-M2.5-TEE`](https://chutes.ai/app/chute/chutes-minimaxai-minimax-m2-5-tee) | chutes | text in → text out | MiniMax-M2.5 is a frontier-class LLM excelling at coding, agentic tool use, and office ... |
| [`moonshotai/Kimi-K2.5-TEE`](https://chutes.ai/app/chute/chutes-moonshotai-kimi-k2-5-tee) | chutes | text, image in → text out | Kimi K2.5 with DFlash speculative decoding |
| [`moonshotai/Kimi-K2.6-TEE`](https://chutes.ai/app/chute/chutes-moonshotai-kimi-k2-6-tee) | chutes | text, image, video in → text out | moonshotai/Kimi-K2.6 |
| [`Qwen/Qwen3-235B-A22B-Thinking-2507-TEE`](https://chutes.ai/app/chute/chutes-qwen-qwen3-235b-a22b-thinking-2507-tee) | chutes | text in → text out | Qwen/Qwen3-235B-A22B-Thinking-2507-TEE model on Chutes. |
| [`Qwen/Qwen3-32B-TEE`](https://chutes.ai/app/chute/chutes-qwen-qwen3-32b-tee) | chutes | text in → text out | Qwen/Qwen3-32B, FP8 precision with DFLASH speculative decoding |
| [`Qwen/Qwen3.5-397B-A17B-TEE`](https://chutes.ai/app/chute/chutes-qwen-qwen3-5-397b-a17b-tee) | chutes | text, image, video in → text out | Qwen/Qwen3.5-397B-A17B-FP8 |
| [`Qwen/Qwen3.6-27B-TEE`](https://chutes.ai/app/chute/chutes-qwen-qwen3-6-27b-tee) | chutes | text, image, video in → text out | Qwen/Qwen3.6-27B-FP8 with DFlash speculative decoding |
| [`unsloth/Mistral-Nemo-Instruct-2407-TEE`](https://chutes.ai/app/chute/chutes-unsloth-mistral-nemo-instruct-2407-tee) | chutes | text in → text out | unsloth/Mistral-Nemo-Instruct-2407 |
| [`zai-org/GLM-5-TEE`](https://chutes.ai/app/chute/chutes-zai-org-glm-5-tee) | chutes | text in → text out | zai-org/GLM-5-FP8 |
| [`zai-org/GLM-5.1-TEE`](https://chutes.ai/app/chute/chutes-zai-org-glm-5-1-tee) | chutes | text in → text out | GLM-5.1 is a large language model optimized for agentic tasks and coding that excels at... |
| [`zai-org/GLM-5.2-TEE`](https://chutes.ai/app/chute/chutes-zai-org-glm-5-2-tee) | chutes | text in → text out | nvidia/GLM-5.2-NVFP4 |

## Vision / multimodal understanding (media in → text out)

| Model | Owner | Modalities | What it is |
|---|---|---|---|
| [`docuextract`](https://chutes.ai/app/chute/vonkaiser-docuextract) | vonkaiser | image, text in → text out | Document OCR and structured extraction from PDFs and images |
| [`Nemotron-3-Nano-Omni-30B-TEE`](https://chutes.ai/app/chute/vonkaiser-nemotron-3-nano-omni-30b-tee) | vonkaiser | text, image, video, audio in → text out | Multimodal reasoning: video, audio, image, and text → answers, summaries, and tools |
| [`nsfw-classifier`](https://chutes.ai/app/chute/vonkaiser-nsfw-classifier) | vonkaiser | image, text in → text out | NSFW check for images and text |

## Embeddings

| Model | Owner | Modalities | What it is |
|---|---|---|---|
| [`Qwen/Qwen3-Embedding-8B-TEE`](https://chutes.ai/app/chute/chutes-qwen-qwen3-embedding-8b-tee) | chutes | text in → embedding out | Qwen/Qwen3-Embedding-8B |

## Image generation & editing

| Model | Owner | Modalities | What it is |
|---|---|---|---|
| [`imageclassic`](https://chutes.ai/app/chute/vonkaiser-imageclassic) | vonkaiser | text in → image out | Four classic image models on one chute: FLUX.1-schnell + three SDXL checkpoints |
| [`Qwen-Image-2512`](https://chutes.ai/app/chute/vonkaiser-qwen-image-2512) | vonkaiser | text in → image out | Qwen/Qwen-Image-2512 |
| [`Qwen-Image-Edit-2511`](https://chutes.ai/app/chute/vonkaiser-qwen-image-edit-2511) | vonkaiser | text, image in → image out | Qwen/Qwen-Image-Edit-2511 |
| [`z-image-turbo`](https://chutes.ai/app/chute/vonkaiser-z-image-turbo) | vonkaiser | text in → image out | Z-Image Turbo: fast text-to-image generation |

## Video generation

| Model | Owner | Modalities | What it is |
|---|---|---|---|
| [`turbowani2v`](https://chutes.ai/app/chute/vonkaiser-turbowani2v) | vonkaiser | text, image in → video out | TurboDiffusion I2V: Wan2.2-A14B-720P, 4-step distilled, SLA |

## Audio / speech / music

| Model | Owner | Modalities | What it is |
|---|---|---|---|
| [`ACE-Step-15-Music-Generator`](https://chutes.ai/app/chute/vonkaiser-ace-step-15-music-generator) | vonkaiser | text, audio in → audio out | MIT-licensed ACE-Step 1.5 XL — dual DiT (SFT quality + Turbo speed) with LM 4B planner.... |
| [`AudioDojo`](https://chutes.ai/app/chute/vonkaiser-audiodojo) | vonkaiser | text, audio in → audio, text out | One chute, 12 models, 13 endpoints — covering text-to-speech, voice cloning, voice desi... |
| [`kokoro`](https://chutes.ai/app/chute/chutes-kokoro) | chutes | text in → audio out | Text-to-speech with hexgrad/Kokoro-82M |
| [`LTX-23-Video`](https://chutes.ai/app/chute/vonkaiser-ltx-23-video) | vonkaiser | text, image in → video, audio out | Lightricks LTX 2.3 distilled-1.1 FP8 on RTX 6000 Pro — cinematic T2V, I2V, and keyframe... |

## Guard classifiers, scoring & segmentation

| Model | Owner | Modalities | What it is |
|---|---|---|---|
| [`halo-guard`](https://chutes.ai/app/chute/astroboi-halo-guard) | astroboi | — | Structured guard classifier for Halo0.8B-guard-v1 |
| [`halo4b-guard-alpha`](https://chutes.ai/app/chute/astroboi-halo4b-guard-alpha) | astroboi | — | Halo Guard Alpha 4B |
| [`haloqwen-output-guard`](https://chutes.ai/app/chute/astroboi-haloqwen-output-guard) | astroboi | — | HaloQwen Output Guard |
| [`RESI-USA-residential-appraisal`](https://chutes.ai/app/chute/resi0aaron-resi-usa-residential-appraisal) | resi0aaron | — | RESI USA Residential Model Current Winner |
| [`sam3`](https://chutes.ai/app/chute/score-test-sam3) | score_test | — | Segment Anything Model (SAM3) |

## Notes

- The live `/v1/models` endpoint remains the source of truth for chat LLM pricing and capabilities; this catalog is a convenience index of published model pages.
- Non-chat chutes are not OpenAI chat-completions compatible; call each via its own endpoint (see the model's `llms.txt` / `openapi.json`).
