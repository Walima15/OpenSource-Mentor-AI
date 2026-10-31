// Post-login redirects must stay on this site. A value such as "@evil.example"
// or "//evil.example" would otherwise change the host when joined to the origin.

const FALLBACK = "/dashboard";

export function safeRedirectPath(value: string | null | undefined): string {
  if (typeof value !== "string") return FALLBACK;
  const path = value.trim();
  if (!path.startsWith("/") || path.startsWith("//")) return FALLBACK;
  if (path.includes("@") || path.includes("\\") || path.includes("//")) {
    return FALLBACK;
  }
  return path;
}

export function sameOriginRedirect(origin: string, path: string): string {
  const base = new URL(origin);
  const target = new URL(safeRedirectPath(path), base);
  if (target.origin !== base.origin) {
    return new URL(FALLBACK, base).toString();
  }
  return target.toString();
}
