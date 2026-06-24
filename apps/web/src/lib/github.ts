// Small GitHub-related helpers for the browser.

export function parseRepoInput(input: string): { owner: string; name: string } | null {
  const trimmed = input.trim();
  // Accept "owner/name" or a full GitHub URL.
  const urlMatch = trimmed.match(/github\.com\/([^/]+)\/([^/]+?)(?:\.git|\/|$)/i);
  if (urlMatch) {
    return { owner: urlMatch[1], name: urlMatch[2] };
  }
  const slug = trimmed.match(/^([^/\s]+)\/([^/\s]+)$/);
  if (slug) {
    return { owner: slug[1], name: slug[2] };
  }
  return null;
}

export function repoUrl(owner: string, name: string): string {
  return `https://github.com/${owner}/${name}`;
}

export function issueUrl(owner: string, name: string, number: number): string {
  return `https://github.com/${owner}/${name}/issues/${number}`;
}
