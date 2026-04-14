#!/usr/bin/env python3
"""Parse a TDX v4 quote from a Chutes evidence envelope and print fields.

Usage:
  python verify_quote.py --input <evidence.json> [--instance 0]
  python verify_quote.py --quote-b64 <base64>

Shape-only parse. Extracts header + TD report body fields. Does NOT
verify the ECDSA signature or the cert chain — that requires Intel DCAP.
See references/dcap-trust-root.md for how to enable full verification.

Exit codes:
  0 shape-valid
  1 bad input
  2 shape-invalid (quote doesn't match TDX v4 spec)
"""
from __future__ import annotations

import argparse
import base64
import json
import struct
import sys
from pathlib import Path


def parse_header(raw: bytes) -> dict:
    if len(raw) < 48:
        raise ValueError(f"quote too short for header ({len(raw)} < 48)")
    fields: dict = {}
    fields["version"], = struct.unpack_from("<H", raw, 0)
    fields["att_key_type"], = struct.unpack_from("<H", raw, 2)
    fields["tee_type"], = struct.unpack_from("<I", raw, 4)
    fields["qe_svn"], = struct.unpack_from("<H", raw, 8)
    fields["pce_svn"], = struct.unpack_from("<H", raw, 10)
    fields["qe_vendor_id"] = raw[12:28].hex()
    fields["user_data"] = raw[28:48].hex()
    return fields


def parse_body(raw: bytes) -> dict:
    """TD report body starts at offset 48 and is 584 bytes."""
    if len(raw) < 48 + 584:
        raise ValueError(f"quote too short for TD body ({len(raw)} < {48 + 584})")
    body = raw[48 : 48 + 584]
    fields: dict = {}
    fields["tee_tcb_svn"] = body[0:16].hex()
    fields["mrseam"] = body[16:64].hex()
    fields["mrsignerseam"] = body[64:112].hex()
    fields["seamattributes"] = body[112:120].hex()
    fields["tdattributes"] = body[120:128].hex()
    fields["xfam"] = body[128:136].hex()
    fields["mrtd"] = body[136:184].hex()
    fields["mrconfigid"] = body[184:232].hex()
    fields["mrowner"] = body[232:280].hex()
    fields["mrownerconfig"] = body[280:328].hex()
    fields["rtmr0"] = body[328:376].hex()
    fields["rtmr1"] = body[376:424].hex()
    fields["rtmr2"] = body[424:472].hex()
    fields["rtmr3"] = body[472:520].hex()
    fields["report_data"] = body[520:584].hex()
    return fields


def parse_auth_data_size(raw: bytes) -> int:
    """After the 584-byte body, there's a 4-byte auth data size field."""
    offset = 48 + 584
    if len(raw) < offset + 4:
        return 0
    size, = struct.unpack_from("<I", raw, offset)
    return size


def load_quote_from_input(args: argparse.Namespace) -> bytes:
    if args.quote_b64:
        return base64.b64decode(args.quote_b64)
    if not args.input:
        raise ValueError("must provide --input or --quote-b64")
    envelope = json.loads(Path(args.input).read_text())
    ev = envelope.get("evidence") if isinstance(envelope, dict) else None
    if not ev:
        raise ValueError("envelope has no 'evidence' list")
    if args.instance >= len(ev):
        raise ValueError(f"instance {args.instance} out of range (have {len(ev)})")
    quote_b64 = ev[args.instance].get("quote")
    if not quote_b64:
        raise ValueError(f"instance {args.instance} has no 'quote' field")
    return base64.b64decode(quote_b64)


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--input", help="path to a Chutes evidence envelope JSON")
    p.add_argument("--instance", type=int, default=0, help="which evidence[] index to parse")
    p.add_argument("--quote-b64", help="base64 quote directly (skip envelope)")
    p.add_argument("--json", action="store_true")
    args = p.parse_args()

    try:
        raw = load_quote_from_input(args)
    except (ValueError, json.JSONDecodeError) as e:
        print(f"error: {e}", file=sys.stderr)
        return 1

    try:
        header = parse_header(raw)
        body = parse_body(raw)
    except ValueError as e:
        print(f"SHAPE-INVALID: {e}", file=sys.stderr)
        return 2

    auth_size = parse_auth_data_size(raw)

    if args.json:
        print(json.dumps({
            "raw_bytes": len(raw),
            "header": header,
            "body": body,
            "auth_data_size": auth_size,
            "verdict": "shape-valid",
            "cryptographic_validation": "not-run",
        }, indent=2))
        return 0

    print(f"=== TDX quote (instance {args.instance}) ===")
    print(f"  raw bytes:      {len(raw)}")
    print()
    print(f"  version:        {header['version']}")
    print(f"  att_key_type:   {header['att_key_type']} ({'ECDSA P-256' if header['att_key_type'] == 2 else '?'})")
    print(f"  tee_type:       0x{header['tee_type']:08x} ({'TDX' if header['tee_type'] == 0x81 else '?'})")
    print(f"  qe_svn:         0x{header['qe_svn']:04x}")
    print(f"  pce_svn:        0x{header['pce_svn']:04x}")
    print(f"  qe_vendor_id:   {header['qe_vendor_id']}")
    print(f"  user_data:      {header['user_data']}")
    print()
    print(f"  TD report body:")
    for k in ("mrtd", "mrconfigid", "rtmr0", "rtmr1", "rtmr2", "rtmr3", "report_data"):
        print(f"    {k:<14} {body[k]}")
    print()
    print(f"  auth_data_size: {auth_size} bytes")
    print()
    print(f"  verdict:        shape-valid")
    print(f"  cryptographic:  not-run (install Intel DCAP to enable)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
