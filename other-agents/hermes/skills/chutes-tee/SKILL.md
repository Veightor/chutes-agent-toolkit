---
name: chutes-tee
description: "Chutes.ai TEE and attestation workflow for Hermes users: fetch evidence envelopes, parse TDX quotes, parse NVIDIA GPU attestation, and explain what TEE does and does not guarantee. Triggers on: chutes tee, confidential compute, TEE attestation, fetch evidence, verify quote, GPU attestation, tdx quote, /chutes evidence."
version: 0.2.0
author: Chutes Agent Toolkit
license: MIT
metadata:
  hermes:
    tags: [chutes, tee, attestation, confidential-compute, tdx, hermes]
    status: shape-valid
---

# Chutes TEE for Hermes

> Status: SHAPE-VALID, verified live 2026-04-13 against a real TEE chute. The current scripts parse and validate evidence shape; full cryptographic validation requires Intel DCAP tooling. Full skill lives at `plugins/chutes-ai/skills/chutes-tee/`.

## When to use this skill

Use when a Hermes user wants to:
- Confirm whether a Chutes model/chute is confidential-compute backed.
- Fetch `/chutes/{id}/evidence` and inspect the evidence envelope.
- Parse TDX v4 quotes or NVIDIA Hopper GPU attestation fields.
- Understand the limits of TEE: it helps isolate runtime execution, but does not automatically prove model weights, prompts, or downstream systems are safe.

## Hermes-facing workflow

Run from the repo root:

```bash
python plugins/chutes-ai/skills/chutes-tee/scripts/fetch_evidence.py --chute-id <id> --out /tmp/evidence.json
python plugins/chutes-ai/skills/chutes-tee/scripts/verify_quote.py --evidence /tmp/evidence.json
python plugins/chutes-ai/skills/chutes-tee/scripts/verify_gpu_attestation.py --evidence /tmp/evidence.json
python plugins/chutes-ai/skills/chutes-tee/scripts/attest_chute.py --chute-id <id>
```

For model selection, still use the live models endpoint and filter `confidential_compute: true`.

## Deep references

- `plugins/chutes-ai/skills/chutes-tee/SKILL.md`
- `plugins/chutes-ai/skills/chutes-tee/references/evidence-envelope.md`
- `plugins/chutes-ai/skills/chutes-tee/references/tdx-quote-anatomy.md`
- `plugins/chutes-ai/skills/chutes-tee/references/dcap-trust-root.md`
- `plugins/chutes-ai/skills/chutes-tee/references/what-tee-does-not-protect.md`

## Safety rules

- Do not claim cryptographic verification unless DCAP validation has actually run and passed.
- Do not rely solely on a `-TEE` model-name suffix; use live metadata and evidence.
- Keep evidence files out of commits unless intentionally adding sanitized fixtures.
