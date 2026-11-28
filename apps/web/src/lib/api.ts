export class ApiError extends Error {
  status: number;

  constructor(status: number, message: string) {
    super(message);
    this.status = status;
  }
}

export async function api<T>(path: string, init?: RequestInit): Promise<T> {
  const headers = new Headers(init?.headers);
  if (init?.body && !headers.has("Content-Type")) {
    headers.set("Content-Type", "application/json");
  }
  const response = await fetch(`/api/agent/${path}`, {
    ...init,
    headers,
    cache: "no-store",
  });
  if (response.status === 204) {
    return undefined as T;
  }
  const text = await response.text();
  let payload: unknown = null;
  if (text) {
    try {
      payload = JSON.parse(text);
    } catch {
      payload = null;
    }
  }
  if (!response.ok) {
    const detail =
      payload && typeof payload === "object" && payload && "detail" in payload
        ? String((payload as { detail: unknown }).detail)
        : response.statusText || "Request failed";
    throw new ApiError(response.status, detail);
  }
  return payload as T;
}

export type LessonSummary = { id: string; title: string; summary: string; order?: number };

export type LearningPath = {
  id: string;
  title: string;
  summary: string;
  audience: string;
  lessons: LessonSummary[];
};

export type QuizQuestion = { prompt: string; choices: string[] };

export type Lesson = {
  id: string;
  path_id: string;
  title: string;
  summary: string;
  body: string;
  concepts: string[];
  sources: { title: string; url: string }[];
  quiz: QuizQuestion[];
};

export type ProjectCard = {
  slug: string;
  name: string;
  owner: string;
  repo: string;
  language: string;
  difficulty: string;
  summary: string;
  tags: string[];
  html_url: string;
};

export type ProjectGuide = ProjectCard & {
  prerequisites: string[];
  setup_steps: string[];
  test_steps: string[];
  contributing: string[];
  code_map: { path: string; why: string }[];
  docs: { title: string; url: string }[];
  review_notes: string[];
};

export type IssueHit = {
  number: number;
  title: string;
  url: string;
  why: string;
  comments: number;
  labels: string[];
};

export type ToolTrace = { name: string; ok: boolean; summary: string };

export type ChatMessage = {
  id: string;
  role: "user" | "assistant";
  content: string;
  tool_trace: ToolTrace[];
  created_at: string;
};

export type Conversation = {
  id: string;
  title: string;
  updated_at: string;
};

export type IdeProject = {
  slug: string;
  name: string;
  owner: string;
  repo: string;
  language: string;
  summary: string;
  clone_note?: string;
};

export type LearnLink = { href: string; label: string };

export type WorkspaceInfo = {
  id: string;
  slug: string;
  name: string;
  owner: string;
  repo: string;
  summary: string;
  language: string;
  contributing: string[];
  setup_steps?: string[];
  test_steps: string[];
  checklist: string[];
  recommended_model: string;
  clone_note?: string;
  issue_hint?: string;
  learn_links?: LearnLink[];
  file_chars?: number;
  reused?: boolean;
};

export type TreeEntry = { path: string; type: "file" | "dir" };

export type WorkspaceFile = {
  path: string;
  binary: boolean;
  truncated: boolean;
  text: string;
  sha256: string;
};

export type PendingEdit = { id: string; path: string; diff: string; status: string };

export type SearchHit = { path: string; line: number; text: string };
