---
type: llm
weight: 1
---

Should route to the chutes-deploy skill (permanent BETA). Should explicitly acknowledge that deploy consumes real paid compute, confirm before POSTing, POST /chutes/vllm with a templated body (model Qwen/Qwen3-8B, gpu_type h100, gpu_count 1, revision pinned to a full 40-hex HF commit SHA — the API rejects branch names and short SHAs), stream build logs from GET /images/{image_id}/logs, poll GET /chutes/warmup/{chute_id} until ready, then POST /model_aliases/ with {alias: interactive-fast, chute_ids: [<chute_uuid>]} — NOT {alias, model}. Should return the base_url + model_id for inference. Must warn about BETA status and that the easy-deploy lane may be server-side gated (403) on some account classes.
