# Chutes Evidence Envelope — JSON Shape

> Based on wave-2 live probe of `GET /chutes/{chute_id}/evidence?nonce=<64-hex>` against `Qwen/Qwen3-32B-TEE`. Shape may evolve between Chutes releases; always re-probe before trusting a schema.

## Top level

```json
{
  "evidence": [<instance_record>, ...],
  "failed_instance_ids": [<uuid>, ...]
}
```

- `evidence` — list of per-instance records, one per running TEE instance of the chute.
- `failed_instance_ids` — list of instance UUIDs that could not generate evidence (empty on a healthy chute).

Wave-2 probe against the test chute: 7 evidence records, 0 failures. A healthy chute has `len(evidence) == number_of_instances` and `failed_instance_ids == []`.

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
- `quote` — base64-encoded raw Intel TDX v4 quote. ~6600 base64 chars = ~5000 bytes. See `tdx-quote-anatomy.md` for byte layout.
- `certificate` — base64 PEM certificate. ~1860 chars in the test probe. The signer cert for the TDX quote (not the GPU certs — those are nested under `gpu_evidence`).
- `gpu_evidence` — list of per-GPU evidence records.

## Per-GPU record

```json
{
  "arch": "HOPPER",
  "certificate": "<base64_PEM>",
  "evidence": "<base64_binary>"
}
```

- `arch` — GPU architecture string. Test probe returned `HOPPER` (NVIDIA H100) for all 56 GPUs (8 per instance × 7 instances).
- `certificate` — base64 PEM certificate for the GPU's attestation. ~6436 chars. X.509 with subject `CN=NVIDIA GPU...` (verify live).
- `evidence` — base64-encoded binary GPU attestation report. ~5700 chars.

## Shape anomalies that matter

- `failed_instance_ids` non-empty → at least one instance couldn't produce evidence. Chute can still serve inference via other instances, but if your threat model requires verified instances only, treat non-empty as a hard fail.
- `gpu_evidence` empty for an instance → instance is running in TDX but without GPU confidential compute. Possible on non-Hopper hardware; downgrade your trust accordingly.
- Missing `certificate` at the instance level → the signing cert chain cannot be constructed. Shape-invalid.
- `arch` value not in `{HOPPER, BLACKWELL, ...}` → unexpected; log and investigate.

## Nonce binding

The nonce you supplied on `?nonce=<64-hex>` should be committed into the `report_data` field of the TDX quote (bytes 520-584 of the decoded quote body). `verify_quote.py --check-nonce` extracts this and compares. A quote whose `report_data` does not incorporate the nonce is **replay-vulnerable** and should not be trusted.

Wave-2 scripts auto-generate a fresh 32-byte nonce per fetch; the binding check is recommended but not yet implemented in `verify_quote.py` beyond extracting the field. Full nonce-binding verification ships as a wave-3 improvement.
