# Deployment

OSMA is a monorepo. Only the **Next.js web app** (`apps/web`) is a good fit for
Vercel. The rest of the stack is long-running and must be hosted elsewhere:

| Component                | Where it runs                              |
| ------------------------ | ------------------------------------------ |
| `apps/web` (Next.js)     | **Vercel**                                 |
| `services/agent-api`     | Container/VM host (Railway, Fly, Render…)  |
| Arq worker (scanning)    | Same host as the API                       |
| Postgres                 | Supabase (managed)                         |
| Qdrant                   | Qdrant Cloud or self-hosted                |
| Redis                    | Managed Redis (Upstash, etc.)              |

Deploy the backend first, then point the Vercel app at its public URL.

## Deploy the web app to Vercel

### Option A — Vercel Dashboard (no CLI)

1. **Add New → Project** and import this GitHub repository.
2. Set **Root Directory** to `apps/web` (this is required for the monorepo).
3. Framework preset: **Next.js** (auto-detected).
4. Add the environment variables below.
5. Deploy.

### Option B — Vercel CLI

```bash
npm i -g vercel
cd apps/web
vercel link          # select/create the project
vercel env add ...   # or set them in the dashboard
vercel --prod
```

If you deploy from CI or a token-based flow, export `VERCEL_TOKEN` (and
optionally `VERCEL_ORG_ID` / `VERCEL_PROJECT_ID`) and run
`vercel pull && vercel build && vercel deploy --prebuilt --prod`.

## Environment variables (Vercel → Project → Settings → Environment Variables)

| Variable                        | Purpose                                             |
| ------------------------------- | --------------------------------------------------- |
| `NEXT_PUBLIC_SUPABASE_URL`      | Supabase project URL                                |
| `NEXT_PUBLIC_SUPABASE_ANON_KEY` | Supabase anon key                                   |
| `NEXT_PUBLIC_AGENT_API_URL`     | Public URL of the deployed `agent-api` backend      |
| `AGENT_API_URL`                 | Backend URL used server-side (auth callback, proxy) |
| `NEXT_PUBLIC_SITE_URL`          | Your Vercel deployment URL                          |

`NEXT_PUBLIC_*` variables are exposed to the browser; the others are
server-only. All variables in `.env.example` remain the source of truth for the
backend service.

## After deploying

1. In **Supabase → Authentication → URL Configuration**, add your Vercel
   callback URL (e.g. `https://<your-app>.vercel.app/auth/callback`) to the
   allowed redirect URLs.
2. Update the GitHub OAuth app's homepage URL to the Vercel URL if desired.
3. Make sure the backend's `CORS_ORIGINS` includes your Vercel domain.
