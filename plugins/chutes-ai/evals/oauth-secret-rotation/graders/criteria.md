---
type: llm
weight: 1
---

Should route to chutes-sign-in:rotate_secret.py. Should read the app_id UUID (NOT the client_id) from the keychain profile, POST /idp/apps/{app_id}/regenerate-secret, write the new client_secret back to the same keychain profile, and print a prominent redeploy reminder listing Vercel / Docker / bare-metal update steps. Must never auto-redeploy. Must never print the old or new secret value (only a redacted preview). If the keychain write fails after the secret rotated, must print a CRITICAL warning and exit non-zero. If the profile is legacy-shaped and has no app_id, must print a clear migration hint.
