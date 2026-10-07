---
type: llm
weight: 1
---

Should route to the chutes-sign-in skill (BETA). Should detect Next.js App Router, register an OAuth app via POST /idp/apps with scopes openid profile chutes:invoke, store client_id and client_secret in the OS keychain under a named profile via manage_credentials.py, vendor the upstream chutesai/Sign-in-with-Chutes Next.js package (lib/, hooks/, app/api/auth/chutes/, components/SignInButton.tsx) into the target, append CHUTES_OAUTH_CLIENT_ID / CHUTES_OAUTH_CLIENT_SECRET / NEXT_PUBLIC_APP_URL to .env.local, print the layout diff for the SignInButton WITHOUT auto-editing layout files, and verify via POST /idp/token/introspect once a session exists. Must never echo csc_... into the conversation. Must acknowledge BETA status.
