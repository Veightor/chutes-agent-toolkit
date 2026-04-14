---
name: chutes-tee
description: "Verify Chutes.ai TEE (Trusted Execution Environment) attestation evidence — Intel TDX quotes and NVIDIA Hopper GPU confidential-compute reports. Use this skill when a user wants to actually verify that a chute marked confidential_compute:true is really running inside hardware isolation, fetch attestation evidence from the chute endpoint, parse a TDX quote byte-level, inspect the GPU attestation report, or audit the certificate chain. Triggers on: TEE verification, confidential compute, TDX quote, Intel TDX, NVIDIA Hopper attestation, GPU confidential compute, /chutes/{id}/evidence, quote verification, DCAP, attestation, chute attest, tee_type, mrsigner, mrtd, rtmr."
---

# chutes-tee

> **Status: VERIFIED LIVE 2026-04-13** via `docs/chutes-maxi-wave-2.md` Track B — fetched real TDX + Hopper attestation evidence from a live TEE chute (`Qwen/Qwen3-32B-TEE`, chute_id `ac059e33...`), parsed the TDX v4 quote header byte-level, inspected one of 56 GPU evidence records. The skill ships with **shape-only verification as the default** — cryptographic validation against Intel DCAP / NVIDIA trust roots is optional and only runs if the corresponding tooling is installed locally.

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

One-shot: fetch → verify → report. Example output:

```
=== chute attest: Qwen/Qwen3-32B-TEE (ac059e33-...) ===
  evidence envelope:   7 instances, 0 failed
  TDX quote version:   4
  TDX tee_type:        0x81 (TDX)
  GPU architecture:    HOPPER x 56 (8 per instance × 7)
  certificate subject: CN=Chutes TEE (example), ...
  nonce echo match:    ok
  verdict:             shape-valid
  cryptographic validation:  not run (DCAP tooling not installed)
```

### Step 3 — deep parse of a single quote

```bash
python <skill-scripts-dir>/verify_quote.py --input /tmp/evidence.json --instance 0
```

Extracts TDX quote fields from one evidence record:

```
=== TDX quote (instance 0) ===
  version:       4
  att_key_type:  2 (ECDSA P-256)
  tee_type:      0x00000081 (TDX)
  qe_svn:        0x0000
  pce_svn:       0x0000
  qe_vendor_id:  <16 bytes>
  user_data:     <20 bytes>
  mrsigner:      <48 bytes hex>
  mrtd:          <48 bytes hex>
  rtmr[0..3]:    <48 bytes each>
  report_data:   <64 bytes — includes nonce commitment>
```

`mrsigner` / `mrtd` / `rtmr[0..3]` are the measurement registers an auditor compares against expected values. This skill prints them; it does not ship a reference list of "good" values — that's your policy decision.

### Step 4 — parse GPU attestation

```bash
python <skill-scripts-dir>/verify_gpu_attestation.py --input /tmp/evidence.json --instance 0 --gpu 0
```

Extracts one NVIDIA Hopper GPU evidence record:

```
=== GPU evidence (instance 0, gpu 0) ===
  arch:              HOPPER
  evidence size:     5704 b64 chars (~4278 bytes decoded)
  certificate:
    subject:         CN=NVIDIA GPU ..., O=NVIDIA Corporation
    issuer:          CN=..., O=NVIDIA Corporation
    valid from:      ...
    valid to:        ...
    signature alg:   ecdsa-with-SHA256
```

## Cryptographic verification (optional)

To graduate from `shape-valid` to `verified`, install:

- **Intel DCAP quote verification** — the `sgx-dcap-quote-verify-python` Python binding, or Intel's `dcap-quote-verify` CLI. The scripts detect both at import time; neither is required to run the skill.
- **NVIDIA GPU attestation verifier** — `nv-trust` or equivalent; optional for GPU evidence validation.
- **cryptography** — the Python `cryptography` package is usually already installed as a transitive dep of `chutes-ai/manage_credentials.py`'s AES-GCM fallback.

