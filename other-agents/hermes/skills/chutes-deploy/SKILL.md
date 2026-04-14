---
name: chutes-deploy
description: "[BETA — permanent until verified] Deploy models on the Chutes.ai decentralized GPU network from Hermes. vLLM / diffusion / custom CDK deploy, image builds, teeify, rolling updates, stable aliases. Triggers on: deploy chute, chutes deploy, vllm chute, diffusion chute, build chute image, POST /chutes/, teeify, rolling update chutes, model alias deploy."
version: 0.1.0
author: Chutes Agent Toolkit
license: MIT
metadata:
  hermes:
    tags: [chutes, deploy, vllm, diffusion, tee, beta]
    status: beta
---

# Chutes Deploy for Hermes **[BETA — permanent until verified live runs]**

> **Status: BETA (permanent).** Mirror of the Claude-plugin `chutes-deploy` skill. Stays BETA until every script has a recorded live run against a dev Chutes account. Time alone does not remove the label.

## When to use this skill

A Hermes user wants to:

- Deploy a new vLLM or diffusion chute from a Hugging Face repo id.
- Build a custom CDK chute image from a Dockerfile + context.
- Teeify an existing affine chute into a TEE-isolated variant.
- Inspect rolling updates on an existing chute.
- Create a stable model alias (`interactive-fast`, `tee-chat`, etc.) on top of a deployed chute.

Not for: calling models that already exist on Chutes. That's the hub `chutes-ai` skill.

## Walkthrough (Hermes-facing)

Full walkthroughs and scripts live at `plugins/chutes-ai/skills/chutes-deploy/`. Hermes users run the same scripts from the repo root:

```bash
# Lane A — vLLM
python plugins/chutes-ai/skills/chutes-deploy/scripts/deploy_vllm.py \
  --model Qwen/Qwen3-8B --gpu h100 --alias interactive-fast

# Lane B — diffusion
python plugins/chutes-ai/skills/chutes-deploy/scripts/deploy_diffusion.py \
  --model stabilityai/sdxl-turbo --gpu a100_40gb

# Lane C — custom CDK (two-step)
python plugins/chutes-ai/skills/chutes-deploy/scripts/build_image.py \
  --dockerfile ./Dockerfile --context ./ctx --name myorg/my-chute --tag v1
python plugins/chutes-ai/skills/chutes-deploy/scripts/deploy_custom.py \
  --image-id <id> --entrypoint my_module:chute --gpu h100 --name myorg/my-chute

# Teeify
python plugins/chutes-ai/skills/chutes-deploy/scripts/teeify_chute.py --chute-id <id>

# Alias
python plugins/chutes-ai/skills/chutes-deploy/scripts/alias_deploy.py \
  --alias interactive-fast --model <model_id>
```

All scripts read `cpk_` from the shared keychain via `manage_credentials.py`.

## Deep references

- `plugins/chutes-ai/skills/chutes-deploy/SKILL.md` — full walkthrough
- `plugins/chutes-ai/skills/chutes-deploy/references/vllm-recipe.md`
- `plugins/chutes-ai/skills/chutes-deploy/references/diffusion-recipe.md`
- `plugins/chutes-ai/skills/chutes-deploy/references/teeify.md`
- `plugins/chutes-ai/skills/chutes-deploy/references/rolling-updates.md`
- `plugins/chutes-ai/skills/chutes-ai/references/model-aliases.md`

## Safety rules (same as the Claude skill)

- Deploy operations consume real paid compute — always confirm GPU class + cost before POSTing.
- Never hardcode `cpk_` anywhere. Always read from `manage_credentials.py`.
- `DELETE`, `teeify`, and `make_public` are hard to reverse — warn before executing.
- Do not make TEE privacy guarantees without attestation verification. Surface `/chutes/{id}/evidence` and point at the future `chutes-tee` skill.

## Related Hermes skills

- `chutes-ai` (Hermes hub) — API key prerequisite.
- `chutes-mcp-portability` **[BETA]** — exposes `chutes_deploy_vllm`, `chutes_deploy_diffusion`, `chutes_teeify`, `chutes_set_alias` as MCP tools (all labeled `[BETA]`).
