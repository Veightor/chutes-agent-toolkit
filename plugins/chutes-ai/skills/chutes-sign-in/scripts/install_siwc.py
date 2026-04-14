#!/usr/bin/env python3
"""Vendor chutesai/Sign-in-with-Chutes Next.js files into a target app. [BETA]

Usage:
  python install_siwc.py --target /path/to/next-app --profile oauth.my-app

What it does (idempotent, prompts before overwriting):
  1. Detects target framework (Next.js App Router required; other frameworks stub out).
  2. Clones https://github.com/chutesai/Sign-in-with-Chutes at a pinned commit into a cache dir.
  3. Copies packages/nextjs/{lib,hooks,app/api/auth/chutes,components} into the target.
  4. Appends CHUTES_OAUTH_CLIENT_ID, CHUTES_OAUTH_CLIENT_SECRET, NEXT_PUBLIC_APP_URL
     to the target .env.local, reading values from the keychain profile.
  5. Prints a diff showing how to add <SignInButton /> to the root layout.
     Does NOT auto-edit layout files.

Exit codes:
  0 success
  1 bad input / framework unsupported / user aborted
  2 clone or filesystem error
"""
from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
import tempfile
from datetime import datetime
from pathlib import Path

from _common import get_secret

# Pin an upstream commit here to guarantee reproducibility.
# TODO(beta): pin to a verified SHA during the first live verification run.
SIWC_REPO = "https://github.com/chutesai/Sign-in-with-Chutes.git"
SIWC_PINNED_REF = "main"
CACHE_DIR = Path.home() / ".chutes" / "cache" / "siwc"

# Files relative to packages/nextjs/
FILES_TO_VENDOR = [
    "lib/chutesAuth.ts",
    "lib/serverAuth.ts",
    "hooks/useChutesSession.ts",
    "app/api/auth/chutes/login/route.ts",
    "app/api/auth/chutes/callback/route.ts",
    "app/api/auth/chutes/logout/route.ts",
    "app/api/auth/chutes/session/route.ts",
    "components/SignInButton.tsx",
]


def detect_framework(target: Path) -> str:
    """Return 'nextjs-app-router', 'nextjs-pages-router', 'express', 'fastapi', or 'unknown'."""
    pkg = target / "package.json"
    req = target / "requirements.txt"
    if pkg.exists():
        try:
            data = json.loads(pkg.read_text())
        except json.JSONDecodeError:
            data = {}
        deps = {**data.get("dependencies", {}), **data.get("devDependencies", {})}
        if "next" in deps:
            if (target / "src" / "app").exists() or (target / "app").exists():
                return "nextjs-app-router"
            if (target / "src" / "pages").exists() or (target / "pages").exists():
                return "nextjs-pages-router"
            return "nextjs-app-router"  # default for new projects
        if "express" in deps:
            return "express"
    if req.exists() and "fastapi" in req.read_text().lower():
        return "fastapi"
    return "unknown"


def app_root(target: Path) -> Path:
    """Return the destination root for app-router files ('src/app' or 'app')."""
    if (target / "src" / "app").exists():
        return target / "src"
    return target


def clone_siwc() -> Path:
    """Clone (or reuse cached) SIWC repo and return the packages/nextjs path."""
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    work = CACHE_DIR / SIWC_PINNED_REF
    if not work.exists():
        with tempfile.TemporaryDirectory(prefix="siwc-clone-") as tmp:
            tmp_path = Path(tmp) / "repo"
            try:
                subprocess.run(
                    ["git", "clone", "--depth", "1", "--branch", SIWC_PINNED_REF, SIWC_REPO, str(tmp_path)],
                    check=True,
                    capture_output=True,
                    text=True,
                )
            except subprocess.CalledProcessError as e:
                print(f"error: git clone failed: {e.stderr}", file=sys.stderr)
                raise SystemExit(2)
            shutil.move(str(tmp_path), str(work))
    nextjs_src = work / "packages" / "nextjs"
    if not nextjs_src.exists():
        print(
            f"error: {nextjs_src} does not exist in the cloned SIWC repo. "
            f"Upstream layout may have changed — update SIWC_PINNED_REF or FILES_TO_VENDOR.",
            file=sys.stderr,
        )
        raise SystemExit(2)
    return nextjs_src


def confirm(prompt: str) -> bool:
    try:
        reply = input(f"{prompt} [y/N]: ").strip().lower()
    except EOFError:
        return False
    return reply in ("y", "yes")


