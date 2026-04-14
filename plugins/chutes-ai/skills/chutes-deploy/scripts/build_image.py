#!/usr/bin/env python3
"""Build a chute image via POST /images/ (multipart upload). [BETA]

Usage:
  python build_image.py \
    --dockerfile /path/to/Dockerfile \
    --context /path/to/context \
    --name my-org/my-chute \
    --tag v1

What it does:
  1. Tars the build context.
  2. Multipart-uploads the tar + Dockerfile to POST /images/.
  3. Streams GET /images/{image_id}/logs until the build terminates.
  4. Prints the resulting image_id.

Exit codes:
  0 built
  1 bad input
  2 Chutes API error or build failure

Note: multipart upload uses urllib.request manually to avoid a third-party
dependency. If the repo adopts httpx or requests, migrate this to that.
"""
from __future__ import annotations

import argparse
import io
import mimetypes
import os
import sys
import tarfile
import urllib.request
from pathlib import Path

from _common import api_key, idp_request, CHUTES_API_BASE
from deploy_vllm import stream_build_logs  # noqa: E402


def tar_context(context_dir: Path) -> bytes:
    buf = io.BytesIO()
    with tarfile.open(fileobj=buf, mode="w:gz") as tar:
        tar.add(str(context_dir), arcname=".")
    return buf.getvalue()


def multipart_upload(url: str, bearer: str, fields: dict, files: dict) -> dict:
    """Minimal multipart/form-data POST with no third-party deps."""
    boundary = f"----chutes-build-{os.urandom(8).hex()}"
    body = io.BytesIO()

    def write_field(name: str, value: str) -> None:
        body.write(f"--{boundary}\r\n".encode())
        body.write(f'Content-Disposition: form-data; name="{name}"\r\n\r\n'.encode())
        body.write(value.encode())
        body.write(b"\r\n")

    def write_file(name: str, filename: str, content: bytes, content_type: str) -> None:
        body.write(f"--{boundary}\r\n".encode())
        body.write(
            f'Content-Disposition: form-data; name="{name}"; filename="{filename}"\r\n'.encode()
        )
        body.write(f"Content-Type: {content_type}\r\n\r\n".encode())
        body.write(content)
        body.write(b"\r\n")

    for k, v in fields.items():
        write_field(k, v)
    for k, (filename, content, content_type) in files.items():
        write_file(k, filename, content, content_type)

    body.write(f"--{boundary}--\r\n".encode())
    payload = body.getvalue()

    req = urllib.request.Request(
        url,
        data=payload,
        headers={
            "Authorization": f"Bearer {bearer}",
            "Content-Type": f"multipart/form-data; boundary={boundary}",
            "Accept": "application/json",
        },
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=600) as resp:
        import json as _json

        return _json.loads(resp.read().decode("utf-8"))


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--dockerfile", required=True)
    p.add_argument("--context", required=True)
    p.add_argument("--name", required=True, help="image name (e.g. my-org/my-chute)")
    p.add_argument("--tag", default="latest")
    p.add_argument("--dry-run", action="store_true")
    args = p.parse_args()

    dockerfile = Path(args.dockerfile).expanduser().resolve()
    context = Path(args.context).expanduser().resolve()
    if not dockerfile.exists():
        print(f"error: Dockerfile not found: {dockerfile}", file=sys.stderr)
        return 1
    if not context.is_dir():
        print(f"error: context dir not found: {context}", file=sys.stderr)
        return 1

    print(f"!! BETA — building a chute image.")
    print(f"   name:       {args.name}:{args.tag}")
    print(f"   dockerfile: {dockerfile}")
    print(f"   context:    {context}")

    if args.dry_run:
        print("dry-run: would POST /images/ with multipart body")
        return 0

    try:
        confirm = input("Proceed? [y/N]: ").strip().lower()
    except EOFError:
        confirm = ""
    if confirm not in ("y", "yes"):
        print("aborted.")
        return 1

    try:
        bearer = api_key()
    except RuntimeError as e:
        print(f"error: {e}", file=sys.stderr)
        return 1

    print("tarring build context…")
    tar_bytes = tar_context(context)
    dockerfile_bytes = dockerfile.read_bytes()

    fields = {"name": args.name, "tag": args.tag}
    files = {
        "dockerfile": ("Dockerfile", dockerfile_bytes, "text/plain"),
        "context": ("context.tar.gz", tar_bytes, "application/gzip"),
    }

    url = CHUTES_API_BASE.rstrip("/") + "/images/"
    print(f"POST {url} …")
    try:
        resp = multipart_upload(url, bearer, fields, files)
    except Exception as e:
        print(f"error: upload failed: {e}", file=sys.stderr)
        return 2

    image_id = resp.get("image_id") or resp.get("id")
    if not image_id:
        print(f"error: response missing image_id: {resp}", file=sys.stderr)
        return 2

    print(f"  image_id: {image_id}")
    print("streaming build logs…")
    if not stream_build_logs(bearer, image_id):
        return 2

    print(f"\nBUILT. image_id: {image_id}")
    print("Deploy with: python deploy_custom.py --image-id <id> --entrypoint my_module:chute --gpu h100 --name my-chute")
    return 0


if __name__ == "__main__":
    sys.exit(main())
