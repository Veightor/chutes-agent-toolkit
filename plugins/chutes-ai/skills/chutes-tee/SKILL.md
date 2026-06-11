---
name: chutes-tee
description: "Verify Chutes.ai TEE (Trusted Execution Environment) attestation evidence — Intel TDX quotes and NVIDIA GPU confidential-compute reports (Hopper H200, Blackwell B200/B300/RTX Pro 6000). Use this skill when a user wants to actually verify that a chute marked confidential_compute:true is really running inside hardware isolation, fetch attestation evidence from the chute endpoint, parse a TDX quote byte-level, inspect the GPU attestation report, compare measurements against Chutes' published golden values, or audit the certificate chain. Triggers on: TEE verification, confidential compute, TDX quote, Intel TDX, NVIDIA Hopper attestation, NVIDIA Blackwell attestation, GPU confidential compute, /chutes/{id}/evidence, /servers/tee/measurements, golden measurements, quote verification, DCAP, attestation, chute attest, tee_type, mrsigner, mrtd, rtmr."
---

# chutes-tee

> **Status: RE-VERIFIED LIVE 2026-06-11** — all four scripts re-run against the same live TEE chute (`Qwen/Qwen3-32B-TEE`, chute_id `ac059e33...`): 14 instances, 0 failures, TDX v4 quote parsed byte-level, GPU evidence now reports `arch: BLACKWELL` (GB20X-class, 8 GPUs per instance). Originally verified 2026-04-13 via `docs/chutes-maxi-wave-2.md` Track B (then 7 instances on HOPPER/H100). Note the gateway has since gone **TEE-only**: all 13 models on `llm.chutes.ai/v1/models` carry `confidential_compute: true` (verified 2026-06-11), so this skill now applies to every hosted LLM. The skill ships with **shape-only verification as the default** — cryptographic validation against Intel DCAP / NVIDIA trust roots is optional tooling the scripts detect but do not yet fully run (see below).

## What this skill does

Takes `GET /chutes/{chute_id}/evidence` and turns raw attestation data into one of four verdicts:

| Verdict | Meaning |
|---|---|
| `verified` | Full cryptographic validation passed (DCAP + NVIDIA chain) |
| `shape-valid` | Byte layout is consistent with the TDX spec + GPU cert chain parses, but no crypto validation was run (DCAP not installed, or `--shape-only` mode) |
| `shape-invalid` | The envelope does not match the expected structure — suspicious |
| `expired` | A certificate in the chain has expired / nonce is too old |
| `failed-validation` | Cryptographic validation ran and failed — **do not trust this chute** |

**Honest limits:** shape-only is not a cryptographic guarantee — it only proves the envelope looks right. For audited / regulated use cases, you must install the DCAP tooling and run in full-verification mode. See `references/what-tee-does-not-protect.md`.

## Walkthrough

### Step 1 — fetch evidence

```bash
python <skill-scripts-dir>/fetch_evidence.py \
  --chute-id <chute_id> \
  --out /tmp/evidence.json
```

What it does:
1. `GET /instances/nonce` to obtain a 64-char hex nonce (32 bytes).
2. `GET /chutes/{chute_id}/evidence?nonce=<nonce>` with the management bearer.
3. Writes the JSON envelope to `--out` (or stdout with `--json`).

The nonce **must** be 64 hex characters (32 bytes). Any other length returns HTTP 400 `"Nonce must be exactly 64 hex characters (32 bytes)"`. `fetch_evidence.py` generates nonces automatically via `secrets.token_hex(32)`.

### Step 2 — attest end-to-end

```bash
python <skill-scripts-dir>/attest_chute.py --chute-id <chute_id>
```

One-shot: fetch → verify → report. Real output from the 2026-06-11 live run:

```
=== chute attest: ac059e33-eb27-541c-b9a9-24b214036475 ===
  instances:          14  (failed: 0)
  selected instance:  0 (0e2841ca-...)
  TDX quote version:  4
  TDX tee_type:       0x00000081 (TDX)
  att_key_type:       2 (ECDSA P-256)
  quote raw bytes:    5243
  mrtd (prefix):      ddc6efcdd2309e10837f8a7f64b71272...
  report_data pfx:    ...
  auth_data size:     4300 bytes

  GPUs attested:      8 (arch: BLACKWELL)
  GPU cert subject:   CN=GB20X A01 GSP FMC LF,O=NVIDIA Corporation,C=US,...
  GPU cert valid to:  9999-12-31T23:59:59+00:00

  verdict:            shape-valid
  cryptographic validation: not run — install Intel DCAP and run it manually against the saved envelope
```

### Step 3 — deep parse of a single quote

