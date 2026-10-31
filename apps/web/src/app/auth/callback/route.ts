import { NextResponse } from "next/server";
import { createClient } from "@/lib/supabase/server";
import { sameOriginRedirect } from "@/lib/safe-redirect";

const GITHUB_API = "https://api.github.com";

// Exchanges the OAuth code for a session, then captures the GitHub provider
// token and persists it (encrypted) on the backend for server-side API calls.
export async function GET(request: Request) {
  const url = new URL(request.url);
  const searchParams = url.searchParams;
  const code = searchParams.get("code");
  const redirectPath = searchParams.get("redirect");

  // Behind Docker, request.url resolves to the container's internal host
  // (0.0.0.0:3000). Use the configured public site URL for browser redirects,
  // falling back to the request origin for local `next dev`.
  const origin = process.env.NEXT_PUBLIC_SITE_URL ?? url.origin;

  if (!code) {
    return NextResponse.redirect(`${origin}/login?error=missing_code`);
  }

  const supabase = await createClient();
  const { data, error } = await supabase.auth.exchangeCodeForSession(code);

  if (error) {
    return NextResponse.redirect(
      `${origin}/login?error=${encodeURIComponent(error.message)}`,
    );
  }

  // Persist the GitHub provider token on the backend.
  const providerToken = data.session?.provider_token;
  const accessToken = data.session?.access_token;
  if (providerToken && accessToken) {
    const saved = await saveGitHubToken(providerToken, accessToken);
    if (!saved) {
      const failed = new URL(sameOriginRedirect(origin, "/dashboard"));
      failed.searchParams.set("error", "github_token");
      return NextResponse.redirect(failed);
    }
  }

  return NextResponse.redirect(sameOriginRedirect(origin, redirectPath ?? ""));
}

async function githubGrantedScope(token: string): Promise<string | null> {
  const res = await fetch(`${GITHUB_API}/user`, {
    headers: {
      Accept: "application/vnd.github+json",
      Authorization: `Bearer ${token}`,
      "User-Agent": "osma",
      "X-GitHub-Api-Version": "2022-11-28",
    },
  });
  if (!res.ok) return null;
  const scope = res.headers.get("x-oauth-scopes");
  return scope && scope.trim() ? scope.trim() : null;
}

async function saveGitHubToken(
  providerToken: string,
  accessToken: string,
): Promise<boolean> {
  let scope: string | null = null;
  try {
    scope = await githubGrantedScope(providerToken);
  } catch {
    scope = null;
  }
  try {
    const res = await fetch(
      `${process.env.AGENT_API_URL ?? "http://localhost:8000"}/api/v1/me/github-token`,
      {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${accessToken}`,
        },
        body: JSON.stringify({
          access_token: providerToken,
          scope,
        }),
      },
    );
    return res.ok;
  } catch {
    return false;
  }
}
