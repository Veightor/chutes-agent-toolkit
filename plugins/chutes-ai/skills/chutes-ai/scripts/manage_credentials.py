#!/usr/bin/env python3
"""
Chutes.ai secure credential manager.

Stores secrets in macOS Keychain (primary), Linux secret-tool, or an
AES-256-GCM encrypted file (fallback). Non-secret metadata lives in
~/.chutes/config (INI, chmod 600).

Commands:
  set-profile   Save or update a full credential profile
  set           Update a single field in a profile
  get           Read a credential field (raw value to stdout)
  list-profiles List all configured profiles
  delete        Remove a profile and its secrets
  check         Show status without revealing secrets

Exit codes: 0=success, 1=not found, 2=backend error

Usage examples:
  python manage_credentials.py set-profile --username alice --user-id UUID --fingerprint FP --api-key cpk_...
  python manage_credentials.py get --field api_key
  python manage_credentials.py get --profile production --field fingerprint
  python manage_credentials.py check
"""

import argparse
import configparser
import hashlib
import json
import os
import platform
import shutil
import stat
import subprocess
import sys
from pathlib import Path
from typing import Optional

CHUTES_DIR = Path.home() / ".chutes"
CONFIG_FILE = CHUTES_DIR / "config"
ENCRYPTED_FILE = CHUTES_DIR / ".keychain"
GITIGNORE_FILE = CHUTES_DIR / ".gitignore"

SERVICE_NAME = "chutes-ai"

SECRET_FIELDS = {"api_key", "fingerprint", "client_id", "client_secret", "app_id"}
METADATA_FIELDS = {"username", "user_id"}
ALL_FIELDS = SECRET_FIELDS | METADATA_FIELDS

ENV_OVERRIDES = {
    "api_key": ("CHUTES_API_KEY",),
    "fingerprint": ("CHUTES_FINGERPRINT",),
    "client_id": ("CHUTES_OAUTH_CLIENT_ID", "CHUTES_CLIENT_ID"),
    "client_secret": ("CHUTES_OAUTH_CLIENT_SECRET", "CHUTES_CLIENT_SECRET"),
}


def env_override_value(field: str) -> Optional[str]:
    """Return the first matching env var value for a field, or None."""
    for env_var in ENV_OVERRIDES.get(field, ()):
        val = os.environ.get(env_var)
        if val:
            return val
    return None


# ---------------------------------------------------------------------------
# Directory & config helpers
# ---------------------------------------------------------------------------

def ensure_chutes_dir():
    """Create ~/.chutes/ with secure permissions."""
    CHUTES_DIR.mkdir(mode=0o700, parents=True, exist_ok=True)
    # Enforce directory permissions even if it already existed
    CHUTES_DIR.chmod(0o700)
    if not GITIGNORE_FILE.exists():
        GITIGNORE_FILE.write_text("*\n")


def load_config() -> configparser.ConfigParser:
    cp = configparser.ConfigParser()
    if CONFIG_FILE.exists():
        cp.read(CONFIG_FILE)
    return cp


def save_config(cp: configparser.ConfigParser):
    ensure_chutes_dir()
    with open(CONFIG_FILE, "w") as f:
        cp.write(f)
    CONFIG_FILE.chmod(0o600)


def resolve_profile(args_profile: Optional[str]) -> str:
    if args_profile:
        return args_profile
    return os.environ.get("CHUTES_PROFILE", "default")


# ---------------------------------------------------------------------------
# Backend detection
# ---------------------------------------------------------------------------

def detect_backend() -> str:
    if platform.system() == "Darwin" and shutil.which("security"):
        return "keychain"
    if platform.system() == "Linux" and shutil.which("secret-tool"):
        return "linux_secretservice"
    return "encrypted_file"


# ---------------------------------------------------------------------------
# macOS Keychain backend
# ---------------------------------------------------------------------------