```bash
python <skill-scripts-dir>/verify_quote.py --input /tmp/evidence.json --instance 0
```

Extracts TDX quote fields from one evidence record:

```
=== TDX quote (instance 0) ===
  raw bytes:      5243
  version:        4
  att_key_type:   2 (ECDSA P-256)
  tee_type:       0x00000081 (TDX)
  qe_svn:         0x0000
  pce_svn:        0x0000
  qe_vendor_id:   <16 bytes hex>
  user_data:      <20 bytes hex>
  TD report body:
    mrtd           <48 bytes hex>
    mrconfigid     <48 bytes hex>
    rtmr0..rtmr3   <48 bytes hex each>
    report_data    <64 bytes hex — nonce commitment lives here>
  auth_data_size: 4300 bytes
```

`mrtd` / `rtmr[0..3]` are the measurement registers an auditor compares against expected values. This skill prints them; it does not ship a reference list — but Chutes now publishes golden measurement sets at `GET /servers/tee/measurements` (public, no auth; verified 2026-06-11). The 2026-06-11 live quote's `mrtd` matched the published golden `mrtd` exactly, and its `rtmr0` matched one of the published `8xRTX_PRO_6000` sets. Comparing against those published values is your policy decision; the scripts do not automate it yet.

### Step 4 — parse GPU attestation

```bash
python <skill-scripts-dir>/verify_gpu_attestation.py --input /tmp/evidence.json --instance 0 --gpu 0
```

Extracts one NVIDIA GPU evidence record (2026-06-11 live output — Blackwell; the 2026-04 probe returned HOPPER, so treat `arch` as fleet-dependent):

```
=== GPU evidence (instance 0, gpu 0) ===
  arch:            BLACKWELL
  evidence bytes:  4140 (decoded from 5520 b64 chars)
  certificate:
    subject:         CN=GB20X A01 GSP FMC LF,O=NVIDIA Corporation,C=US,...
    issuer:          CN=GB20X A01 GSP BROM,O=NVIDIA Corporation,C=US,...
    valid from:      2023-06-20T00:00:00+00:00
    valid to:        9999-12-31T23:59:59+00:00
    signature alg:   ecdsa-with-SHA384
```

## Cryptographic verification (optional)

To graduate from `shape-valid` to `verified`, install:

- **Intel DCAP quote verification** — the `sgx-dcap-quote-verify-python` Python binding, or Intel's `dcap-quote-verify` CLI. The scripts detect both at import time; neither is required to run the skill.
- **NVIDIA GPU attestation verifier** — `nv-trust` or equivalent; optional for GPU evidence validation.
- **cryptography** — the Python `cryptography` package is usually already installed as a transitive dep of `chutes-ai/manage_credentials.py`'s AES-GCM fallback.

**[BETA] Verified-mode caveat (corrected 2026-06-11):** as shipped, `attest_chute.py` *detects* DCAP availability and reports it, but does **not** yet run the full cryptographic validation pipeline or upgrade the verdict — the practical verdict ceiling of the bundled scripts is `shape-valid` even with DCAP installed. The `verified` graduation path is specified in `references/dcap-trust-root.md` but unwired; until it ships, run DCAP/`nv-trust` manually against the saved envelope if you need cryptographic assurance.

## Endpoint map

| Purpose | Method | Path | Notes |
|---|---|---|---|
| Get a fresh nonce | GET | `/instances/nonce` | Returns a 64-char hex string wrapped in quotes (JSON). Re-verified live 2026-06-11 |
| Chute-level evidence | GET | `/chutes/{chute_id}/evidence?nonce=<64-hex>` | Returns all instances for the chute. Re-verified live 2026-06-11 |
| Instance-level evidence | GET | `/instances/{instance_id}/evidence?nonce=<64-hex>` | Same shape, one instance (present in openapi.json; instance-level call itself unverified as of 2026-06-11) |
| Golden measurements | GET | `/servers/tee/measurements` | **New (verified live 2026-06-11, public — no auth needed).** Named measurement sets (`8xh200`, `8xb200`, `8xb200-eth`, `8xb300`, `8xRTX_PRO_6000`), each with `mrtd`, `boot_rtmrs`/`runtime_rtmrs` (RTMR0–3), `expected_gpus`, `gpu_count`. Compare a live quote's `mrtd`/RTMRs against these instead of hand-capturing references |

**Live probe findings (wave-2 2026-04-13; re-verified 2026-06-11):**

