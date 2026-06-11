---
name: chutes-deploy
status: beta
description: "[BETA — permanent until verified] Deploy models on the Chutes.ai decentralized GPU network. Use this skill when the user wants to deploy a vLLM chute, diffusion chute, custom CDK chute, build a chute image, deploy a TEE/confidential chute (tee=True), inspect rolling updates, or create a stable model alias after deploy. Triggers on: deploy chute, chutes deploy, vllm chute, diffusion chute, build chute image, POST /chutes/, POST /chutes/vllm, POST /chutes/diffusion, POST /images/, teeify, tee=True, private chute, deployment fee, chutes deploy --accept-fee, revision pinning, rolling update chutes, chute share/unshare/make_public, model alias deploy."
---

# chutes-deploy **[BETA — permanent until verified live runs]**

> **Status: BETA (permanent).** This skill drives chute deployment, which falls under the toolkit's deploy-features policy: it is BETA until every script in it has a recorded live run against a dev Chutes account *and* the full end-to-end verification step has been executed. Time alone does not remove the label. Individual scripts graduate from BETA only with a commit that references the verification output that exercised them.
>
> **Easy-deploy gate status (refreshed 2026-06-11):** as of 2026-04-13, `POST /chutes/vllm` and `POST /chutes/diffusion` returned HTTP 403 `{"detail":"Easy deployment is currently disabled!"}` on the test account. On 2026-06-11 both endpoints are still present in `api.chutes.ai/openapi.json` (verified, read-only), but the gate itself was not re-probed (POST calls were out of scope for this refresh) and no announcement of it being lifted was found — assume it is still in effect (unverified as of 2026-06-11). When the gate is on, fall back to the custom CDK lane (`build_image.py` + `deploy_custom.py`) or the official `chutes` SDK/CLI flow. `deploy_vllm.py` / `deploy_diffusion.py` detect the 403 and print the fall-back hint. Note the pricing page now advertises self-serve **private TEE deployments** (RTX Pro 6000, 96GB Blackwell, $1.80/hr + one-time deploy fee of 3× the hourly rate, billed per second, idle auto-shutdown) — this may be the productized replacement for the easy lane (deploy flow itself unverified as of 2026-06-11).
>
> **Revision pinning (now definitive, verified 2026-06-11 against the chutes-api source):** the API enforces `revision` matching `^[a-fA-F0-9]{40}$` — a **full 40-hex HF commit SHA only**. Branch names (`main`) *and* short SHAs are rejected with `{"msg":"Value error, Invalid revision specified."}`. The scripts auto-resolve a branch name → current commit SHA via the Hugging Face API; pass `--revision <full-40-hex-sha>` explicitly to pin a specific commit. The official SDK (`chutes` ≥ 0.6.x) now also makes `revision=` a mandatory top-level kwarg on `build_vllm_chute` and suggests the current SHA on error.
>
> **Official SDK lane (recommended by Chutes docs):** the platform's documented deploy path is the `chutes` SDK/CLI — PyPI `chutes` 0.6.9 stable as of 2026-06-11 (0.6.11rc in flight) — `build_vllm_chute(...)` / `build_sglang_chute(...)` / `build_diffusion_chute(...)` + `chutes build my_image:tag --wait` + `chutes deploy my_image:tag --accept-fee`. Building images requires ≥ $50 balance; deploys charge a one-time fee of 3× the hourly GPU rate (gpu_count × cheapest compatible GPU). TEE is a first-class `tee=True` kwarg on all three templates. (SDK facts verified from source/README 2026-06-11; the flow was not exercised live this run.)

## What this skill does

Takes a user from "I want to run model X on Chutes" to a live `/v1/chat/completions` endpoint plus an optional stable alias:

- **Lane A — vLLM (easy).** Templated `POST /chutes/vllm` with build log streaming and warmup polling.
- **Lane B — diffusion (easy).** Templated `POST /chutes/diffusion` for image models.
- **Lane C — custom (CDK).** Build a Docker image via `POST /images/`, then `POST /chutes/` with the image reference.
- **TEE deploy.** Deploy a confidential-compute chute. **The old `PUT /chutes/{chute_id}/teeify` endpoint is GONE from the live OpenAPI schema (verified 2026-06-11)** — TEE is now selected at deploy time via the SDK templates' `tee=True` kwarg. See `references/teeify.md`.
- **Rolling updates.** Inspect and reason about `GET /chutes/rolling_updates`.
- **Sharing / visibility.** `POST /chutes/share`, `POST /chutes/unshare`, `POST /chutes/make_public`.
- **Stable alias on top.** Optional `POST /model_aliases/` so callers see `interactive-fast` instead of `myuser/my-chute-v3`.

