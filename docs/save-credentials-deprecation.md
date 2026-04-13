# Deprecation Notes for `save_credentials.py`

`plugins/chutes-ai/skills/chutes-ai/scripts/save_credentials.py` is a legacy compatibility script.

## Status

- supported only for backward compatibility
- not recommended for new workflows
- superseded by `manage_credentials.py`

Primary replacement:
- `plugins/chutes-ai/skills/chutes-ai/scripts/manage_credentials.py`

## Why it is deprecated

`save_credentials.py` writes sensitive Chutes credentials to a plaintext file.

That is worse than the secure credential manager because plaintext backups can leak through:
- accidental git commits
- shell/file sync mistakes
- local malware or other-user file access
- insecure cloud backup workflows
- simple copy/paste mishandling

`manage_credentials.py` is the preferred path because it uses:
- macOS Keychain when available
- Linux Secret Service when available
- encrypted-file fallback only when necessary

## When legacy plaintext backup may still be acceptable

Only use `save_credentials.py` intentionally for narrow cases such as:
- creating an offline emergency backup that will be stored manually and securely
- exporting credentials into a temporary, isolated environment where keychain-style storage is unavailable
- migration from an older workflow where plaintext backup is temporarily unavoidable

Even then:
- do not store the file in the repo
- do not commit it
- do not leave it in a synced documents folder by accident
- prefer deleting it after the credential is moved into secure storage

## Recommended migration path

Instead of:

```bash
python save_credentials.py --username alice --fingerprint ... --user-id ... --api-key cpk_...
```

Use:

```bash
python manage_credentials.py set-profile \
  --profile default \
  --username alice \
  --user-id 550e8400-e29b-41d4-a716-446655440000 \
  --fingerprint ... \
  --api-key cpk_...
```

Then verify with:

```bash
python manage_credentials.py check
```

## Guidance for agent authors

If an agent or skill references `save_credentials.py`, that should be treated as technical debt.

Preferred behavior:
- use `manage_credentials.py` by default
- mention plaintext backup only as a legacy or emergency option
- avoid presenting plaintext file storage as the standard path

## Suggested future removal path

Safe removal path:
1. keep deprecation warning in place
2. update docs/skills/examples to stop recommending it
3. once downstream consumers are migrated, remove the script in a later cleanup release
