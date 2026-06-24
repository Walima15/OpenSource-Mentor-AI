"use client";

import { use, useState } from "react";
import Link from "next/link";
import { PageHeader } from "@/components/PageHeader";
import { ChatPanel } from "@/components/ChatPanel";
import { Markdown } from "@/components/Markdown";
import { DiffViewer } from "@/components/DiffViewer";
import { api, ApiError } from "@/lib/api-client";
import type {
  CodeSuggestion,
  ContributionPlan,
  PullRequestDraft,
  PullRequestResult,
} from "@/types";

export default function MentorWorkspace({
  params,
}: {
  params: Promise<{ repoId: string; sessionId: string }>;
}) {
  const { repoId, sessionId } = use(params);
  const [tab, setTab] = useState<"chat" | "contribute" | "pr">("chat");

  return (
    <div className="flex h-full flex-col">
      <PageHeader
        title="Mentor session"
        subtitle="Chat with your mentor and build a contribution step by step"
        action={
          <Link href={`/dashboard/repos/${repoId}`} className="btn-ghost">
            ← Back to repo
          </Link>
        }
      />

      <div className="flex gap-1 border-b border-surface-border px-6">
        {(["chat", "contribute", "pr"] as const).map((t) => (
          <button
            key={t}
            onClick={() => setTab(t)}
            className={`px-4 py-3 text-sm ${
              tab === t
                ? "border-b-2 border-brand-500 text-slate-100"
                : "text-slate-400 hover:text-slate-200"
            }`}
          >
            {t === "pr" ? "Pull request" : t === "chat" ? "Chat" : "Contribute"}
          </button>
        ))}
      </div>

      <div className="min-h-0 flex-1">
        {tab === "chat" && (
          <div className="grid h-full lg:grid-cols-[1fr_360px]">
            <div className="min-h-0 border-r border-surface-border">
              <ChatPanel sessionId={sessionId} />
            </div>
            <MentorActions sessionId={sessionId} />
          </div>
        )}
        {tab === "contribute" && (
          <ContributeTab sessionId={sessionId} />
        )}
        {tab === "pr" && <PullRequestTab sessionId={sessionId} />}
      </div>
    </div>
  );
}

function MentorActions({ sessionId }: { sessionId: string }) {
  const [output, setOutput] = useState<string | null>(null);
  const [busy, setBusy] = useState<string | null>(null);

  async function run(kind: "issue" | "repo") {
    setBusy(kind);
    setOutput(null);
    try {
      const res =
        kind === "issue"
          ? await api.explainIssue(sessionId)
          : await api.explainRepo(sessionId);
      setOutput(res.content);
    } catch (err) {
      setOutput(err instanceof ApiError ? err.message : "Request failed");
    } finally {
      setBusy(null);
    }
  }

  return (
    <div className="scrollbar-thin overflow-y-auto p-4">
      <h3 className="mb-3 text-sm font-semibold uppercase tracking-wide text-slate-400">
        Quick actions
      </h3>
      <div className="space-y-2">
        <button
          onClick={() => run("issue")}
          disabled={busy !== null}
          className="btn-secondary w-full"
        >
          {busy === "issue" ? "Explaining..." : "Explain the issue"}
        </button>
        <button
          onClick={() => run("repo")}
          disabled={busy !== null}
          className="btn-secondary w-full"
        >
          {busy === "repo" ? "Explaining..." : "Explain the repo"}
        </button>
      </div>
      {output && (
        <div className="card mt-4">
          <Markdown content={output} />
        </div>
      )}
    </div>
  );
}