def _keychain_write(profile: str, secrets: dict):
    """Write a JSON blob to macOS Keychain."""
    payload = json.dumps(secrets, separators=(",", ":"))
    result = subprocess.run(
        [
            "security", "add-generic-password",
            "-s", SERVICE_NAME,
            "-a", profile,
            "-U",  # upsert
            "-w", payload,
        ],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        print(
            f"Keychain write failed (rc={result.returncode}): {result.stderr.strip()}",
            file=sys.stderr,
        )
        sys.exit(2)


def _keychain_read(profile: str) -> Optional[dict]:
    """Read a JSON blob from macOS Keychain."""
    result = subprocess.run(
        [
            "security", "find-generic-password",
            "-s", SERVICE_NAME,
            "-a", profile,
            "-w",
        ],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        return None
    raw = result.stdout.strip()
    if not raw:
        return None
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        print(
            f"Corrupt credential data for profile '{profile}'. "
            f"Run: manage_credentials.py delete --profile {profile} and re-save.",
            file=sys.stderr,
        )
        sys.exit(2)


def _keychain_delete(profile: str):
    subprocess.run(
        [
            "security", "delete-generic-password",
            "-s", SERVICE_NAME,
            "-a", profile,
        ],
        capture_output=True,
    )


# ---------------------------------------------------------------------------
# Linux secret-tool backend
# ---------------------------------------------------------------------------

def _secretservice_write(profile: str, secrets: dict):
    payload = json.dumps(secrets, separators=(",", ":"))
    proc = subprocess.Popen(
        [
            "secret-tool", "store",
            "--label", f"{SERVICE_NAME} ({profile})",
            "service", SERVICE_NAME,
            "profile", profile,
        ],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    stdout, stderr = proc.communicate(input=payload.encode())
    if proc.returncode != 0:
        print(
            f"secret-tool write failed (rc={proc.returncode}): {stderr.decode().strip()}",
            file=sys.stderr,
        )
        sys.exit(2)


def _secretservice_read(profile: str) -> Optional[dict]:
    result = subprocess.run(
        [
            "secret-tool", "lookup",
            "service", SERVICE_NAME,
            "profile", profile,
        ],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0 or not result.stdout.strip():
        return None
    try:
        return json.loads(result.stdout.strip())
    except json.JSONDecodeError:
        print(
            f"Corrupt credential data for profile '{profile}'. "
            f"Run: manage_credentials.py delete --profile {profile} and re-save.",
            file=sys.stderr,
        )
        sys.exit(2)


def _secretservice_delete(profile: str):
    subprocess.run(
        [
            "secret-tool", "clear",
            "service", SERVICE_NAME,
            "profile", profile,
        ],
        capture_output=True,
    )


# ---------------------------------------------------------------------------
# Encrypted file backend (AES-256-GCM fallback)
# ---------------------------------------------------------------------------

def _derive_key() -> bytes:
    """Derive an encryption key from machine identity."""
    identity_parts = []
    machine_id_path = Path("/etc/machine-id")
    if machine_id_path.exists():
        identity_parts.append(machine_id_path.read_text().strip())
    identity_parts.append(str(os.getuid()))
    identity_parts.append(os.environ.get("HOME", str(Path.home())))
    identity_parts.append(platform.node())
    combined = "|".join(identity_parts).encode()
    return hashlib.pbkdf2_hmac("sha256", combined, b"chutes-ai-credential-store", 600_000)


def _encrypted_file_read_all() -> dict:
    """Read all profiles from the encrypted file."""
    if not ENCRYPTED_FILE.exists():
        return {}
    try:
        from cryptography.hazmat.primitives.ciphers.aead import AESGCM
    except ImportError:
        print(
            "The 'cryptography' package is required for encrypted file backend. "
            "Install with: pip install cryptography",
            file=sys.stderr,
        )
        sys.exit(2)
    raw = ENCRYPTED_FILE.read_bytes()
    if len(raw) < 13:  # 12-byte nonce + at least 1 byte
        return {}
    nonce = raw[:12]
    ciphertext = raw[12:]
    key = _derive_key()
    aesgcm = AESGCM(key)
    try:
        plaintext = aesgcm.decrypt(nonce, ciphertext, None)
    except Exception:
        print("Failed to decrypt credential store. Machine identity may have changed.", file=sys.stderr)
        sys.exit(2)
    return json.loads(plaintext)


def _encrypted_file_write_all(data: dict):
    """Write all profiles to the encrypted file."""
    try:
        from cryptography.hazmat.primitives.ciphers.aead import AESGCM
    except ImportError:
        print(
            "The 'cryptography' package is required for encrypted file backend. "
            "Install with: pip install cryptography",
            file=sys.stderr,
        )
        sys.exit(2)
    ensure_chutes_dir()
    key = _derive_key()
    aesgcm = AESGCM(key)
    nonce = os.urandom(12)
    plaintext = json.dumps(data, separators=(",", ":")).encode()
    ciphertext = aesgcm.encrypt(nonce, plaintext, None)
    ENCRYPTED_FILE.write_bytes(nonce + ciphertext)
    ENCRYPTED_FILE.chmod(0o600)


def _encrypted_file_read(profile: str) -> Optional[dict]:
    all_data = _encrypted_file_read_all()
    return all_data.get(profile)


def _encrypted_file_write(profile: str, secrets: dict):
    all_data = _encrypted_file_read_all()
    all_data[profile] = secrets
    _encrypted_file_write_all(all_data)


def _encrypted_file_delete(profile: str):
    all_data = _encrypted_file_read_all()
    all_data.pop(profile, None)
    if all_data:
        _encrypted_file_write_all(all_data)
    elif ENCRYPTED_FILE.exists():
        ENCRYPTED_FILE.unlink()


# ---------------------------------------------------------------------------
# Unified secret operations
# ---------------------------------------------------------------------------

def write_secrets(backend: str, profile: str, secrets: dict):
    if backend == "keychain":
        _keychain_write(profile, secrets)
    elif backend == "linux_secretservice":
        _secretservice_write(profile, secrets)
    else:
        _encrypted_file_write(profile, secrets)


def read_secrets(backend: str, profile: str) -> Optional[dict]:
    if backend == "keychain":
        return _keychain_read(profile)
    elif backend == "linux_secretservice":
        return _secretservice_read(profile)
    else:
        return _encrypted_file_read(profile)


def delete_secrets(backend: str, profile: str):
    if backend == "keychain":
        _keychain_delete(profile)
    elif backend == "linux_secretservice":
        _secretservice_delete(profile)
    else:
        _encrypted_file_delete(profile)


# ---------------------------------------------------------------------------
# Commands
# ---------------------------------------------------------------------------

def cmd_set_profile(args):
    profile = resolve_profile(args.profile)
    backend = detect_backend()
    cp = load_config()

    # Read existing secrets for merge
    existing_secrets = {}
    if cp.has_section(profile):
        existing_backend = cp.get(profile, "backend", fallback=backend)
        existing_secrets = read_secrets(existing_backend, profile) or {}
    else:
        existing_secrets = read_secrets(backend, profile) or {}

    # Build secret fields from args
    secret_updates = {}
    for field in SECRET_FIELDS:
        val = getattr(args, field, None)
        if val is not None:
            secret_updates[field] = val
    merged_secrets = {**existing_secrets, **secret_updates}

    if not merged_secrets and not args.username and not args.user_id:
        print("No credentials provided. Use --api-key, --fingerprint, --username, etc.", file=sys.stderr)
        sys.exit(1)

    # Write secrets to backend
    if merged_secrets:
        write_secrets(backend, profile, merged_secrets)

    # Update config with metadata
    if not cp.has_section(profile):
        cp.add_section(profile)
    cp.set(profile, "backend", backend)
    if args.username:
        cp.set(profile, "username", args.username)
    if args.user_id:
        cp.set(profile, "user_id", args.user_id)

    save_config(cp)
    print(f"Profile '{profile}' saved (backend: {backend})", file=sys.stderr)


def cmd_set(args):
    profile = resolve_profile(args.profile)
    cp = load_config()
    backend = detect_backend()

    if cp.has_section(profile):
        backend = cp.get(profile, "backend", fallback=backend)

    if args.field in SECRET_FIELDS:
        existing = read_secrets(backend, profile) or {}
        existing[args.field] = args.value
        write_secrets(backend, profile, existing)
        # Ensure profile exists in config
        if not cp.has_section(profile):
            cp.add_section(profile)
            cp.set(profile, "backend", backend)
            save_config(cp)
    elif args.field in METADATA_FIELDS:
        if not cp.has_section(profile):
            cp.add_section(profile)
            cp.set(profile, "backend", backend)
        cp.set(profile, args.field, args.value)
        save_config(cp)
    else:
        print(
            f"Unknown field '{args.field}'. "
            f"Valid: {', '.join(sorted(ALL_FIELDS))}",
            file=sys.stderr,
        )
        sys.exit(1)

    print(f"Updated '{args.field}' in profile '{profile}'", file=sys.stderr)


def cmd_get(args):
    profile = resolve_profile(args.profile)

    # Environment variable override (highest priority)
    if args.field and args.field in ENV_OVERRIDES:
        env_val = env_override_value(args.field)
        if env_val:
            print(env_val)
            return

    cp = load_config()
    backend = detect_backend()
    if cp.has_section(profile):
        backend = cp.get(profile, "backend", fallback=backend)
    else:
        print(f"Profile '{profile}' not found.", file=sys.stderr)
        sys.exit(1)

    # Check metadata fields
    if args.field and args.field in METADATA_FIELDS:
        val = cp.get(profile, args.field, fallback=None)
        if val:
            print(val)
            return
        print(f"Field '{args.field}' not set in profile '{profile}'.", file=sys.stderr)
        sys.exit(1)

    # Read secrets
    secrets = read_secrets(backend, profile) or {}
    if not secrets and args.field in SECRET_FIELDS:
        print(f"No secrets found for profile '{profile}'.", file=sys.stderr)
        sys.exit(1)

    if args.field:
        val = secrets.get(args.field)
        if val is None:
            print(f"Field '{args.field}' not set in profile '{profile}'.", file=sys.stderr)
            sys.exit(1)
        print(val)
    else:
        # Return all fields as JSON (secrets + metadata)
        result = {}
        if cp.has_section(profile):
            for key in METADATA_FIELDS:
                val = cp.get(profile, key, fallback=None)
                if val:
                    result[key] = val
        result.update(secrets)
        print(json.dumps(result, indent=2))


def cmd_list_profiles(args):
    cp = load_config()
    profiles = cp.sections()
    print(json.dumps(profiles))


def cmd_delete(args):
    profile = resolve_profile(args.profile)
    cp = load_config()
    backend = detect_backend()

    if cp.has_section(profile):
        backend = cp.get(profile, "backend", fallback=backend)
        cp.remove_section(profile)
        save_config(cp)

    delete_secrets(backend, profile)
    print(f"Profile '{profile}' deleted.", file=sys.stderr)


def cmd_check(args):
    backend = detect_backend()
    cp = load_config()
    profiles = cp.sections()

    result = {
        "status": "ok",
        "backend": backend,
        "config_file": str(CONFIG_FILE),
        "config_exists": CONFIG_FILE.exists(),
        "profiles": profiles,
    }

    if CONFIG_FILE.exists():
        mode = oct(stat.S_IMODE(CONFIG_FILE.stat().st_mode))
        result["config_permissions"] = mode
        result["config_secure"] = mode == "0o600"

    if CHUTES_DIR.exists():
        dir_mode = oct(stat.S_IMODE(CHUTES_DIR.stat().st_mode))
        result["dir_permissions"] = dir_mode
        result["dir_secure"] = dir_mode == "0o700"

    result["gitignore_exists"] = GITIGNORE_FILE.exists()
    if GITIGNORE_FILE.exists():
        result["gitignore_secure"] = GITIGNORE_FILE.read_text() == "*\n"

    result["encrypted_file_exists"] = ENCRYPTED_FILE.exists()
    if ENCRYPTED_FILE.exists():
        encrypted_mode = oct(stat.S_IMODE(ENCRYPTED_FILE.stat().st_mode))
        result["encrypted_file_permissions"] = encrypted_mode
        result["encrypted_file_secure"] = encrypted_mode == "0o600"

    # Check for env overrides
    active_env = {}
    for field, env_vars in ENV_OVERRIDES.items():
        for env_var in env_vars:
            if os.environ.get(env_var):
                active_env[field] = env_var
                break
    if active_env:
        result["env_overrides"] = active_env

    print(json.dumps(result, indent=2))


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Chutes.ai secure credential manager",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    sub = parser.add_subparsers(dest="command", required=True)

    # set-profile
    sp = sub.add_parser("set-profile", help="Save/update a full credential profile")
    sp.add_argument("--profile", default=None, help="Profile name (default: 'default')")
    sp.add_argument("--username", default=None, help="Chutes username")
    sp.add_argument("--user-id", dest="user_id", default=None, help="User UUID")
    sp.add_argument("--fingerprint", default=None, help="32-character fingerprint")
    sp.add_argument("--api-key", dest="api_key", default=None, help="API key (cpk_...)")
    sp.add_argument("--client-id", dest="client_id", default=None, help="OAuth client ID (cid_...)")
    sp.add_argument("--client-secret", dest="client_secret", default=None, help="OAuth client secret (csc_...)")

    # set
    sp = sub.add_parser("set", help="Update a single field")
    sp.add_argument("--profile", default=None, help="Profile name")
    sp.add_argument("--field", required=True, help="Field name")
    sp.add_argument("--value", required=True, help="Field value")

    # get
    sp = sub.add_parser("get", help="Read a credential field")
    sp.add_argument("--profile", default=None, help="Profile name")
    sp.add_argument("--field", default=None, help="Specific field (omit for all as JSON)")

    # list-profiles
    sub.add_parser("list-profiles", help="List configured profiles")

    # delete
    sp = sub.add_parser("delete", help="Remove a profile")
    sp.add_argument("--profile", required=True, help="Profile to delete")

    # check
    sub.add_parser("check", help="Show status without revealing secrets")

    args = parser.parse_args()

    commands = {
        "set-profile": cmd_set_profile,
        "set": cmd_set,
        "get": cmd_get,
        "list-profiles": cmd_list_profiles,
        "delete": cmd_delete,
        "check": cmd_check,
    }
    commands[args.command](args)


if __name__ == "__main__":
    main()
