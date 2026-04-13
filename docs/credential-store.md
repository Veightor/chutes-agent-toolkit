# Chutes Credential Store

This document explains how the Chutes credential manager works, what it stores, and how agents should invoke it safely.

Primary implementation:
- `plugins/chutes-ai/skills/chutes-ai/scripts/manage_credentials.py`

## Goals

The credential manager exists to let agents store and retrieve Chutes credentials without pushing secrets into:
- plaintext project files
- shell history
- process lists
- chat transcripts

Secrets should be retrievable across sessions and projects while remaining outside the repo itself.

## What gets stored

Secret fields:
- `api_key`
- `fingerprint`
- `client_id`
- `client_secret`

Non-secret metadata:
- `username`
- `user_id`

Storage split:
- secrets go to the active secret backend
- metadata goes in `~/.chutes/config`

## Backend selection

The script auto-detects a backend:

- macOS + `security` available -> `keychain`
- Linux + `secret-tool` available -> `linux_secretservice`
- otherwise -> `encrypted_file`

### Backends

#### macOS Keychain
Uses the `security` CLI to store a JSON blob in Keychain Access.

#### Linux Secret Service
Uses `secret-tool` with freedesktop Secret Service (for example GNOME Keyring / KDE Wallet).

#### Encrypted file fallback
Uses AES-256-GCM with a key derived from local machine identity.

Fallback file path:
- `~/.chutes/.keychain`

This is weaker than platform keychains but still better than plaintext.

## File-system security expectations

The script should maintain:
- `~/.chutes/` -> `0700`
- `~/.chutes/config` -> `0600`
- `~/.chutes/.keychain` -> `0600` when fallback backend is used
- `~/.chutes/.gitignore` containing `*`

The `.gitignore` file is an additional safeguard against accidental commits.

## CLI commands

### Save/update a full profile

```bash
python manage_credentials.py set-profile \
  --profile default \
  --username alice \
  --user-id 550e8400-e29b-41d4-a716-446655440000 \
  --api-key cpk_... \
  --fingerprint ABCD1234...
```

### Update a single field

```bash
python manage_credentials.py set --profile default --field api_key --value cpk_...
```

### Get one field

```bash
python manage_credentials.py get --profile default --field api_key
```

### Get all stored values for a profile

```bash
python manage_credentials.py get --profile default
```

### List profiles

```bash
python manage_credentials.py list-profiles
```

### Delete a profile

```bash
python manage_credentials.py delete --profile default
```

### Check status

```bash
python manage_credentials.py check
```

Current `check` output includes security-oriented fields such as:
- detected backend
- config existence and permissions
- directory existence and permissions
- `.gitignore` presence and correctness
- encrypted fallback file presence and permissions
- active environment-variable overrides

## Environment variable overrides

Environment variables have highest priority for secret retrieval.

Supported overrides:
- `CHUTES_API_KEY`
- `CHUTES_FINGERPRINT`
- `CHUTES_CLIENT_ID`
- `CHUTES_CLIENT_SECRET`
- `CHUTES_PROFILE`

Implications:
- CI/CD can inject secrets without writing them to disk
- agents should expect `get --field api_key` to return env-provided values if present

## Agent-safe invocation guidance

### Do

- call the script directly from tooling or terminal execution
- pass secrets via stdin or secure env vars when possible
- store credentials immediately after account creation or API key issuance
- use `check` at session start to determine whether credentials already exist

### Do not

- paste raw secret values into chat when avoidable
- commit `~/.chutes/` contents
- pass secrets in ways that expose them to `ps`
- treat fallback encrypted file as equivalent to system keychain security

## Recommended session flow for agents

1. Run:

```bash
python manage_credentials.py check
```

2. If a profile exists and credentials are available, retrieve only what is needed:

```bash
python manage_credentials.py get --field api_key
```

3. Use the credential in API headers, not in conversation text.

4. If no credentials exist, walk through account/API key setup, then immediately save them with `set-profile`.

## Testing notes

Tests for the credential manager live under:
- `tests/test_manage_credentials.py`

Current coverage includes:
- secure directory creation
- `.gitignore` creation
- environment override precedence
- `check` output for `.gitignore`
- `set-profile` metadata/secret persistence behavior
- `delete` removing profile state
- encrypted fallback file status reporting

Further recommended coverage:
- corrupt encrypted file handling
- Linux/macOS backend command mocking
- profile merge/update behavior across repeated writes
- missing-field and error exit-code cases
