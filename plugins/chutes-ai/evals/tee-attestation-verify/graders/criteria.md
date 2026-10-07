---
type: llm
weight: 1
---

Should route to chutes-tee:attest_chute.py. Must GET /instances/nonce or generate a 64-hex nonce via secrets.token_hex(32), then GET /chutes/{id}/evidence?nonce=<nonce> (wave-2 finding: nonce query param is REQUIRED and must be exactly 64 hex chars), parse the TDX v4 quote header (version=4, tee_type=0x81, att_key_type=2), extract mrtd + rtmr[0..3] + report_data, parse one NVIDIA GPU certificate (arch is fleet-dependent - Blackwell observed live 2026-06-11, Hopper previously; do not hardcode), optionally cross-check mrtd/rtmr0 against the public GET /servers/tee/measurements golden sets, and return a verdict of 'shape-valid' if crypto validation isn't available (explicitly labeled 'not run - install Intel DCAP for verified mode'). Must NOT claim 'verified' unless DCAP tooling actually ran. Must explain honest limits of TEE (see references/what-tee-does-not-protect.md).
