import { NextRequest, NextResponse } from "next/server";

import { agentBaseUrl, safeAgentPath } from "@/lib/proxy";

const METHODS = new Set(["GET", "POST", "DELETE"]);
const MAX_BODY = 100_000;

async function proxy(request: NextRequest, context: { params: Promise<{ path: string[] }> }) {
  if (!METHODS.has(request.method)) {
    return NextResponse.json({ detail: "Method not allowed" }, { status: 405 });
  }
  const { path } = await context.params;
  let target: string;
  try {
    target = `${agentBaseUrl()}/${safeAgentPath(path)}`;
  } catch {
    return NextResponse.json({ detail: "Invalid path" }, { status: 400 });
  }

  const headers = new Headers();
  const contentType = request.headers.get("content-type");
  if (contentType?.startsWith("application/json")) {
    headers.set("content-type", contentType.split(";")[0]);
  }

  const init: RequestInit = { method: request.method, headers, cache: "no-store" };
  if (request.method !== "GET") {
    const body = await request.arrayBuffer();
    if (body.byteLength > MAX_BODY) {
      return NextResponse.json({ detail: "Request too large" }, { status: 413 });
    }
    init.body = body;
  }

  const search = new URL(request.url).search;
  try {
    const response = await fetch(`${target}${search}`, init);
    const out = new Headers();
    const responseType = response.headers.get("content-type");
    if (responseType) out.set("content-type", responseType);
    out.set("x-content-type-options", "nosniff");
    out.set("cache-control", "no-store");
    const retry = response.headers.get("retry-after");
    if (retry && /^\d+$/.test(retry)) out.set("retry-after", retry);
    return new NextResponse(response.body, { status: response.status, headers: out });
  } catch {
    return NextResponse.json(
      { detail: "The mentor API is not running. Start it with make dev." },
      { status: 502 },
    );
  }
}

export const GET = proxy;
export const POST = proxy;
export const DELETE = proxy;
