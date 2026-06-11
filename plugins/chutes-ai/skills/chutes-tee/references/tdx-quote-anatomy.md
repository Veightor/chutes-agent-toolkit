# TDX Quote Anatomy

> What's inside an Intel TDX v4 quote, byte-level. Source of truth: Intel's "Architecture Specification: Intel Trust Domain Extensions (Intel TDX) Module" and the DCAP quote format specs. This doc summarizes what the `chutes-tee` skill parses.

## Quote envelope

A Chutes evidence record contains a base64-encoded quote that decodes to **~5200 bytes** (5243 bytes on the 2026-06-11 live probe) for TDX v4 with GPU co-attestation. The envelope is:

```
| Quote Header   (48 bytes)  |
| TD Report Body (584 bytes) |
| Auth Data Size (4 bytes)   |
| Auth Data      (variable)  |
```

The auth data contains the ECDSA signature + the signing key + the QE (quoting enclave) report + the QE cert chain.

## Quote header (48 bytes)

| Offset | Field | Size | Meaning |
|---|---|---|---|
| 0 | `version` | u16 LE | `4` for TDX v4 |
| 2 | `att_key_type` | u16 LE | `2` = ECDSA P-256 + SHA-256 |
| 4 | `tee_type` | u32 LE | `0x81` = TDX |
| 8 | `qe_svn` | u16 LE | Quoting enclave SVN |
| 10 | `pce_svn` | u16 LE | Platform certification enclave SVN |
| 12 | `qe_vendor_id` | 16 bytes | Intel QE vendor id |
| 28 | `user_data` | 20 bytes | Vendor-specific |

Live parses against a Chutes TEE chute (wave-2 2026-04-13, re-verified 2026-06-11) confirmed `version=4, att_key_type=2, tee_type=0x81`. `verify_quote.py` extracts and prints these.

## TD report body (584 bytes, starting at offset 48)

This is the core — the measurements that prove what ran inside the TD.

| Offset (rel) | Field | Size | Meaning |
|---|---|---|---|
| 0 | `tee_tcb_svn` | 16 bytes | TDX module SVN |
| 16 | `mrseam` | 48 bytes | Measurement of SEAM module |
| 64 | `mrsignerseam` | 48 bytes | Signer of SEAM module (always zero in TDX v4) |
| 112 | `seamattributes` | 8 bytes | |
| 120 | `tdattributes` | 8 bytes | |
| 128 | `xfam` | 8 bytes | |
| 136 | `mrtd` | 48 bytes | **Measurement of the TD (container)** |
| 184 | `mrconfigid` | 48 bytes | TD config identifier |
| 232 | `mrowner` | 48 bytes | TD owner (typically zero) |
| 280 | `mrownerconfig` | 48 bytes | TD owner config (typically zero) |
| 328 | `rtmr[0]` | 48 bytes | Runtime measurement 0 |
| 376 | `rtmr[1]` | 48 bytes | Runtime measurement 1 |
| 424 | `rtmr[2]` | 48 bytes | Runtime measurement 2 |
| 472 | `rtmr[3]` | 48 bytes | Runtime measurement 3 |
| 520 | `report_data` | 64 bytes | User-controlled — **nonce commitment lives here** |

The **`report_data`** field is where the caller's nonce (what `fetch_evidence.py` supplies as `?nonce=...`) is committed into the quote. A valid quote's `report_data` must incorporate the nonce; otherwise the attestation can be replayed. The bundled scripts extract and print `report_data` but do **not** verify the binding (no `--check-nonce` flag exists as of 2026-06-11). Live check 2026-06-11: `report_data` is not the literal nonce hex nor a plain SHA-256/384 of the nonce bytes — the commitment derivation is undocumented (unverified as of 2026-06-11), so a real binding check needs Chutes' scheme.

**`mrtd`** is the measurement of the trust domain — effectively a hash of what code is running inside the TD. Change the code, and `mrtd` changes. Chutes publishes golden `mrtd` + RTMR sets per server class at `GET /servers/tee/measurements` (public; verified 2026-06-11) — compare against those, and/or capture a reference `mrtd` for a known-good release and alert on drift.

## Auth data (variable)

Contains:
- ECDSA signature over the (header + body)
- Attestation key (ECDSA public key)
- QE report (which attests the quoting enclave itself)
- Cert chain anchored at Intel's root

This section is what DCAP verifies cryptographically. Without DCAP, `verify_quote.py` reports the auth data size and leaves it at that.

## What the skill actually parses

`verify_quote.py` (shape-only mode):

- All 12 header fields (byte-exact).
- `mrtd`, `mrconfigid`, `rtmr[0..3]`, `report_data` from the body (printed as hex).
- Auth data size.

It does NOT:
- Verify the ECDSA signature.
- Walk the cert chain to Intel's root.
- Check `seamattributes` / `tdattributes` bits for policy compliance.

Those belong to full-crypto mode, which requires DCAP.

## Further reading

- Intel DCAP docs: <https://download.01.org/intel-sgx/latest/dcap-latest/linux/docs/>
- TDX v4 spec sections on attestation quote layout.
- NVIDIA Confidential Compute attestation (Hopper and Blackwell): <https://docs.nvidia.com/confidential-computing/>
