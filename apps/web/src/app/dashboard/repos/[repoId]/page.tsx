"use client";

import { useCallback, useEffect, useState } from "react";
import { use } from "react";
import { useRouter } from "next/navigation";
import { PageHeader } from "@/components/PageHeader";
import { StatusBadge, LabelChip } from "@/components/StatusBadge";
import { Markdown } from "@/components/Markdown";
import { api, ApiError } from "@/lib/api-client";
import { repoUrl } from "@/lib/github";
import type { Issue, TrackedRepo } from "@/types";

type Tab = "overview" | "structure" | "issues";

export default function RepoDetailPage({
  params,
}: {
  params: Promise<{ repoId: string }>;
}) {
  const { repoId } = use(params);
  const router = useRouter();
  const [repo, setRepo] = useState<TrackedRepo | null>(null);
  const [tab, setTab] = useState<Tab>("overview");
  const [error, setError] = useState<string | null>(null);

  const loadRepo = useCallback(
    () => api.getRepo(repoId).then(setRepo).catch(() => undefined),
    [repoId],
  );

  useEffect(() => {
    loadRepo();
  }, [loadRepo]);

  // Poll index status while indexing.
  useEffect(() => {
    if (repo?.index_status !== "indexing") return;
    const t = setInterval(loadRepo, 4000);
    return () => clearInterval(t);
  }, [repo?.index_status, loadRepo]);

  async function startIndex() {
    setError(null);
    try {
      await api.indexRepo(repoId);
      setRepo((r) => (r ? { ...r, index_status: "indexing" } : r));
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Indexing failed");
    }
  }

  if (!repo) {
    return (
      <div className="p-6 text-sm text-slate-500">Loading repository...</div>
    );
  }

  return (
    <div>
      <PageHeader
        title={`${repo.owner}/${repo.name}`}
        subtitle={repo.description ?? undefined}
        action={
          <div className="flex items-center gap-3">
            <StatusBadge status={repo.index_status} />
            <button
              onClick={startIndex}
              disabled={repo.index_status === "indexing"}
              className="btn-secondary"
            >
              {repo.index_status === "ready" ? "Re-index" : "Index repo"}
            </button>
            <a
              href={repoUrl(repo.owner, repo.name)}
              target="_blank"
              rel="noreferrer"
              className="btn-ghost"
            >
              View on GitHub
            </a>
          </div>
        }
      />

      {error && (
        <p className="mx-6 mt-4 rounded-lg bg-red-500/10 px-3 py-2 text-sm text-red-300">
          {error}
        </p>
      )}

      <div className="flex gap-1 border-b border-surface-border px-6">
        {(["overview", "structure", "issues"] as Tab[]).map((t) => (
          <button
            key={t}
            onClick={() => setTab(t)}
            className={`px-4 py-3 text-sm capitalize ${
              tab === t
                ? "border-b-2 border-brand-500 text-slate-100"
                : "text-slate-400 hover:text-slate-200"
            }`}
          >
            {t}
          </button>
        ))}
      </div>

      <div className="p-6">
        {tab === "overview" && <OverviewTab repo={repo} />}
        {tab === "structure" && <StructureTab repoId={repoId} />}
        {tab === "issues" && <IssuesTab repo={repo} router={router} />}
      </div>
    </div>
  );
}

