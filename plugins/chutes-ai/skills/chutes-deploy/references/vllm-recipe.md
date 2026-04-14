# vLLM Chute Deploy Recipe **[BETA]**

> Source of truth: `POST /chutes/vllm` on `api.chutes.ai`. Verify the exact field names and required keys against `https://api.chutes.ai/openapi.json` before the first live run. This doc is a starting template, not a spec.

## Minimal request body

```json
{
  "name": "myuser/qwen3-8b",
  "model": "Qwen/Qwen3-8B",
  "tagline": "Qwen3 8B via vLLM",
  "readme": "Deployed via chutes-deploy skill.",
  "node_selector": {
    "gpu_count": 1,
    "gpu_type": "h100"
  },
  "vllm_args": {
    "max_model_len": 32768,
    "gpu_memory_utilization": 0.9
  },
  "revision": "main",
  "public": false
}
```

### Field notes

- **`name`** — `owner/chute-name`. Must be unique within the owner namespace. The deploy script defaults to `<your_username>/<model-slug>` if not supplied.
- **`model`** — Hugging Face repo id (for the easy vLLM lane, this is usually enough).
- **`revision`** — HF revision / commit sha. `main` is fine for experimentation; pin a commit for production.
- **`node_selector`** — `gpu_count` + `gpu_type`. Allowed types: `a100_40gb`, `a100_80gb`, `h100`, `h200`, `l40s`, `mi300x`. Check `GET /nodes/supported` for the authoritative current list.
- **`vllm_args`** — passes through to the vLLM server. Common knobs:
  - `max_model_len` — context window. Cannot exceed model's native max.
  - `gpu_memory_utilization` — 0.85–0.95 is typical.
  - `quantization` — `fp8`, `awq`, `gptq`, `bf16` (engine-dependent).
  - `dtype` — `auto`, `bfloat16`, `float16`.
  - `trust_remote_code` — `true` for models that need custom code paths.
- **`public`** — `false` keeps the chute private to you + anyone you share with; `true` makes it publicly callable.

## Response shape (captured fields)

```json
{
  "chute_id": "chute_...",
  "image_id": "image_...",
  "model_id": "myuser/qwen3-8b",
  "status": "building",
  "build_started_at": "2026-04-13T00:00:00Z"
}
```

Save `image_id` and `chute_id` — the deploy script polls both.

## Build log streaming

```
GET /images/{image_id}/logs
Accept: text/event-stream
```

Server-sent events with `data: <log_line>\n\n`. The deploy script tails this until it sees a terminal "build succeeded" / "build failed" line, or the connection closes with a 2xx.

## Warmup polling

```
GET /chutes/warmup/{chute_id}
```

Returns either:
- `{"status": "warming", "progress": 0.42}` — still coming up
- `{"status": "ready", "endpoint": "https://llm.chutes.ai/v1", "model_id": "myuser/qwen3-8b"}` — callable
- `{"status": "error", "detail": "..."}` — build or warmup failed

Poll every 5 seconds for up to 20 minutes; bail out with a clear error on timeout.

## Sizing cheat-sheet

| Model size | Minimum GPU | Comfortable GPU |
|---|---|---|
| ≤ 3B params | a100_40gb | a100_80gb |
| 7–13B | a100_80gb | h100 |
| 30–70B | h100 | h200 or 2× h100 |
| MoE / 100B+ | h200 | 2× h200 or mi300x cluster |

Deploying under-sized gets you an OOM during warmup and a failed build. Deploying over-sized burns money.

## Common failure modes

- **`trust_remote_code` required.** Some models (Qwen2.5, DeepSeek-V3 variants) ship custom modeling code. Set `vllm_args.trust_remote_code = true`.
- **Context length too large.** If `max_model_len` exceeds what the GPU can hold with the chosen dtype, vLLM will OOM. Drop `max_model_len` first, then revisit.
- **Tokenizer mismatch.** Rare but happens — usually a bad HF revision. Pin to a known-good commit.
- **GPU unavailable.** The Chutes network does not always have the requested GPU class free. Retry or fall back to the next tier.