With full tooling installed, `attest_chute.py` automatically runs crypto validation and upgrades the verdict to `verified`. Without it, the verdict stays `shape-valid` and the output says so loudly.

## Endpoint map

| Purpose | Method | Path | Notes |
|---|---|---|---|
| Get a fresh nonce | GET | `/instances/nonce` | Returns a 64-char hex string wrapped in quotes (JSON) |
| Chute-level evidence | GET | `/chutes/{chute_id}/evidence?nonce=<64-hex>` | Returns all instances for the chute |
| Instance-level evidence | GET | `/instances/{instance_id}/evidence?nonce=<64-hex>` | Same shape, one instance |

**Wave-2 findings:**

1. **`/chutes/{chute_id}/evidence` requires a `nonce` query parameter.** Without it, HTTP 400 `{"error":"$.query.nonce: required parameter missing"}`. The nonce must be exactly 64 hex chars (32 bytes); HTTP 400 `"Nonce must be exactly 64 hex characters (32 bytes), got N"` on any other length. `fetch_evidence.py` auto-generates via `secrets.token_hex(32)`.

2. **Top-level envelope shape:** `{"evidence": [<instance_record>, ...], "failed_instance_ids": [<uuid>, ...]}`. Test chute returned 7 instance records with 0 failures. A non-empty `failed_instance_ids` means those instances couldn't generate evidence — still informative.

3. **Per-instance record:** `{"quote": "<b64>", "gpu_evidence": [...], "instance_id": "<uuid>", "certificate": "<b64_PEM>"}`. Quote is raw TDX quote bytes base64-encoded.

4. **TDX quote version 4 confirmed.** First 8 bytes of the decoded quote:
   - version (2 bytes LE) = 4
   - att_key_type (2 bytes LE) = 2 (ECDSA P-256)
   - tee_type (4 bytes LE) = 0x81 (TDX)
   Matches Intel TDX v4 spec.

5. **GPU evidence per instance: 8 records, all `arch: "HOPPER"` (NVIDIA H100).** Each has `{certificate: <b64 PEM>, evidence: <b64 binary>, arch: "HOPPER"}`. The certificate decodes as a standard X.509 NVIDIA GPU attestation cert.

## Scripts in this skill

| Script | Purpose | Status |
|---|---|---|
| `scripts/fetch_evidence.py` | Fetch `/chutes/{id}/evidence` with auto-nonce, cache to disk | VERIFIED (2026-04-13) |
| `scripts/verify_quote.py` | Parse TDX v4 quote header, print fields | VERIFIED (2026-04-13, shape-only) |
| `scripts/verify_gpu_attestation.py` | Parse GPU evidence record + X.509 certificate | VERIFIED (2026-04-13, shape-only) |
| `scripts/attest_chute.py` | One-shot fetch + verify + report | VERIFIED (2026-04-13, shape-only) |

## Safety rules

- **Never claim "verified" without crypto validation running.** The verdict stays `shape-valid` unless DCAP + NVIDIA tooling actually ran. Don't let users hand-wave the distinction.
- **Never hardcode expected `mrsigner` / `mrtd` values.** Those change with every Chutes release. Document them as "capture a reference once the chute is at a stable release and alert on drift."
- **Nonce is per-request.** Do not reuse nonces across calls; that's the anti-replay property of the whole scheme.
- **Evidence is ~100 KB per instance.** The scripts write to disk rather than stdout by default so full envelopes don't end up in shell history.
- **If `failed_instance_ids` is non-empty, surface it.** Silent failures are worse than loud ones — one broken instance can still run user inference if the chute routes to it.

## Related skills

- `chutes-routing` — `tee-chat` intent filters by `confidential_compute: true`, but **does not verify attestation**. Pair with `chutes-tee` for sensitive use cases.
- `chutes-deploy` — `teeify_chute.py` creates a TEE variant of an existing affine chute. Run `attest_chute.py` against the new chute_id immediately after teeify to confirm the variant actually has valid evidence.
- `chutes-mcp-portability` — `chutes_get_evidence` exposes the raw envelope as an MCP tool (currently BETA because wave-1 never fetched live evidence; Track B does).
