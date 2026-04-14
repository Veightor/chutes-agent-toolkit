# Diffusion Chute Deploy Recipe **[BETA]**

> Source of truth: `POST /chutes/diffusion`. Verify body shape against `https://api.chutes.ai/openapi.json` before the first live run.

## Minimal request body

```json
{
  "name": "myuser/sdxl-turbo",
  "model": "stabilityai/sdxl-turbo",
  "tagline": "SDXL Turbo",
  "readme": "Deployed via chutes-deploy skill.",
  "node_selector": {
    "gpu_count": 1,
    "gpu_type": "a100_40gb"
  },
  "pipeline_args": {
    "torch_dtype": "float16"
  },
  "revision": "main",
  "public": false
}
```

## Field notes

- **`model`** — Hugging Face repo id of a diffusers-compatible pipeline (SDXL, SDXL-Turbo, SD 1.5, FLUX, etc.).
- **`pipeline_args`** — passed to `DiffusionPipeline.from_pretrained()`. Common knobs:
  - `torch_dtype` — `float16`, `bfloat16`.
  - `variant` — `fp16`, etc.
  - `use_safetensors` — `true` when the repo has safetensors.
- **`node_selector`** — most diffusion models fit on a single A100 40GB; FLUX and SD3 want 80GB.

## Sizing cheat-sheet

| Model | Minimum GPU |
|---|---|
| SDXL / SDXL-Turbo | a100_40gb |
| SD 1.5 | l40s / a100_40gb |
| FLUX.1 | a100_80gb |
| SD 3 Medium | a100_80gb |
| Video diffusion (SVD, LTX) | h100 |

## Calling a deployed diffusion chute

```bash
curl https://llm.chutes.ai/v1/images/generations \
  -H "Authorization: Bearer $CHUTES_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "myuser/sdxl-turbo",
    "prompt": "a watercolor owl",
    "size": "1024x1024",
    "n": 1
  }'
```

Response shape follows the OpenAI image-generation schema (`data[].url` or `data[].b64_json`).

## Common failure modes

- **`variant="fp16"` missing.** Some repos only ship fp16 weights under a variant. Set it explicitly.
- **`trust_remote_code` required.** Some pipelines ship custom schedulers or text encoders.
- **Pipeline can't find tokenizer.** The HF repo may depend on a separate text-encoder repo; include the dependency in `pipeline_args.text_encoder` or use a bundled-model repo.
