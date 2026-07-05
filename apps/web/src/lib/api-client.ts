import { createClient } from "@/lib/supabase/client";
import type {
  CodeSuggestion,
  ContributionPlan,
  Issue,
  MentorMessage,
  MentorSession,
  Profile,
  PullRequestDraft,
  PullRequestResult,
  Recommendation,
  RepoSearchResult,
  ScanResult,
  Skill,
  TrackedRepo,
} from "@/types";

const API_URL =
  process.env.NEXT_PUBLIC_AGENT_API_URL ?? "http://localhost:8000";

async function authHeader(): Promise<Record<string, string>> {
  const supabase = createClient();
  const {
    data: { session },
  } = await supabase.auth.getSession();
  return session?.access_token
    ? { Authorization: `Bearer ${session.access_token}` }
    : {};
}

async function request<T>(path: string, init: RequestInit = {}): Promise<T> {
  const headers = {
    "Content-Type": "application/json",
    ...(await authHeader()),
    ...(init.headers ?? {}),
  };
  const res = await fetch(`${API_URL}/api/v1${path}`, { ...init, headers });
  if (!res.ok) {
    let detail = res.statusText;
    try {
      const body = await res.json();
      detail = body.detail ?? detail;
    } catch {
      // ignore parse errors
    }
    throw new ApiError(res.status, detail);
  }
  if (res.status === 204) return undefined as T;
  return res.json() as Promise<T>;
}

export class ApiError extends Error {
  constructor(
    public status: number,
    message: string,
  ) {
    super(message);
    this.name = "ApiError";
  }
}

export const api = {
  // Profile
  getProfile: () => request<Profile>("/me"),
  updateProfile: (data: Partial<Pick<Profile, "bio" | "avatar_url">>) =>
    request<Profile>("/me", { method: "PATCH", body: JSON.stringify(data) }),
  saveGithubToken: (access_token: string, scope?: string) =>
    request<void>("/me/github-token", {
      method: "POST",
      body: JSON.stringify({ access_token, scope }),
    }),
  listSkills: () => request<Skill[]>("/me/skills"),
  upsertSkill: (data: { language: string; level: string; score: number }) =>
    request<Skill>("/me/skills", {
      method: "POST",
      body: JSON.stringify(data),
    }),

  // Repos
  searchRepos: (q: string) =>
    request<RepoSearchResult[]>(`/repos/search?q=${encodeURIComponent(q)}`),
  listRepos: () => request<TrackedRepo[]>("/repos"),
  trackRepo: (owner: string, name: string) =>
    request<TrackedRepo>("/repos/track", {
      method: "POST",
      body: JSON.stringify({ owner, name }),
    }),
  getRepo: (id: string) => request<TrackedRepo>(`/repos/${id}`),
  indexRepo: (id: string) =>
    request<{ index_status: string }>(`/repos/${id}/index`, { method: "POST" }),
  indexStatus: (id: string) =>
    request<{ index_status: string; indexed_chunks: number }>(
      `/repos/${id}/index/status`,
    ),
  repoStructure: (id: string) =>
    request<{
      default_branch: string;
      tree: { path: string; type: string; size: number | null }[];
      truncated: boolean;
    }>(`/repos/${id}/structure`),
  repoDocs: (id: string) =>
    request<{ readme: string | null; contributing: string | null }>(
      `/repos/${id}/docs`,
    ),

  // Issues
  listIssues: (repoId: string, labels?: string) =>
    request<Issue[]>(
      `/repos/${repoId}/issues${labels ? `?labels=${encodeURIComponent(labels)}` : ""}`,
    ),
  getIssue: (repoId: string, number: number) =>
    request<Issue>(`/repos/${repoId}/issues/${number}`),

  // Recommendations (issue-to-skill matching)
  getRecommendations: (limit = 20) =>
    request<Recommendation[]>(`/recommendations?limit=${limit}`),
  scanRecommendations: () =>
    request<ScanResult>("/recommendations/scan", { method: "POST" }),

  // Mentor
  createSession: (data: {
    repo_id: string;
    issue_number?: number;
    title?: string;
  }) =>
    request<MentorSession>("/mentor/sessions", {
      method: "POST",
      body: JSON.stringify(data),
    }),
  listSessions: () => request<MentorSession[]>("/mentor/sessions"),
  getSessionMessages: (id: string) =>
    request<MentorMessage[]>(`/mentor/sessions/${id}`),
  explainRepo: (id: string) =>
    request<{ content: string }>(`/mentor/sessions/${id}/explain-repo`, {
      method: "POST",
    }),
  explainIssue: (id: string) =>
    request<{ content: string }>(`/mentor/sessions/${id}/explain-issue`, {
      method: "POST",
    }),
  createPlan: (id: string) =>
    request<ContributionPlan>(`/mentor/sessions/${id}/plan`, {
      method: "POST",
    }),

  // Contribute
  recommendFiles: (planId: string) =>
    request<ContributionPlan>(`/contribute/${planId}/recommend-files`, {
      method: "POST",
    }),
  suggestCode: (planId: string, file_path: string, instruction?: string) =>
    request<CodeSuggestion>(`/contribute/${planId}/suggest-code`, {
      method: "POST",
      body: JSON.stringify({ file_path, instruction }),
    }),

  // Pull request
  commitMessage: (planId: string) =>
    request<PullRequestDraft>(`/pr/${planId}/commit-message`, {
      method: "POST",
    }),
  prDescription: (planId: string) =>
    request<PullRequestDraft>(`/pr/${planId}/description`, { method: "POST" }),
  summarize: (planId: string) =>
    request<{ content: string }>(`/pr/${planId}/summarize`, { method: "POST" }),
  createPullRequest: (planId: string, draft = false) =>
    request<PullRequestResult>(`/pr/${planId}/create`, {
      method: "POST",
      body: JSON.stringify({ draft }),
    }),
};

export function chatStreamUrl(sessionId: string): string {
  return `${API_URL}/api/v1/mentor/sessions/${sessionId}/chat`;
}

export async function streamChat(
  sessionId: string,
  message: string,
  onDelta: (text: string) => void,
): Promise<void> {
  const res = await fetch(chatStreamUrl(sessionId), {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      ...(await authHeader()),
    },
    body: JSON.stringify({ message }),
  });
  if (!res.ok || !res.body) {
    throw new ApiError(res.status, "Chat request failed");
  }
  const reader = res.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";
  while (true) {
    const { done, value } = await reader.read();
    if (done) break;
    buffer += decoder.decode(value, { stream: true });
    const events = buffer.split("\n\n");
    buffer = events.pop() ?? "";
    for (const evt of events) {
      const lines = evt.split("\n");
      let event = "message";
      let data = "";
      for (const line of lines) {
        if (line.startsWith("event:")) event = line.slice(6).trim();
        if (line.startsWith("data:")) data += line.slice(5).replace(/^ /, "");
      }
      if (event === "delta" && data) onDelta(data);
    }
  }
}
