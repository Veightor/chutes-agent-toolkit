---
name: chutes-deploy
status: beta
description: "[BETA — permanent until verified] Deploy models on the Chutes.ai decentralized GPU network. Use this skill when the user wants to deploy a vLLM chute, diffusion chute, custom CDK chute, build a chute image, teeify an existing chute, inspect rolling updates, or create a stable model alias after deploy. Triggers on: deploy chute, chutes deploy, vllm chute, diffusion chute, build chute image, POST /chutes/, POST /chutes/vllm, POST /chutes/diffusion, POST /images/, teeify, PUT /chutes/{id}/teeify, rolling update chutes, chute share/unshare/make_public, model alias deploy."
---

# chutes-deploy **[BETA — permanent until verified live runs]**

> **Status: BETA (permanent).** This skill drives chute deployment, which falls under the toolkit's deploy-features policy: it is BETA until every script in it has a recorded live run against a dev Chutes account *and* the full end-to-end verification step has been executed. Time alone does not remove the label. Individual scripts graduate from BETA only with a commit that references the verification output that exercised them.
>
> **Wave-2 platform finding:** as of 2026-04-13, `POST /chutes/vllm` and `POST /chutes/diffusion` returned HTTP 403 `{"detail":"Easy deployment is currently disabled!"}` on the test account. The easy lanes may be gated server-side on some account classes. When this is in effect, fall back to the custom CDK lane (`build_image.py` + `deploy_custom.py`). `deploy_vllm.py` / `deploy_diffusion.py` detect the 403 and print the fall-back hint.
>
> **Wave-2 bug fix:** Chutes rejects branch names on the `revision` field with `{"msg":"Value error, Invalid revision specified."}`. The scripts now auto-resolve branch → commit SHA via the Hugging Face API. Pass `--revision <sha>` explicitly if you need a pinned specific commit.

## What this skill does

Takes a user from "I want to run model X on Chutes" to a live `/v1/chat/completions` endpoint plus an optional stable alias:

- **Lane A — vLLM (easy).** Templated `POST /chutes/vllm` with build log streaming and warmup polling.
- **Lane B — diffusion (easy).** Templated `POST /chutes/diffusion` for image models.
- **Lane C — custom (CDK).** Build a Docker image via `POST /images/`, then `POST /chutes/` with the image reference.
- **Teeify.** Promote an existing affine chute into a TEE-isolated variant via `PUT /chutes/{chute_id}/teeify`.
- **Rolling updates.** Inspect and reason about `GET /chutes/rolling_updates`.
- **Sharing / visibility.** `POST /chutes/share`, `POST /chutes/unshare`, `POST /chutes/make_public`.
- **Stable alias on top.** Optional `POST /model_aliases/` so callers see `interactive-fast` instead of `myuser/my-chute-v3`.

## Prerequisites

- Chutes account + API key stored in the keychain (run `chutes-ai` hub first).
- Sufficient balance — deploy operations consume real paid compute.
- For custom lane (C): a CDK chute file (`my_chute.py` exposing a `chute` object) and a Dockerfile that the `chutes` SDK will package.
- For teeify: the source chute must already be an affine chute on Chutes.

## Walkthrough

### Lane A — Deploy a vLLM chute

Agent asks the user:

- **Model repo** (e.g. `Qwen/Qwen3-8B`, `deepseek-ai/DeepSeek-V3-0324`).
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

### Teeify an existing chute

```bash
python <skill-scripts-dir>/teeify_chute.py --chute-id <id>
```

`PUT /chutes/{chute_id}/teeify`. Explains the confidential-compute semantics (hardware TDX isolation, even Chutes operators cannot read prompts/responses), and points the user at `GET /chutes/{chute_id}/evidence` to fetch attestation evidence. **Deep verification of the evidence is wave-2 work**; this skill only surfaces the raw endpoint.

### Create a stable alias for any deployed chute

```bash
python <skill-scripts-dir>/alias_deploy.py \
  --alias interactive-fast \
  --model <chute_id_or_model_id>
```

`POST /model_aliases/`. See `plugins/chutes-ai/skills/chutes-ai/references/model-aliases.md` for recommended packs.

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

| Action | Method | Path |
|---|---|---|
| Deploy vLLM (easy) | POST | `/chutes/vllm` |
| Deploy diffusion (easy) | POST | `/chutes/diffusion` |
| Deploy custom | POST | `/chutes/` |
| Build image | POST | `/images/` (multipart) |
| Stream build logs | GET | `/images/{image_id}/logs` |
| Warmup chute | GET | `/chutes/warmup/{chute_id}` |
| Teeify | PUT | `/chutes/{chute_id}/teeify` |
| Attestation evidence | GET | `/chutes/{chute_id}/evidence` |
| Rolling updates | GET | `/chutes/rolling_updates` |
| Share / unshare / make public | POST | `/chutes/share`, `/chutes/unshare`, `/chutes/make_public` |
| Delete | DELETE | `/chutes/{chute_id}` |
| Create alias | POST | `/model_aliases/` |

## Scripts in this skill

| Script | Purpose | Status |
|---|---|---|
| `scripts/deploy_vllm.py` | POST /chutes/vllm, stream build, warmup poll, optional alias | **[BETA]** |
| `scripts/deploy_diffusion.py` | POST /chutes/diffusion | **[BETA]** |
| `scripts/build_image.py` | POST /images/, stream logs | **[BETA]** |
| `scripts/deploy_custom.py` | POST /chutes/ with image ref | **[BETA]** |
| `scripts/teeify_chute.py` | PUT /chutes/{id}/teeify | **[BETA]** |
| `scripts/alias_deploy.py` | POST /model_aliases/ | **[BETA]** |

## Safety rules

- **Never auto-deploy without explicit user confirmation.** Deploy operations consume real paid compute; always recap GPU class + cost estimate + model before POSTing.
- **Never hardcode `cpk_` into a script or transcript.** Always read from `manage_credentials.py`.
- **Warn before delete/teeify.** `DELETE /chutes/{id}` and `teeify` are hard to reverse.
- **Warn on `make_public`.** Once public, the chute is visible to other users until you delete it.
- **Never promise TEE guarantees without attestation.** Surface `/chutes/{id}/evidence` and tell the user deep verification is wave-2 work in a future `chutes-tee` skill.

## Related skills

- `chutes-ai` (hub) — account + API key prerequisite.
- `chutes-mcp-portability` **[BETA]** — exposes `chutes_deploy_vllm`, `chutes_deploy_diffusion`, `chutes_teeify`, `chutes_set_alias` as MCP tools (each prepended with `[BETA]` in the tool description).
- `chutes-routing` (wave 2 stub) — routing recipes that compose naturally with newly-deployed chutes via aliases.