def copy_file(src: Path, dst: Path, force: bool) -> str:
    """Copy src → dst. Return 'copied', 'skipped', or 'overwritten'."""
    dst.parent.mkdir(parents=True, exist_ok=True)
    if dst.exists():
        if not force and not confirm(f"  {dst} exists. Overwrite?"):
            return "skipped"
        backup = dst.with_suffix(dst.suffix + f".bak-{datetime.now():%Y%m%d%H%M%S}")
        shutil.copy2(dst, backup)
        shutil.copy2(src, dst)
        return f"overwritten (backup: {backup.name})"
    shutil.copy2(src, dst)
    return "copied"


def append_env_local(target: Path, profile: str) -> None:
    env_file = target / ".env.local"
    existing = env_file.read_text() if env_file.exists() else ""
    client_id = get_secret("client_id", profile=profile)
    client_secret = get_secret("client_secret", profile=profile)
    app_url = "http://localhost:3000"

    entries = {
        "CHUTES_OAUTH_CLIENT_ID": client_id,
        "CHUTES_OAUTH_CLIENT_SECRET": client_secret,
        "NEXT_PUBLIC_APP_URL": app_url,
    }

    to_add = []
    for key, value in entries.items():
        if f"{key}=" in existing:
            print(f"  .env.local already has {key}, leaving it")
            continue
        to_add.append(f"{key}={value}")

    if to_add:
        with env_file.open("a") as f:
            if existing and not existing.endswith("\n"):
                f.write("\n")
            f.write("\n".join(to_add) + "\n")
        env_file.chmod(0o600)

    # Check gitignore
    gitignore = target / ".gitignore"
    if gitignore.exists() and ".env.local" not in gitignore.read_text():
        print(
            "  WARNING: .env.local is not in .gitignore. Add it before committing.",
            file=sys.stderr,
        )


def print_layout_diff(target: Path, framework: str) -> None:
    root = app_root(target)
    layout_candidates = [
        root / "app" / "layout.tsx",
        root / "app" / "layout.jsx",
    ]
    layout_path = next((p for p in layout_candidates if p.exists()), layout_candidates[0])
    print("\n--- Wire up the sign-in button -----------------------------------")
    print(f"Open {layout_path} and add the SignInButton import + render:")
    print()
    print("  import { SignInButton } from \"@/components/SignInButton\";")
    print()
    print("  // inside your <header> or nav:")
    print("  <SignInButton />")
    print()
    print("This script does NOT auto-edit layout files — apply the diff yourself.")


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--target", required=True, help="Path to the target Next.js project")
    p.add_argument("--profile", required=True, help="Keychain profile holding client_id/client_secret")
    p.add_argument("--force", action="store_true", help="Overwrite existing files without prompting")
    args = p.parse_args()

    target = Path(args.target).expanduser().resolve()
    if not target.exists():
        print(f"error: target {target} does not exist", file=sys.stderr)
        return 1

    framework = detect_framework(target)
    if framework == "nextjs-pages-router":
        print("error: Pages Router is not yet supported by upstream SIWC.", file=sys.stderr)
        print("       See plugins/chutes-ai/skills/chutes-sign-in/references/frameworks/", file=sys.stderr)
        return 1
    if framework in ("express", "fastapi"):
        print(f"error: {framework} is not yet supported by upstream SIWC.", file=sys.stderr)
        return 1
    if framework == "unknown":
        print("error: could not detect Next.js App Router in target.", file=sys.stderr)
        return 1

    print(f"Detected framework: {framework}")
    print(f"Target: {target}")

    print("Cloning SIWC upstream…")
    siwc_root = clone_siwc()
    print(f"Using SIWC source: {siwc_root}")

    dest_root = app_root(target)
    print(f"Destination root: {dest_root}")

    print("\nVendoring files:")
    results = {}
    for rel in FILES_TO_VENDOR:
        src = siwc_root / rel
        if not src.exists():
            print(f"  WARNING: upstream file missing: {rel}")
            results[rel] = "missing"
            continue
        dst = dest_root / rel
        results[rel] = copy_file(src, dst, force=args.force)
        print(f"  {rel}: {results[rel]}")

    print("\nWriting .env.local entries from keychain…")
    try:
        append_env_local(target, args.profile)
    except RuntimeError as e:
        print(f"error: {e}", file=sys.stderr)
        return 1

    print_layout_diff(target, framework)

    print("\nNext: `cd`, `npm run dev`, click SignInButton, then run verify_siwc.py.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