function OverviewTab({ repo }: { repo: TrackedRepo }) {
  const [explanation, setExplanation] = useState<string | null>(null);
  const [docs, setDocs] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api
      .repoDocs(repo.id)
      .then((d) => setDocs(d.readme))
      .catch(() => undefined);
  }, [repo.id]);

  async function explain() {
    setBusy(true);
    setError(null);
    try {
      const session = await api.createSession({ repo_id: repo.id });
      const res = await api.explainRepo(session.id);
      setExplanation(res.content);
    } catch (err) {
      setError(
        err instanceof ApiError ? err.message : "Could not generate explanation",
      );
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="grid gap-6 lg:grid-cols-2">
      <div className="card">
        <div className="flex items-center justify-between">
          <h3 className="font-semibold">AI architecture explainer</h3>
          <button onClick={explain} disabled={busy} className="btn-primary">
            {busy ? "Analyzing..." : "Explain this repo"}
          </button>
        </div>
        {repo.index_status !== "ready" && (
          <p className="mt-3 text-xs text-amber-300">
            Tip: index the repository first for code-grounded explanations.
          </p>
        )}
        {error && <p className="mt-3 text-sm text-red-300">{error}</p>}
        <div className="mt-4">
          {explanation ? (
            <Markdown content={explanation} />
          ) : (
            <p className="text-sm text-slate-500">
              Generate a plain-language overview of the project architecture.
            </p>
          )}
        </div>
      </div>

      <div className="card">
        <h3 className="font-semibold">README</h3>
        <div className="scrollbar-thin mt-4 max-h-[60vh] overflow-y-auto">
          {docs ? (
            <Markdown content={docs} />
          ) : (
            <p className="text-sm text-slate-500">No README found.</p>
          )}
        </div>
      </div>
    </div>
  );
}

function StructureTab({ repoId }: { repoId: string }) {
  const [tree, setTree] = useState<{ path: string; type: string }[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api
      .repoStructure(repoId)
      .then((s) => setTree(s.tree))
      .catch((err) =>
        setError(err instanceof ApiError ? err.message : "Failed to load tree"),
      )
      .finally(() => setLoading(false));
  }, [repoId]);

  if (loading) return <p className="text-sm text-slate-500">Loading tree...</p>;
  if (error) return <p className="text-sm text-red-300">{error}</p>;

  return (
    <div className="card scrollbar-thin max-h-[70vh] overflow-y-auto">
      <ul className="space-y-1 font-mono text-xs">
        {tree.slice(0, 800).map((node) => (
          <li
            key={node.path}
            className={node.type === "dir" ? "text-brand-300" : "text-slate-400"}
          >
            {node.type === "dir" ? "📁" : "📄"} {node.path}
          </li>
        ))}
      </ul>
    </div>
  );
}

function IssuesTab({
  repo,
  router,
}: {
  repo: TrackedRepo;
  router: ReturnType<typeof useRouter>;
}) {
  const [issues, setIssues] = useState<Issue[]>([]);
  const [filter, setFilter] = useState("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    setLoading(true);
    api
      .listIssues(repo.id, filter || undefined)
      .then(setIssues)
      .catch((err) =>
        setError(err instanceof ApiError ? err.message : "Failed to load issues"),
      )
      .finally(() => setLoading(false));
  }, [repo.id, filter]);

  async function startMentor(issue: Issue) {
    const session = await api.createSession({
      repo_id: repo.id,
      issue_number: issue.number,
      title: `#${issue.number} ${issue.title}`,
    });
    router.push(`/dashboard/repos/${repo.id}/sessions/${session.id}`);
  }

  return (
    <div>
      <div className="mb-4 flex gap-2">
        {[
          { label: "Beginner-friendly", value: "" },
          { label: "good first issue", value: "good first issue" },
          { label: "help wanted", value: "help wanted" },
          { label: "bug", value: "bug" },
        ].map((f) => (
          <button
            key={f.label}
            onClick={() => setFilter(f.value)}
            className={`badge ${
              filter === f.value
                ? "bg-brand-600/20 text-brand-200"
                : "bg-surface-muted text-slate-400"
            }`}
          >
            {f.label}
          </button>
        ))}
      </div>

      {loading && <p className="text-sm text-slate-500">Loading issues...</p>}
      {error && <p className="text-sm text-red-300">{error}</p>}
      {!loading && issues.length === 0 && (
        <p className="text-sm text-slate-500">No matching issues found.</p>
      )}

      <div className="space-y-3">
        {issues.map((issue) => (
          <div key={issue.number} className="card">
            <div className="flex items-start justify-between gap-3">
              <div>
                <p className="font-medium text-slate-100">
                  #{issue.number} {issue.title}
                </p>
                <div className="mt-2 flex flex-wrap gap-1.5">
                  {issue.labels.map((l) => (
                    <LabelChip key={l} label={l} />
                  ))}
                </div>
              </div>
              <button
                onClick={() => startMentor(issue)}
                className="btn-primary shrink-0"
              >
                Start mentor
              </button>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
