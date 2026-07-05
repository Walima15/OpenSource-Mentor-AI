# Deploying OSMA to production

OSMA is multi-service, so a full deploy uses three platforms (Postgres is
already on Supabase):

| Component            | Platform      | Notes                                    |
| -------------------- | ------------- | ---------------------------------------- |
| Web (Next.js)        | Vercel        | Root directory: `apps/web`               |
| API (FastAPI)        | Render        | Docker, `services/agent-api`             |
| Vectors (Qdrant)     | Qdrant Cloud  | Free cluster                             |
| Postgres + Auth      | Supabase      | Already provisioned                      |

Ingestion runs in-process (FastAPI BackgroundTasks); no Redis/worker required
for this tier.

## Order of operations

1. **Qdrant Cloud** — create a free cluster; note the URL + API key.
2. **Render (API)** — deploy `render.yaml`; set secrets:
   - `DATABASE_URL` (Supabase session pooler), `SUPABASE_URL`, `SUPABASE_ANON_KEY`,
     `SUPABASE_JWT_SECRET`
   - `ANTHROPIC_API_KEY`, `GITHUB_CLIENT_ID`, `GITHUB_CLIENT_SECRET`
   - `QDRANT_URL`, `QDRANT_API_KEY`
   - `TOKEN_ENCRYPTION_KEY`
   - `CORS_ORIGINS` = your Vercel URL (set after step 3, then redeploy)
   - Note the API URL, e.g. `https://osma-agent-api.onrender.com`.
3. **Vercel (Web)** — project root `apps/web`; env vars:
   - `NEXT_PUBLIC_SUPABASE_URL`, `NEXT_PUBLIC_SUPABASE_ANON_KEY`
   - `NEXT_PUBLIC_AGENT_API_URL` = the Render API URL
   - `NEXT_PUBLIC_SITE_URL` = the Vercel URL
   - `AGENT_API_URL` = the Render API URL (server-side callback -> backend)
4. **Supabase** — Authentication -> URL Configuration:
   - Site URL = your Vercel URL
   - Redirect URLs += `https://<your-vercel-domain>/auth/callback`
5. **Render** — set `CORS_ORIGINS` to the Vercel URL and redeploy.

The GitHub OAuth app callback stays `https://<ref>.supabase.co/auth/v1/callback`.
