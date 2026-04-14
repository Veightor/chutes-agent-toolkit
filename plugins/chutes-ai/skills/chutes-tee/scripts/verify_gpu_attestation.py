#!/usr/bin/env python3
"""Parse a single NVIDIA GPU attestation record from a Chutes evidence envelope.

Usage:
  python verify_gpu_attestation.py --input <evidence.json> [--instance 0] [--gpu 0]

Shape-only parse: extracts arch, evidence size, and X.509 certificate
metadata (subject, issuer, validity). Does NOT verify the certificate
against NVIDIA's trust root — that requires nv-trust or an equivalent.

Exit codes:
  0 shape-valid
  1 bad input
  2 shape-invalid
"""
from __future__ import annotations

import argparse
import base64
import json
import sys
from pathlib import Path


def parse_cert_metadata(pem_bytes: bytes) -> dict:
    """Parse an X.509 certificate. Uses `cryptography` if available, else regex fallback."""
    try:
        from cryptography import x509
        from cryptography.hazmat.backends import default_backend
    except ImportError:
        # Fallback: regex the PEM header to confirm it's a cert
        head = pem_bytes[:100].decode("ascii", errors="replace")
        is_cert = "BEGIN CERTIFICATE" in head
        return {
            "parsed": False,
            "reason": "cryptography package not installed",
            "looks_like_pem": is_cert,
            "bytes": len(pem_bytes),
        }
    try:
        cert = x509.load_pem_x509_certificate(pem_bytes, default_backend())
    except Exception as e:
        return {"parsed": False, "error": str(e)}
    # Prefer the timezone-aware UTC accessors on cryptography >= 42; fall back
    # to the older naive accessors for compatibility.
    nvb = getattr(cert, "not_valid_before_utc", None) or cert.not_valid_before
    nva = getattr(cert, "not_valid_after_utc", None) or cert.not_valid_after
    return {
        "parsed": True,
        "subject": cert.subject.rfc4514_string(),
        "issuer": cert.issuer.rfc4514_string(),
        "not_valid_before": nvb.isoformat(),
        "not_valid_after": nva.isoformat(),
        "signature_algorithm": cert.signature_algorithm_oid._name,
        "serial_number": hex(cert.serial_number),
    }


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--input", required=True)
    p.add_argument("--instance", type=int, default=0)
    p.add_argument("--gpu", type=int, default=0)
    p.add_argument("--json", action="store_true")
    args = p.parse_args()

    try:
        envelope = json.loads(Path(args.input).read_text())
    except Exception as e:
        print(f"error: {e}", file=sys.stderr)
        return 1

    ev = envelope.get("evidence", []) if isinstance(envelope, dict) else []
    if args.instance >= len(ev):
        print(f"error: instance {args.instance} out of range ({len(ev)})", file=sys.stderr)
        return 1
    gpus = ev[args.instance].get("gpu_evidence", [])
    if args.gpu >= len(gpus):
        print(f"error: gpu {args.gpu} out of range ({len(gpus)})", file=sys.stderr)
        return 1

    g = gpus[args.gpu]
    arch = g.get("arch", "?")
    evidence_b64 = g.get("evidence", "")
    cert_b64 = g.get("certificate", "")

    try:
        evidence_raw = base64.b64decode(evidence_b64)
    except Exception as e:
        print(f"SHAPE-INVALID: evidence not base64: {e}", file=sys.stderr)
        return 2
    try:
        cert_raw = base64.b64decode(cert_b64)
    except Exception as e:
        print(f"SHAPE-INVALID: certificate not base64: {e}", file=sys.stderr)
        return 2

    cert_meta = parse_cert_metadata(cert_raw)

    if args.json:
        print(json.dumps({
            "arch": arch,
            "evidence_bytes": len(evidence_raw),
            "certificate": cert_meta,
            "verdict": "shape-valid",
            "nvidia_chain_validation": "not-run",
        }, indent=2))
        return 0

    print(f"=== GPU evidence (instance {args.instance}, gpu {args.gpu}) ===")
    print(f"  arch:            {arch}")
    print(f"  evidence bytes:  {len(evidence_raw)} (decoded from {len(evidence_b64)} b64 chars)")
    print()
    print(f"  certificate:")
    if cert_meta.get("parsed"):
        print(f"    subject:         {cert_meta['subject']}")
        print(f"    issuer:          {cert_meta['issuer']}")
        print(f"    valid from:      {cert_meta['not_valid_before']}")
        print(f"    valid to:        {cert_meta['not_valid_after']}")
        print(f"    signature alg:   {cert_meta['signature_algorithm']}")
        print(f"    serial:          {cert_meta['serial_number']}")
    else:
        print(f"    parsed:          False")
        for k, v in cert_meta.items():
            if k != "parsed":
                print(f"    {k}: {v}")
    print()
    print(f"  verdict:         shape-valid")
    print(f"  nvidia chain:    not-run (install nv-trust or manual chain validation to enable)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