1. **`/chutes/{chute_id}/evidence` requires a `nonce` query parameter.** Without it, HTTP 400 `{"error":"$.query.nonce: required parameter missing"}`. The nonce must be exactly 64 hex chars (32 bytes); HTTP 400 `"Nonce must be exactly 64 hex characters (32 bytes), got N"` on any other length. `fetch_evidence.py` auto-generates via `secrets.token_hex(32)`.

2. **Top-level envelope shape:** `{"evidence": [<instance_record>, ...], "failed_instance_ids": [<uuid>, ...]}`. Test chute returned 7 instance records with 0 failures in 2026-04; 14 records with 0 failures on the 2026-06-11 re-probe. A non-empty `failed_instance_ids` means those instances couldn't generate evidence — still informative.

3. **Per-instance record:** `{"quote": "<b64>", "gpu_evidence": [...], "instance_id": "<uuid>", "certificate": "<b64_PEM>"}`. Quote is raw TDX quote bytes base64-encoded.

4. **TDX quote version 4 confirmed.** First 8 bytes of the decoded quote:
   - version (2 bytes LE) = 4
   - att_key_type (2 bytes LE) = 2 (ECDSA P-256)
   - tee_type (4 bytes LE) = 0x81 (TDX)
   Matches Intel TDX v4 spec.

5. **GPU evidence per instance: 8 records; `arch` is fleet-dependent.** The 2026-04 probe returned `arch: "HOPPER"` (NVIDIA H100); the 2026-06-11 re-probe returned `arch: "BLACKWELL"` (GB20X-class cert chain, `CN=GB20X A01 GSP FMC LF` signed `ecdsa-with-SHA384`). Each record is `{certificate: <b64 PEM>, evidence: <b64 binary>, arch: "<ARCH>"}`. The certificate decodes as a standard X.509 NVIDIA GPU attestation cert. Don't hardcode an expected arch.

6. **Golden measurements published (new, verified 2026-06-11).** `GET /servers/tee/measurements` (public) returns the platform's expected `mrtd` + RTMR sets per server class (h200, b200, b300, RTX Pro 6000). The live quote's `mrtd` matched the published value exactly and its `rtmr0` matched a published `8xRTX_PRO_6000` set — so auditors can now compare against platform-published references rather than only self-captured ones.

## Scripts in this skill

| Script | Purpose | Status |
|---|---|---|
| `scripts/fetch_evidence.py` | Fetch `/chutes/{id}/evidence` with auto-nonce (or `--server-nonce`), cache to disk | RE-VERIFIED LIVE (2026-06-11, both nonce modes) |
| `scripts/verify_quote.py` | Parse TDX v4 quote header, print fields | RE-VERIFIED LIVE (2026-06-11, shape-only) |
| `scripts/verify_gpu_attestation.py` | Parse GPU evidence record + X.509 certificate | RE-VERIFIED LIVE (2026-06-11, shape-only, Blackwell cert) |
| `scripts/attest_chute.py` | One-shot fetch + verify + report | RE-VERIFIED LIVE (2026-06-11, shape-only) |

## Safety rules

- **Never claim "verified" without crypto validation running.** The verdict stays `shape-valid` unless DCAP + NVIDIA tooling actually ran. Don't let users hand-wave the distinction.
- **Never hardcode expected `mrtd` / RTMR values in your own config.** Those change with Chutes releases. Compare against the platform's published golden sets at `GET /servers/tee/measurements` (public; verified 2026-06-11) at verification time, and/or capture a reference at a stable release and alert on drift.
- **Nonce is per-request.** Do not reuse nonces across calls; that's the anti-replay property of the whole scheme.
- **Evidence is ~100 KB per instance.** The scripts write to disk rather than stdout by default so full envelopes don't end up in shell history.
- **If `failed_instance_ids` is non-empty, surface it.** Silent failures are worse than loud ones — one broken instance can still run user inference if the chute routes to it.

## Related skills

- `chutes-routing` — `tee-chat` intent filters by `confidential_compute: true`, but **does not verify attestation**. Pair with `chutes-tee` for sensitive use cases. (As of 2026-06-11 every gateway model is `confidential_compute: true`, so the filter passes everything — attestation is the differentiator now.)
- `chutes-deploy` — `teeify_chute.py` creates a TEE variant of an existing affine chute. Run `attest_chute.py` against the new chute_id immediately after teeify to confirm the variant actually has valid evidence. (Note: "teeify" is a toolkit concept — the upstream Chutes SDK has no such command; its native deploy-side switch is the `tee=True` kwarg on `build_vllm_chute`/`build_sglang_chute`/`build_diffusion_chute`.)
- `chutes-mcp-portability` — `chutes_get_evidence` exposes the raw envelope as an MCP tool (currently BETA because wave-1 never fetched live evidence; Track B does).