## Prerequisites

- Chutes account + API key stored in the keychain (run `chutes-ai` hub first).
- Sufficient balance — deploy operations consume real paid compute.
- For custom lane (C): a CDK chute file (`my_chute.py` exposing a `chute` object) and a Dockerfile that the `chutes` SDK will package.
- Sufficient balance for image builds — the platform requires ≥ $50 balance to build images, and deploys charge a one-time fee of 3× the hourly GPU rate (verified from SDK README 2026-06-11).

## Walkthrough

### Lane A — Deploy a vLLM chute

Agent asks the user:

- **Model repo** (HF repo id, e.g. `Qwen/Qwen3-8B`, `deepseek-ai/DeepSeek-V3.2`).
- **GPU class** (e.g. `a100_80gb`, `h100`, `h200`). Defaults to the cheapest class that fits the model.
- **Optional alias** (e.g. `interactive-fast`).

```bash
python <skill-scripts-dir>/deploy_vllm.py \
  --model Qwen/Qwen3-8B \
  --gpu h100 \
  --alias interactive-fast
```

What the script does:

1. Pulls `cpk_` from `manage_credentials.py get --field api_key`.
2. Loads the templated body from `references/vllm-recipe.md` (or `--body-json <path>` override).
3. `POST /chutes/vllm` with the body. Captures `chute_id`.
4. Streams build logs from `GET /images/{image_id}/logs`.
5. Polls `GET /chutes/warmup/{chute_id}` until the chute is serving.
6. Returns the callable endpoint (`https://llm.chutes.ai/v1`) + the model id to use.
7. If `--alias` was set, calls `POST /model_aliases/ { alias, model: <model_id> }`.

### Lane B — Deploy a diffusion chute

```bash
python <skill-scripts-dir>/deploy_diffusion.py \
  --model stabilityai/sdxl-turbo \
  --gpu a100_40gb
```

Same flow, different endpoint (`POST /chutes/diffusion`). Exposes `/v1/images/generations`-style inference once warmed up.

### Lane C — Custom CDK deploy

Two-step:

```bash
# 1. Build the image
python <skill-scripts-dir>/build_image.py \
  --dockerfile /path/to/Dockerfile \
  --context /path/to/context/ \
  --name my-org/my-chute \
  --tag v1
```

The script multipart-uploads the build context to `POST /images/`, then streams `GET /images/{image_id}/logs` until the build succeeds. Returns the image id.

```bash
# 2. Deploy the chute referencing that image
python <skill-scripts-dir>/deploy_custom.py \
  --image-id <from step 1> \
  --entrypoint my_module:chute \
  --gpu h100 \
  --name my-chute
```

`POST /chutes/` with the image reference and entrypoint.

### Deploy a TEE (confidential-compute) chute

**The `PUT /chutes/{chute_id}/teeify` endpoint no longer exists** — it is absent from `api.chutes.ai/openapi.json` (verified 2026-06-11), and the current SDK has no teeify command. `scripts/teeify_chute.py` is retained for reference but will fail against the live API.

The supported path is **TEE at deploy time**: pass `tee=True` to the SDK templates (`build_vllm_chute`, `build_sglang_chute`, `build_diffusion_chute`) and deploy normally. The only TEE-related write path in the current schema is `POST/PUT /instances/launch_config/{config_id}/tee` (semantics unverified as of 2026-06-11). Confidential-compute semantics: Intel TDX hardware isolation plus NVIDIA Protected PCIe for the CPU↔GPU channel — even Chutes operators cannot read prompts/responses.

Attestation: `GET /chutes/{chute_id}/evidence?nonce=<64-hex-chars>` — the `nonce` query param is **required and must be exactly 64 hex characters (32 bytes)** (live-verified 2026-06-11). For deep verification of the returned TDX quotes and GPU evidence, use the sibling **`chutes-tee` skill** (live-verified).

### Create a stable alias for any deployed chute

```bash
python <skill-scripts-dir>/alias_deploy.py \
  --alias interactive-fast \
  --chute-id <chute_uuid>          # repeat --chute-id for a failover pool
```

`POST /model_aliases/` with `{alias, chute_ids: [...]}` — aliases point at chute UUIDs (a list, for failover pools); live `GET /model_aliases/` re-verified 2026-06-11. See `plugins/chutes-ai/skills/chutes-ai/references/model-aliases.md` for recommended packs.

