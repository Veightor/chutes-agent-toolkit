# Intel DCAP Trust Root — Notes

> How to go beyond `shape-valid` to `verified` in `chutes-tee`.

## The two trust roots

1. **Intel DCAP** — anchors the TDX quote's signature chain up to Intel's SGX root CA. `chutes-tee` uses DCAP tooling via subprocess when available.
2. **NVIDIA GPU attestation** — anchors the per-GPU attestation report up to NVIDIA's trust root. Less mature tooling; `chutes-tee` falls back to X.509 cert validity + subject check without NVIDIA-specific verification.

## Installing Intel DCAP on macOS / Linux

### Option 1: Intel's official Python bindings

```bash
pip install sgx-dcap-quote-verify-python
```

Availability is patchy on macOS (Intel primarily ships for Linux). On Ubuntu 22.04+:

```bash
echo 'deb [arch=amd64] https://download.01.org/intel-sgx/sgx_repo/ubuntu jammy main' | sudo tee /etc/apt/sources.list.d/intel-sgx.list
wget -qO - https://download.01.org/intel-sgx/sgx_repo/ubuntu/intel-sgx-deb.key | sudo apt-key add -
sudo apt update && sudo apt install -y libsgx-dcap-default-qpl libsgx-dcap-quote-verify
pip install sgx-dcap-quote-verify-python
```

### Option 2: CLI binary

Intel also ships `QuoteVerify` as a standalone CLI in the DCAP release archive. `chutes-tee` scripts will use `sgx-dcap-quote-verify` on PATH if the Python binding isn't importable.

### Option 3: Containerized verifier

Run verification inside Intel's reference container and pipe JSON in/out:

```bash
docker run --rm -i intelsgx/dcap-quote-verify < quote.bin
```

Not auto-wired into the skill; use manually as a fallback.

## Trust root refresh

DCAP's root CA certificates expire and rotate periodically. The `sgx-dcap-default-qpl` package ships with a refresh policy; in long-running deployments you want it updated at least monthly. If the root is stale, quotes that were otherwise valid will fail verification — a false negative that looks like a real attack.

`chutes-tee` does NOT handle DCAP root refresh; that's an OS/package-manager concern.

## NVIDIA GPU trust root

As of wave-2 (2026-04), NVIDIA's standalone GPU attestation verifier is less developed than Intel's. Options:

- `nv-trust` if available on your system.
- Parse the GPU certificate manually and verify against NVIDIA's published root (PEM from <https://kb.nvidia.com/>).
- `attest_chute.py` falls back to X.509 cert parsing + validity + subject check when no NVIDIA verifier is present.

Note the fleet now includes Blackwell-class GPUs: the 2026-06-11 live probe returned `arch: BLACKWELL` with a GB20X cert chain (`CN=GB20X A01 GSP FMC LF` issued by `CN=GB20X A01 GSP BROM`, `ecdsa-with-SHA384`) — make sure whatever NVIDIA verifier you use supports Blackwell attestation, not just Hopper.

## Graduation rule for `chutes-tee`

**[BETA] Implementation status (2026-06-11):** this graduation rule is the spec, not current behavior — the bundled scripts detect DCAP availability but do not yet execute the validation pipeline, so the practical verdict ceiling is `shape-valid`. Run DCAP / `nv-trust` manually against a saved envelope to get cryptographic assurance today.

The skill outputs `verdict: verified` only when:

1. Intel DCAP is importable or the CLI is on PATH, AND
2. The quote passed `verify_quote(raw_bytes)` against the current Intel trust root, AND
3. Each `gpu_evidence` cert parses and validates against the issuer chain, AND
4. The nonce in the request matches a nonce commitment in the quote's `report_data`.

Short of any of those, the verdict stays `shape-valid` and the output says loudly what's missing.
