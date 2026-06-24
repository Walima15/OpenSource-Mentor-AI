import { NextResponse, type NextRequest } from "next/server";
import { createClient } from "@/lib/supabase/server";

const GITHUB_API = "https://api.github.com";

// Server-side proxy to the GitHub REST API. Uses the user's session provider
// token (when available) so the token never reaches the browser.
export async function GET(
  request: NextRequest,
  { params }: { params: Promise<{ path: string[] }> },
) {
  const supabase = await createClient();
  const {
    data: { session },
  } = await supabase.auth.getSession();

  if (!session) {
    return NextResponse.json({ detail: "Unauthorized" }, { status: 401 });
  }

  const { path } = await params;
  const search = request.nextUrl.search;
  const target = `${GITHUB_API}/${path.join("/")}${search}`;

  const headers: Record<string, string> = {
    Accept: "application/vnd.github+json",
    "X-GitHub-Api-Version": "2022-11-28",
  };
  if (session.provider_token) {
    headers.Authorization = `Bearer ${session.provider_token}`;
  }

  const res = await fetch(target, { headers });
  const body = await res.text();
  return new NextResponse(body, {
    status: res.status,
    headers: { "Content-Type": "application/json" },
  });
}
