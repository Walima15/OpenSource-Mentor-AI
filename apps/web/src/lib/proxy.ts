/**
 * The browser talks only to the Next.js app. This proxy forwards a narrow set
 * of paths to the local agent API and refuses to become an open proxy.
 */

const ALLOWED_HOSTS = new Set(["127.0.0.1", "localhost", "agent-api"]);

export function agentBaseUrl(raw = process.env.AGENT_API_URL || "http://127.0.0.1:8000"): string {
  let url: URL;
  try {
    url = new URL(raw);
  } catch {
    throw new Error("AGENT_API_URL is not a URL");
  }
  if (url.username || url.password) {
    throw new Error("AGENT_API_URL must not contain credentials");
  }
  if (url.protocol !== "http:" && url.protocol !== "https:") {
    throw new Error("AGENT_API_URL must be http(s)");
  }
  if (!ALLOWED_HOSTS.has(url.hostname)) {
    throw new Error("AGENT_API_URL host is not allowed");
  }
  return url.origin;
}

export function safeAgentPath(parts: string[]): string {
  if (!parts.length || parts.some((part) => !part || part === "." || part === ".." || part.includes("\\") || part.includes("%"))) {
    throw new Error("Invalid path");
  }
  const path = parts.join("/");
  if (!/^(health|api\/v1\/[a-z0-9/-]+)$/.test(path)) {
    throw new Error("Invalid path");
  }
  return path;
}
