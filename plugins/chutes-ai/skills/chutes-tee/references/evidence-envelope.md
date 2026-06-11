# Chutes Evidence Envelope — JSON Shape

> Based on live probes of `GET /chutes/{chute_id}/evidence?nonce=<64-hex>` against `Qwen/Qwen3-32B-TEE` (wave-2 2026-04-13; re-probed 2026-06-11 — same shape, new fleet). Shape may evolve between Chutes releases; always re-probe before trusting a schema.

## Top level

```json
{
  "evidence": [<instance_record>, ...],
  "failed_instance_ids": [<uuid>, ...]
}
```

- `evidence` — list of per-instance records, one per running TEE instance of the chute.
- `failed_instance_ids` — list of instance UUIDs that could not generate evidence (empty on a healthy chute).

Wave-2 probe against the test chute: 7 evidence records, 0 failures. 2026-06-11 re-probe: 14 evidence records, 0 failures. A healthy chute has `len(evidence) == number_of_instances` and `failed_instance_ids == []`.

## Per-instance record

```json
{
  "instance_id": "<uuid>",
  "quote": "<base64_tdx_quote>",
  "certificate": "<base64_PEM_cert>",
  "gpu_evidence": [<gpu_record>, ...]
}
```

- `instance_id` — UUID of the TEE instance running the chute.
- `quote` — base64-encoded raw Intel TDX v4 quote. ~7000 base64 chars = ~5200 bytes (2026-06-11 probe: 6992 b64 chars, 5243 bytes decoded). See `tdx-quote-anatomy.md` for byte layout.
- `certificate` — base64 PEM certificate. ~1880 chars in the 2026-06-11 probe. The signer cert for the TDX quote (not the GPU certs — those are nested under `gpu_evidence`).
- `gpu_evidence` — list of per-GPU evidence records.

## Per-GPU record

```json
{
  "arch": "BLACKWELL",
  "certificate": "<base64_PEM>",
  "evidence": "<base64_binary>"
}
```

- `arch` — GPU architecture string; **fleet-dependent, don't hardcode**. Wave-2 (2026-04) probe returned `HOPPER` (NVIDIA H100) for all 56 GPUs (8 per instance × 7 instances); 2026-06-11 re-probe returned `BLACKWELL` for all 8 GPUs of the inspected instance (GB20X-class).
- `certificate` — base64 PEM certificate for the GPU's attestation. X.509; 2026-06-11 probe: subject `CN=GB20X A01 GSP FMC LF,O=NVIDIA Corporation,C=US,...`, issuer `CN=GB20X A01 GSP BROM,...`, signed `ecdsa-with-SHA384` (2026-04 Hopper certs were `CN=NVIDIA GPU...`).
- `evidence` — base64-encoded binary GPU attestation report. ~5520 b64 chars (4140 bytes decoded) in the 2026-06-11 probe.

## Shape anomalies that matter

- `failed_instance_ids` non-empty → at least one instance couldn't produce evidence. Chute can still serve inference via other instances, but if your threat model requires verified instances only, treat non-empty as a hard fail.
- `gpu_evidence` empty for an instance → instance is running in TDX but without GPU confidential compute. Possible on hardware lacking NVIDIA confidential compute; downgrade your trust accordingly.
- Missing `certificate` at the instance level → the signing cert chain cannot be constructed. Shape-invalid.
- `arch` value not in `{HOPPER, BLACKWELL, ...}` → unexpected; log and investigate.

## Nonce binding

The nonce you supplied on `?nonce=<64-hex>` should be committed into the `report_data` field of the TDX quote (bytes 520-584 of the decoded quote body). A quote whose `report_data` does not incorporate the nonce is **replay-vulnerable** and should not be trusted.

The scripts auto-generate a fresh 32-byte nonce per fetch, and `verify_quote.py` extracts and prints `report_data` — but **the nonce-binding comparison itself is not implemented** (there is no `--check-nonce` flag; status unchanged as of 2026-06-11). Note `report_data` is a commitment, not necessarily the raw nonce — the 2026-06-11 probe's `report_data` did not literally contain the nonce hex, so a correct check must reproduce the platform's commitment scheme (derivation undocumented; unverified as of 2026-06-11). Compare across two fetches with different nonces as a manual freshness smoke test: `report_data` should differ.
