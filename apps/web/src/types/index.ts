// Frontend types mirroring the FastAPI schemas. Kept local to the web app for
// simple imports; the canonical definitions live in packages/shared-types.

export type IndexStatus = "pending" | "indexing" | "ready" | "failed";
export type SkillLevel = "beginner" | "intermediate" | "advanced";
export type MentorRole = "user" | "assistant" | "system" | "tool";
export type PlanStatus = "draft" | "in_progress" | "completed" | "abandoned";

export interface Profile {
  id: string;
  github_username: string | null;
  github_id: number | null;
  avatar_url: string | null;
  bio: string | null;
  created_at: string;
  updated_at: string;
}

export interface Skill {
  id: string;
  user_id: string;
  language: string;
  level: SkillLevel;
  score: number;
  updated_at: string;
}

export interface TrackedRepo {
  id: string;
  owner: string;
  name: string;
  default_branch: string;
  description: string | null;
  stars: number;
  last_indexed_at: string | null;
  index_status: IndexStatus;
}

export interface RepoSearchResult {
  owner: string;
  name: string;
  full_name: string;
  description: string | null;
  stars: number;
  language: string | null;
  url: string;
}

export interface Issue {
  number: number;
  title: string;
  body: string | null;
  labels: string[];
  state: string;
  url: string;
  comments: number;
  created_at: string;
}

export interface Recommendation {
  repo_id: string;
  repo_full_name: string;
  issue_number: number;
  title: string;
  url: string;
  labels: string[];
  comments: number;
  language: string | null;
  score: number;
  reasons: string[];
}

export interface ScanResult {
  scanned_repos: number;
  cached_issues: number;
}

export interface MentorSession {
  id: string;
  repo_id: string;
  issue_number: number | null;
  title: string;
  created_at: string;
}

export interface MentorMessage {
  id: string;
  session_id: string;
  role: MentorRole;
  content: string;
  metadata: Record<string, unknown> | null;
  created_at: string;
}

export interface PlanStep {
  order: number;
  title: string;
  detail: string;
}

export interface RecommendedFile {
  path: string;
  reason: string;
}

export interface ContributionPlan {
  id: string;
  session_id: string;
  summary: string;
  steps: PlanStep[];
  recommended_files: RecommendedFile[];
  status: PlanStatus;
  created_at: string;
}

export interface CodeSuggestion {
  id: string;
  plan_id: string;
  file_path: string;
  diff: string;
  explanation: string;
  tests: string | null;
  created_at: string;
}

export interface PullRequestDraft {
  id: string;
  plan_id: string;
  branch_name: string;
  commit_message: string;
  title: string;
  body: string;
  created_at: string;
}

export interface PullRequestResult {
  url: string;
  number: number;
  branch: string;
  head: string;
  applied_files: string[];
  skipped_files: string[];
  note: string | null;
}
