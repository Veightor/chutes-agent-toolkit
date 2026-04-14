#!/usr/bin/env python3
"""One-shot: fetch TEE evidence -> parse quote + one GPU record -> verdict.

Usage:
  python attest_chute.py --chute-id <chute_id>
  python attest_chute.py --chute-id <chute_id> --instance 0 --gpu 0

Exit codes:
  0 shape-valid
  1 bad input / missing credentials
  2 shape-invalid / Chutes API error
"""
from __future__ import annotations

import argparse
import base64
import json
import secrets
import sys
import tempfile
from pathlib import Path

from _common import api_key, idp_request
from verify_quote import parse_header, parse_body, parse_auth_data_size
from verify_gpu_attestation import parse_cert_metadata


def dcap_available() -> bool:
    try:
        import sgx_dcap_quote_verify  # noqa: F401
        return True
    except ImportError:
        pass
    import shutil
    return shutil.which("sgx-dcap-quote-verify") is not None


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--chute-id", required=True)
    p.add_argument("--instance", type=int, default=0)
    p.add_argument("--gpu", type=int, default=0)
    p.add_argument("--save", help="save full envelope to this path (default: temp file cleaned on exit)")
    p.add_argument("--json", action="store_true")
    args = p.parse_args()

    try:
        bearer = api_key()
    except RuntimeError as e:
        print(f"error: {e}", file=sys.stderr)
        return 1

    nonce = secrets.token_hex(32)
    try:
        envelope = idp_request(
            "GET",
            f"/chutes/{args.chute_id}/evidence?nonce={nonce}",
            bearer=bearer,
            timeout=120,
        )
    except RuntimeError as e:
        print(f"error fetching evidence: {e}", file=sys.stderr)
        return 2

    ev = envelope.get("evidence") if isinstance(envelope, dict) else None
    failed = envelope.get("failed_instance_ids", []) if isinstance(envelope, dict) else []
    if not ev:
        print("SHAPE-INVALID: no evidence list in response", file=sys.stderr)
        return 2
    if args.instance >= len(ev):
        print(f"error: instance {args.instance} out of range ({len(ev)})", file=sys.stderr)
        return 1

    instance = ev[args.instance]
    quote_b64 = instance.get("quote", "")
    gpus = instance.get("gpu_evidence", [])

    try:
        raw = base64.b64decode(quote_b64)
        header = parse_header(raw)
        body = parse_body(raw)
        auth_size = parse_auth_data_size(raw)
    except Exception as e:
        print(f"SHAPE-INVALID quote: {e}", file=sys.stderr)
        return 2

    if args.gpu >= len(gpus):
        gpu_info: dict = {"error": f"gpu {args.gpu} out of range ({len(gpus)})"}
        gpu_cert = None
    else:
        g = gpus[args.gpu]
        try:
            cert_raw = base64.b64decode(g.get("certificate", ""))
            gpu_cert = parse_cert_metadata(cert_raw)
        except Exception as e:
            gpu_cert = {"parsed": False, "error": str(e)}
        gpu_info = {
            "arch": g.get("arch", "?"),
            "evidence_b64_len": len(g.get("evidence", "")),
            "certificate": gpu_cert,
        }

    crypto_available = dcap_available()
    verdict = "shape-valid"
    if failed:
        verdict = "shape-valid-with-failures"

    result = {
        "chute_id": args.chute_id,
        "nonce": nonce[:16] + "...",
        "instance_count": len(ev),
        "failed_instance_count": len(failed),
        "failed_instance_ids": failed,
        "selected_instance": args.instance,
        "selected_instance_id": instance.get("instance_id"),
        "quote": {
            "raw_bytes": len(raw),
            "version": header["version"],
            "tee_type": f"0x{header['tee_type']:08x}",
            "att_key_type": header["att_key_type"],
            "mrtd_prefix": body["mrtd"][:16] + "...",
            "report_data_prefix": body["report_data"][:16] + "...",
            "auth_data_size": auth_size,
        },
        "gpu_count": len(gpus),
        "gpu_selected": args.gpu,
        "gpu_info": gpu_info,
        "verdict": verdict,
        "cryptographic_validation": "dcap-available" if crypto_available else "not-run",
    }

    if args.save:
        Path(args.save).write_text(json.dumps(envelope, indent=2))

    if args.json:
        print(json.dumps(result, indent=2))
    else:
        print(f"=== chute attest: {args.chute_id} ===")
        print(f"  instances:          {len(ev)}  (failed: {len(failed)})")
        print(f"  selected instance:  {args.instance} ({result['selected_instance_id']})")
        print(f"  TDX quote version:  {header['version']}")
        print(f"  TDX tee_type:       0x{header['tee_type']:08x} ({'TDX' if header['tee_type'] == 0x81 else '?'})")
        print(f"  att_key_type:       {header['att_key_type']} ({'ECDSA P-256' if header['att_key_type'] == 2 else '?'})")
        print(f"  quote raw bytes:    {len(raw)}")
        print(f"  mrtd (prefix):      {body['mrtd'][:32]}...")
        print(f"  report_data pfx:    {body['report_data'][:32]}...")
        print(f"  auth_data size:     {auth_size} bytes")
        print()
        print(f"  GPUs attested:      {len(gpus)} (arch: {gpu_info.get('arch', '?')})")
        if gpu_cert and gpu_cert.get("parsed"):
            print(f"  GPU cert subject:   {gpu_cert['subject']}")
            print(f"  GPU cert valid to:  {gpu_cert['not_valid_after']}")
        elif gpu_cert:
            print(f"  GPU cert:           not parsed ({gpu_cert.get('reason') or gpu_cert.get('error', '?')})")
        print()
        print(f"  verdict:            {verdict}")
        print(f"  cryptographic validation: {'DCAP available (run --full to enable)' if crypto_available else 'not run — install Intel DCAP for verified mode'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