function ContributeTab({ sessionId }: { sessionId: string }) {
  const [plan, setPlan] = useState<ContributionPlan | null>(null);
  const [suggestion, setSuggestion] = useState<CodeSuggestion | null>(null);
  const [filePath, setFilePath] = useState("");
  const [instruction, setInstruction] = useState("");
  const [busy, setBusy] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  async function createPlan() {
    setBusy("plan");
    setError(null);
    try {
      setPlan(await api.createPlan(sessionId));
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Could not create plan");
    } finally {
      setBusy(null);
    }
  }

  async function recommend() {
    if (!plan) return;
    setBusy("files");
    try {
      setPlan(await api.recommendFiles(plan.id));
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Failed");
    } finally {
      setBusy(null);
    }
  }

  async function suggest() {
    if (!plan || !filePath.trim()) return;
    setBusy("code");
    setError(null);
    try {
      setSuggestion(
        await api.suggestCode(plan.id, filePath.trim(), instruction || undefined),
      );
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Failed");
    } finally {
      setBusy(null);
    }
  }

  return (
    <div className="scrollbar-thin h-full overflow-y-auto p-6">
      <div className="grid gap-6 lg:grid-cols-2">
        <div className="space-y-4">
          <div className="card">
            <div className="flex items-center justify-between">
              <h3 className="font-semibold">Implementation plan</h3>
              <button
                onClick={createPlan}
                disabled={busy === "plan"}
                className="btn-primary"
              >
                {busy === "plan" ? "Planning..." : "Generate plan"}
              </button>
            </div>
            {error && <p className="mt-3 text-sm text-red-300">{error}</p>}
            {plan ? (
              <div className="mt-4 space-y-4">
                <Markdown content={plan.summary} />
                {plan.steps?.length > 0 && (
                  <ol className="space-y-2">
                    {plan.steps.map((s) => (
                      <li key={s.order} className="rounded-lg bg-surface-muted p-3">
                        <p className="text-sm font-medium text-slate-100">
                          {s.order}. {s.title}
                        </p>
                        <p className="mt-1 text-sm text-slate-400">{s.detail}</p>
                      </li>
                    ))}
                  </ol>
                )}
                <button
                  onClick={recommend}
                  disabled={busy === "files"}
                  className="btn-secondary"
                >
                  {busy === "files" ? "Finding files..." : "Recommend files"}
                </button>
                {plan.recommended_files?.length > 0 && (
                  <ul className="space-y-1 text-sm">
                    {plan.recommended_files.map((f) => (
                      <li key={f.path}>
                        <button
                          onClick={() => setFilePath(f.path)}
                          className="font-mono text-brand-300 hover:underline"
                        >
                          {f.path}
                        </button>
                        <span className="text-slate-500"> — {f.reason}</span>
                      </li>
                    ))}
                  </ul>
                )}
              </div>
            ) : (
              <p className="mt-3 text-sm text-slate-500">
                Generate a step-by-step plan for tackling this contribution.
              </p>
            )}
          </div>
        </div>

        <div className="space-y-4">
          <div className="card">
            <h3 className="font-semibold">Code suggestion</h3>
            <div className="mt-3 space-y-2">
              <input
                value={filePath}
                onChange={(e) => setFilePath(e.target.value)}
                placeholder="path/to/file.py"
                className="input font-mono"
              />
              <textarea
                value={instruction}
                onChange={(e) => setInstruction(e.target.value)}
                placeholder="Optional: what should change in this file?"
                rows={2}
                className="input resize-none"
              />
              <button
                onClick={suggest}
                disabled={busy === "code" || !plan || !filePath.trim()}
                className="btn-primary"
              >
                {busy === "code" ? "Generating..." : "Suggest code"}
              </button>
              {!plan && (
                <p className="text-xs text-amber-300">
                  Create a plan first to enable code suggestions.
                </p>
              )}
            </div>
          </div>

          {suggestion && (
            <div className="card">
              <h4 className="mb-2 font-mono text-sm text-brand-300">
                {suggestion.file_path}
              </h4>
              <DiffViewer diff={suggestion.diff} />
              <div className="mt-4">
                <Markdown content={suggestion.explanation} />
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

function PullRequestTab({ sessionId }: { sessionId: string }) {
  const [draft, setDraft] = useState<PullRequestDraft | null>(null);
  const [summary, setSummary] = useState<string | null>(null);
  const [planId, setPlanId] = useState<string | null>(null);
  const [busy, setBusy] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [asDraft, setAsDraft] = useState(true);
  const [result, setResult] = useState<PullRequestResult | null>(null);

  async function ensurePlan(): Promise<string> {
    if (planId) return planId;
    const plan = await api.createPlan(sessionId);
    setPlanId(plan.id);
    return plan.id;
  }

  async function run(kind: "commit" | "description" | "summary") {
    setBusy(kind);
    setError(null);
    try {
      const id = await ensurePlan();
      if (kind === "commit") setDraft(await api.commitMessage(id));
      else if (kind === "description") setDraft(await api.prDescription(id));
      else setSummary((await api.summarize(id)).content);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Request failed");
    } finally {
      setBusy(null);
    }
  }

  async function createPr() {
    setBusy("create");
    setError(null);
    setResult(null);
    try {
      const id = await ensurePlan();
      setResult(await api.createPullRequest(id, asDraft));
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Could not open pull request");
    } finally {
      setBusy(null);
    }
  }

  return (
    <div className="scrollbar-thin h-full overflow-y-auto p-6">
      <div className="mb-4 flex flex-wrap items-center gap-2">
        <button
          onClick={() => run("commit")}
          disabled={busy !== null}
          className="btn-secondary"
        >
          {busy === "commit" ? "..." : "Generate commit message"}
        </button>
        <button
          onClick={() => run("description")}
          disabled={busy !== null}
          className="btn-secondary"
        >
          {busy === "description" ? "..." : "Generate PR description"}
        </button>
        <button
          onClick={() => run("summary")}
          disabled={busy !== null}
          className="btn-secondary"
        >
          {busy === "summary" ? "..." : "Summarize changes"}
        </button>
        <div className="ml-auto flex items-center gap-3">
          <label className="flex items-center gap-1.5 text-xs text-slate-400">
            <input
              type="checkbox"
              checked={asDraft}
              onChange={(e) => setAsDraft(e.target.checked)}
            />
            Draft PR
          </label>
          <button
            onClick={createPr}
            disabled={busy !== null}
            className="btn-primary"
          >
            {busy === "create" ? "Opening PR..." : "Create pull request"}
          </button>
        </div>
      </div>

      {error && <p className="text-sm text-red-300">{error}</p>}

      {result && (
        <div className="card mb-6 border-emerald-600/40">
          <div className="flex items-center justify-between">
            <h3 className="font-semibold text-emerald-300">
              Pull request #{result.number} opened
            </h3>
            <a
              href={result.url}
              target="_blank"
              rel="noreferrer"
              className="btn-secondary"
            >
              View on GitHub
            </a>
          </div>
          <p className="mt-2 text-sm text-slate-400">
            Branch <code className="text-brand-300">{result.head}</code>
          </p>
          {result.applied_files.length > 0 && (
            <p className="mt-2 text-sm text-slate-400">
              Committed: {result.applied_files.map((f) => (
                <code key={f} className="mr-2 text-emerald-300">{f}</code>
              ))}
            </p>
          )}
          {result.skipped_files.length > 0 && (
            <p className="mt-1 text-sm text-amber-300">
              Skipped (could not auto-apply): {result.skipped_files.join(", ")}
            </p>
          )}
          {result.note && (
            <p className="mt-2 text-xs text-slate-500">{result.note}</p>
          )}
        </div>
      )}

      <div className="grid gap-6 lg:grid-cols-2">
        {draft?.commit_message && (
          <div className="card">
            <h3 className="mb-2 font-semibold">Commit message</h3>
            <pre className="scrollbar-thin overflow-x-auto whitespace-pre-wrap rounded-lg bg-surface p-3 font-mono text-xs text-slate-200">
              {draft.commit_message}
            </pre>
          </div>
        )}
        {draft?.body && (
          <div className="card">
            <h3 className="mb-2 font-semibold">
              Pull request description
              {draft.branch_name && (
                <span className="ml-2 font-mono text-xs text-slate-500">
                  {draft.branch_name}
                </span>
              )}
            </h3>
            <Markdown content={draft.body} />
          </div>
        )}
        {summary && (
          <div className="card">
            <h3 className="mb-2 font-semibold">Change summary</h3>
            <Markdown content={summary} />
          </div>
        )}
      </div>

      {!draft && !summary && (
        <p className="text-sm text-slate-500">
          Generate commit messages, a PR description, and a change summary from
          your code suggestions.
        </p>
      )}
    </div>
  );
}
