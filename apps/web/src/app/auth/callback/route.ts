import { NextResponse } from "next/server";
import { createClient } from "@/lib/supabase/server";

// Exchanges the OAuth code for a session, then captures the GitHub provider
// token and persists it (encrypted) on the backend for server-side API calls.
export async function GET(request: Request) {
  const { searchParams, origin } = new URL(request.url);
  const code = searchParams.get("code");
  const redirect = searchParams.get("redirect") ?? "/dashboard";

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

  // Persist the GitHub provider token on the backend (best-effort).
  const providerToken = data.session?.provider_token;
  const accessToken = data.session?.access_token;
  if (providerToken && accessToken) {
    try {
      await fetch(
        `${process.env.AGENT_API_URL ?? "http://localhost:8000"}/api/v1/me/github-token`,
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            Authorization: `Bearer ${accessToken}`,
          },
          body: JSON.stringify({ access_token: providerToken, scope: "repo" }),
        },
      );
    } catch {
      // Non-fatal: the user can still browse; some GitHub calls may be rate limited.
    }
  }

  return NextResponse.redirect(`${origin}${redirect}`);
}
