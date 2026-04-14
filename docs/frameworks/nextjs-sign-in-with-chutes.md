# Sign in with Chutes — Next.js App Router (operator guide)

> **Status: BETA** — this doc duplicates the skill walkthrough at `plugins/chutes-ai/skills/chutes-sign-in/references/frameworks/nextjs.md` for operators who read `docs/` first. The skill file is the source of truth during the BETA window.

## Prerequisites

- Next.js 14+ App Router (`src/app/` or `app/` layout).
- A Chutes account with a `cpk_` API key stored in the credential manager.
- Python 3.10+ and `git` for the helper scripts.
- The target project's `.env.local` is already in `.gitignore`.

## Step 1 — Register the OAuth app

```bash
python plugins/chutes-ai/skills/chutes-sign-in/scripts/register_oauth_app.py \
  --name "My App" \
  --homepage-url https://myapp.example.com \
  --redirect-uri http://localhost:3000/api/auth/chutes/callback \
  --redirect-uri https://myapp.example.com/api/auth/chutes/callback \
  --scope openid --scope profile --scope chutes:invoke \
  --profile oauth.my-app
```

Behind the scenes:

1. Reads `cpk_` from `manage_credentials.py get --field api_key`.
2. POSTs `/idp/apps` with the supplied metadata.
3. Captures `client_id` (`cid_...`) and `client_secret` (`csc_...`) from the response.
4. Writes both into the keychain under `--profile oauth.my-app`. **The secret never touches transcript.**
5. Prints the `client_id` (safe — OAuth public info), a redacted preview of the secret, and the profile name.

## Step 2 — Vendor the upstream package

```bash
python plugins/chutes-ai/skills/chutes-sign-in/scripts/install_siwc.py \
  --target /path/to/next-app --profile oauth.my-app
```

The installer:

1. Detects Next.js App Router in the target project. Refuses to proceed for Pages Router, Express, or FastAPI (upstream not yet shipped).
2. Clones `https://github.com/chutesai/Sign-in-with-Chutes` at a pinned commit into `~/.chutes/cache/siwc/`.
3. Copies `packages/nextjs/{lib,hooks,app/api/auth/chutes,components}` into the target, respecting `src/` vs flat layout. Prompts before overwrite; backs up existing files with a timestamped `.bak-*` suffix.
4. Reads `client_id` / `client_secret` from the keychain profile (via `manage_credentials.py get`) and appends them plus `NEXT_PUBLIC_APP_URL=http://localhost:3000` to `.env.local`.
5. Prints a diff showing how to wire `<SignInButton />` into the top-level layout — the installer does **not** auto-edit user source files.

## Step 3 — Wire the button

Apply the suggested diff manually to `src/app/layout.tsx` (or `app/layout.tsx`):

```tsx
import { SignInButton } from "@/components/SignInButton";

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>
        <header className="flex justify-end p-4">
          <SignInButton />
        </header>
        {children}
      </body>
    </html>
  );
}
```

## Step 4 — Run and test

```bash
cd /path/to/next-app
npm run dev
```

Click the sign-in button. The browser redirects to Chutes, the user authorizes, and they land on the callback. `useChutesSession` on the client now returns the user.

## Step 5 — Verify programmatically

```bash
python plugins/chutes-ai/skills/chutes-sign-in/scripts/verify_siwc.py \
  --target /path/to/next-app --profile oauth.my-app
```

Checks:

1. All vendored files exist at expected paths.
2. `.env.local` has all three required entries.
3. The `.env.local` client_id matches the keychain profile's client_id.
4. The dev server's `/api/auth/chutes/session` route responds with 200 or 401 (not 500).
5. If an access token is supplied via `--access-token`, introspects it against `POST /idp/token/introspect`.

## Step 6 — Deploy to Vercel

```bash
vercel env add CHUTES_OAUTH_CLIENT_ID
vercel env add CHUTES_OAUTH_CLIENT_SECRET
vercel env add NEXT_PUBLIC_APP_URL   # e.g. https://myapp.example.com
vercel --prod
```

Make sure your production `NEXT_PUBLIC_APP_URL` is in the app's `redirect_uris` list. If not, `PATCH /idp/apps/{app_id}` to add it.

## Step 7 — Rotate the client secret when needed

```bash
python plugins/chutes-ai/skills/chutes-sign-in/scripts/rotate_secret.py \
  --profile oauth.my-app
```

`POST /idp/apps/{app_id}/regenerate-secret`, keychain write-through, redeploy reminder. The script does **not** auto-redeploy — too much blast radius. Update Vercel / Docker / bare-metal env vars and redeploy manually.

## Using the session in a server route

```ts
import { getServerAccessToken } from "@/lib/serverAuth";

export async function POST(req: Request) {
  const token = await getServerAccessToken();
  if (!token) return new Response("Unauthorized", { status: 401 });

  const body = await req.json();
  const upstream = await fetch("https://llm.chutes.ai/v1/chat/completions", {
    method: "POST",
    headers: {
      Authorization: `Bearer ${token}`,
      "Content-Type": "application/json",
    },
    body: JSON.stringify(body),
  });
  return new Response(upstream.body, { status: upstream.status });
}
```

Inference quota and billing hit the **user's** Chutes account, not yours. That's the point of delegated OAuth.

## Related

- `docs/sign-in-with-chutes.md`
- `docs/oauth-app-management.md`
- `docs/oauth-scope-cookbook.md`
- `plugins/chutes-ai/skills/chutes-sign-in/SKILL.md`
- `plugins/chutes-ai/skills/chutes-sign-in/references/frameworks/nextjs.md` (source)
- Upstream: https://github.com/chutesai/Sign-in-with-Chutes
