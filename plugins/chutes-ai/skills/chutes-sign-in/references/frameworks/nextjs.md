# Sign in with Chutes — Next.js App Router

> **Status: BETA** — walkthrough for Next.js App Router (14+). Pages Router / Express / FastAPI are separate stubs.

## Supported layouts

- `src/app/` — preferred
- `app/` — flat layout also supported

The `install_siwc.py` script detects which you use and places files accordingly.

## Files vendored

From `chutesai/Sign-in-with-Chutes` `packages/nextjs/` at a pinned commit:

| Source path | Destination |
|---|---|
| `lib/chutesAuth.ts` | `{src,}/lib/chutesAuth.ts` |
| `lib/serverAuth.ts` | `{src,}/lib/serverAuth.ts` |
| `hooks/useChutesSession.ts` | `{src,}/hooks/useChutesSession.ts` |
| `app/api/auth/chutes/login/route.ts` | `{src,}/app/api/auth/chutes/login/route.ts` |
| `app/api/auth/chutes/callback/route.ts` | `{src,}/app/api/auth/chutes/callback/route.ts` |
| `app/api/auth/chutes/logout/route.ts` | `{src,}/app/api/auth/chutes/logout/route.ts` |
| `app/api/auth/chutes/session/route.ts` | `{src,}/app/api/auth/chutes/session/route.ts` |
| `components/SignInButton.tsx` | `{src,}/components/SignInButton.tsx` |

If any destination file already exists, `install_siwc.py` prompts before overwriting. The original is backed up to `<name>.bak-<timestamp>`.

## Environment variables

Append to `.env.local` (values flow from the keychain, never from transcript):

```
CHUTES_OAUTH_CLIENT_ID=<cid_... from keychain>
CHUTES_OAUTH_CLIENT_SECRET=<csc_... from keychain>
NEXT_PUBLIC_APP_URL=http://localhost:3000
```

For production, set `NEXT_PUBLIC_APP_URL` to the canonical app URL and make sure that URL is in the `redirect_uris` list when you registered the app. If not, run:

```
python manage_credentials.py get --profile oauth.my-app --field client_id
```

and update the app via `PATCH /idp/apps/{app_id}` with the new redirect URI list.

## Wiring the button

The installer prints a diff like this:

```tsx
// src/app/layout.tsx
import { SignInButton } from "@/components/SignInButton";

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>
        <header className="flex justify-end p-4">
          <SignInButton />      {/* ← added */}
        </header>
        {children}
      </body>
    </html>
  );
}
```

Apply manually. The skill never auto-edits layout files.

## Using the session client-side

```tsx
"use client";
import { useChutesSession } from "@/hooks/useChutesSession";

export function Greeting() {
  const { user, loading, signIn, signOut } = useChutesSession();
  if (loading) return <p>Loading…</p>;
  if (!user) return <button onClick={signIn}>Sign in</button>;
  return (
    <div>
      Hi {user.name ?? user.preferred_username}
      <button onClick={signOut}>Sign out</button>
    </div>
  );
}
```

## Making inference calls server-side

Inside any API route or server component:

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

The inference quota and billing hit the **user's** Chutes account, not yours. That's the whole point of delegated OAuth.

## Deploying to Vercel

1. `vercel env add CHUTES_OAUTH_CLIENT_ID` — paste the value (or pipe from `manage_credentials.py get`). Do this for `CHUTES_OAUTH_CLIENT_SECRET` and `NEXT_PUBLIC_APP_URL` as well.
2. Make sure your production `NEXT_PUBLIC_APP_URL` is in the `redirect_uris` list on the Chutes app.
3. Deploy. `vercel --prod` picks up the env vars automatically.
4. If you rotate the client secret via `rotate_secret.py`, you also need to update the Vercel env var and redeploy — Vercel env is a point-in-time snapshot, not a live read.

## Gotchas

- **`http://` localhost redirects must be explicitly allowed.** Chutes will reject redirect URIs that aren't in the app's list. If dev breaks, check `PATCH /idp/apps/{id}` to add the localhost variant.
- **Sessions are cookie-scoped.** If your app is split across subdomains (`app.example.com` vs `www.example.com`), cookie domain settings on the session may cause mysterious 401s.
- **Refresh tokens expire.** If you're seeing forced re-logins every few days, that's the refresh token TTL and it's correct behavior.