### Inspect rolling updates

```bash
curl -H "Authorization: Bearer $(python manage_credentials.py get --field api_key)" \
  https://api.chutes.ai/chutes/rolling_updates
```

Not a script (one-shot query). Agent explains the response shape and whether the user's chute is currently mid-update.

### Share / unshare / make public

Brief recipes (no dedicated script — agent issues the requests):

- `POST /chutes/share` — share with another user
- `POST /chutes/unshare` — revoke
- `POST /chutes/make_public` — promote a subnet chute to public visibility

Each is a one-request operation; agents can build the body from `references/vllm-recipe.md` conventions.

## Endpoint map

All paths below re-verified present in `api.chutes.ai/openapi.json` on 2026-06-11 unless noted.

| Action | Method | Path |
|---|---|---|
| Deploy vLLM (easy) | POST | `/chutes/vllm` (may be 403-gated — see status note) |
| Deploy diffusion (easy) | POST | `/chutes/diffusion` (may be 403-gated — see status note) |
| Deploy custom | POST | `/chutes/` |
| Build image | POST | `/images/` (multipart) |
| Stream build logs | GET | `/images/{image_id}/logs` |
| Warmup chute | GET | `/chutes/warmup/{chute_id_or_name}` |
| ~~Teeify~~ | ~~PUT~~ | ~~`/chutes/{chute_id}/teeify`~~ **REMOVED upstream (gone from openapi.json, verified 2026-06-11)** — use `tee=True` at deploy time |
| Launch-config TEE | POST/PUT | `/instances/launch_config/{config_id}/tee` (semantics unverified as of 2026-06-11) |
| Attestation evidence | GET | `/chutes/{chute_id_or_name}/evidence?nonce=<64-hex>` (nonce required, live-verified 2026-06-11) |
| Rolling updates | GET | `/chutes/rolling_updates` |
| Share / unshare / make public | POST | `/chutes/share`, `/chutes/unshare`, `/chutes/make_public` |
| Delete | DELETE | `/chutes/{chute_id}` |
| Create alias | POST | `/model_aliases/` |
| GPU pricing (public, no auth) | GET | `/pricing` (live-verified 2026-06-11: 27 GPU types, $0.20/hr a4000 → $4.50/hr b200/b300) |

## Scripts in this skill

| Script | Purpose | Status |
|---|---|---|
| `scripts/deploy_vllm.py` | POST /chutes/vllm, stream build, warmup poll, optional alias | **[BETA]** |
| `scripts/deploy_diffusion.py` | POST /chutes/diffusion | **[BETA]** |
| `scripts/build_image.py` | POST /images/, stream logs | **[BETA]** |
| `scripts/deploy_custom.py` | POST /chutes/ with image ref | **[BETA]** |
| `scripts/teeify_chute.py` | PUT /chutes/{id}/teeify | **[BETA — DEFUNCT: endpoint removed upstream (verified 2026-06-11); kept for reference, will fail live]** |
| `scripts/alias_deploy.py` | POST /model_aliases/ | **[BETA]** |

## Safety rules

- **Never auto-deploy without explicit user confirmation.** Deploy operations consume real paid compute; always recap GPU class + cost estimate + model before POSTing.
- **Never hardcode `cpk_` into a script or transcript.** Always read from `manage_credentials.py`.
- **Warn before delete.** `DELETE /chutes/{id}` is hard to reverse.
- **Warn on `make_public`.** Once public, the chute is visible to other users until you delete it.
- **Never promise TEE guarantees without attestation.** Surface `/chutes/{id}/evidence?nonce=<64-hex>` and point the user at the sibling `chutes-tee` skill for actual quote/evidence verification.

## Related skills

- `chutes-ai` (hub) — account + API key prerequisite.
- `chutes-tee` — verifies TEE attestation evidence (TDX quotes, GPU reports) for deployed confidential chutes.
- `chutes-mcp-portability` **[BETA]** — exposes `chutes_deploy_vllm`, `chutes_deploy_diffusion`, `chutes_teeify`, `chutes_set_alias` as MCP tools (each prepended with `[BETA]` in the tool description). Note: the `chutes_teeify` tool targets the removed teeify endpoint and will fail live (verified gone 2026-06-11).
- `chutes-routing` (wave 2 stub) — routing recipes that compose naturally with newly-deployed chutes via aliases.
