# Teeify a Chute **[BETA — ENDPOINT REMOVED UPSTREAM]**

> **Status 2026-06-11: `PUT /chutes/{chute_id}/teeify` is GONE.** The path no longer appears in `https://api.chutes.ai/openapi.json` (verified by direct read-only fetch, 2026-06-11), and the current `chutes` SDK has no teeify command at all. `scripts/teeify_chute.py` is kept for reference but will fail against the live API. This doc now explains the replacement path and the confidential-compute semantics so agents don't oversell them.

## How to get a TEE chute today

TEE is selected **at deploy time**, not retrofitted:

- **SDK templates:** pass `tee=True` to `build_vllm_chute(...)`, `build_sglang_chute(...)`, or `build_diffusion_chute(...)` (first-class boolean, flows through `Chute(tee=...)`; verified in the SDK source 2026-06-11). Runtime detection inside the chute is `is_tee_env()`.
- **Self-serve private TEE deploys:** the pricing page advertises private chutes on RTX Pro 6000 (96GB Blackwell) at $1.80/hr plus a one-time deploy fee of 3× the hourly rate, billed per second with idle auto-shutdown (pricing page verified 2026-06-11; the deploy flow itself unverified as of 2026-06-11).
- The only TEE-related write path remaining in the schema is `POST/PUT /instances/launch_config/{config_id}/tee` (semantics unverified as of 2026-06-11).

There is no supported way to convert an already-deployed non-TEE chute in place — redeploy with `tee=True`.

## What confidential compute means here

Inference runs inside an Intel TDX hardware enclave, with **NVIDIA Protected PCIe (PPCIE)** securing the CPU↔GPU channel (per the official security-architecture doc). Prompts and responses are hardware-isolated from the Chutes operators, the host OS, and the hypervisor.

It does not:

- Provide automatic attestation verification. You still have to fetch and verify `/chutes/{chute_id}/evidence`.
- Make the chute "audited." Hardware isolation is real but does not equal third-party review.

## What to tell the user

1. **"TEE" is a property exposed via `confidential_compute: true` on `/v1/models`, not a suffix.** Models happen to be named `...-TEE` (as of 2026-06-11 the entire hosted LLM catalog is TEE-only); use the boolean as the source of truth.
2. **Hardware isolation is real but does not equal "audited."** The user still needs to fetch attestation evidence and verify the quote / certificate chain before trusting the environment.
3. **Deep verification is handled by the sibling `chutes-tee` skill** (live-verified against a real TEE chute). This skill only surfaces the evidence endpoint.
4. **TEE-class hardware costs money.** Check the public `GET /pricing` for the GPU class hourly rate (e.g. pro_6000 $1.80/hr, verified 2026-06-11).

## Attestation evidence

```
GET /chutes/{chute_id_or_name}/evidence?nonce=<64-hex-chars>
```

The `nonce` query parameter is **required and must be exactly 64 hex characters (32 bytes)** — omitting it returns `$.query.nonce: required parameter missing`, and a wrong-length nonce returns `Nonce must be exactly 64 hex characters (32 bytes)` (live-verified 2026-06-11). A per-instance variant also exists: `GET /instances/{instance_id}/evidence`.

The response envelope (live-verified shape, 2026-06-11) contains per-instance records:

- `quote` — the Intel TDX quote (opaque bytes).
- `gpu_evidence[]` — NVIDIA GPU attestation reports with `certificate`, `evidence`, and `arch` (e.g. `"BLACKWELL"` observed live; older deployments used Hopper).
- `certificate` and `instance_id`, plus a top-level `failed_instance_ids` list.

Golden measurements for comparison are published at `GET /servers/tee/measurements` (named sets with `mrtd` + `boot_rtmrs`, live-verified 2026-06-11). To verify the quote properly you need Intel's DCAP tooling and a trusted root certificate — the **`chutes-tee` skill** automates shape-level verification and optionally cryptographic validation. If the user asks "is it real TEE," the honest answer without verification is "the evidence endpoint returns a TDX quote — verify it with chutes-tee before relying on it."

## Reverting

Deleting a TEE chute: `DELETE /chutes/{tee_chute_id}` — same as any chute.

## Safety reminder

Do not make strong privacy claims to users based solely on the fact that a chute deployed with `tee=True`. Until the evidence is verified, the guarantee is "Chutes says this chute runs in TEE." That is usually true, but "trust me" is not a security claim.
