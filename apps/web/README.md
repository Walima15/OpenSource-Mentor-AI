# OSMA Web (Next.js 15)

The frontend dashboard for OpenSource Mentor AI.

## Stack

- Next.js 15 (App Router) + React 19
- TypeScript
- Tailwind CSS (dark theme)
- Supabase Auth (GitHub OAuth) via `@supabase/ssr`

## Structure

```
src/
  app/
    page.tsx                 # Landing page
    login/                   # GitHub OAuth sign-in
    auth/callback/route.ts   # OAuth code exchange + token sync
    dashboard/
      layout.tsx             # Auth-guarded shell + sidebar
      page.tsx               # Overview
      repos/                 # Repo search, detail, mentor sessions
      sessions/              # Session history
      profile/               # Profile + skills
  components/                # Sidebar, ChatPanel, DiffViewer, Markdown, ...
  lib/
    supabase/                # Browser/server/middleware clients
    api-client.ts            # Typed FastAPI client + SSE chat
    github.ts                # GitHub helpers
  types/                     # Shared TS types (mirror backend schemas)
```

## Develop

```bash
npm install
npm run dev
```

Requires the environment variables documented in the root `.env.example`
(notably `NEXT_PUBLIC_SUPABASE_URL`, `NEXT_PUBLIC_SUPABASE_ANON_KEY`,
`NEXT_PUBLIC_AGENT_API_URL`).
