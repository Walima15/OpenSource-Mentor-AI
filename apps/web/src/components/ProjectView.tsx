"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

import { api, IssueHit, ProjectGuide } from "@/lib/api";

export function ProjectView({ slug }: { slug: string }) {
  const [project, setProject] = useState<ProjectGuide | null>(null);
  const [issues, setIssues] = useState<IssueHit[] | null>(null);
  const [note, setNote] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    api<ProjectGuide>(`api/v1/projects/${slug}`)
      .then(setProject)
      .catch((err: unknown) => setError(err instanceof Error ? err.message : "Project not found"));
  }, [slug]);

  async function loadIssues() {
    setBusy(true);
    setError(null);
    try {
      const body = await api<{ issues: IssueHit[]; note: string | null }>(
        `api/v1/projects/${slug}/issues?limit=5`,
      );
      setIssues(body.issues);
      setNote(body.note);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not load issues");
    } finally {
      setBusy(false);
    }
  }

  return (
    <main className="mx-auto max-w-3xl px-4 py-12">
      <Link href="/projects" className="text-sm text-muted hover:text-rust">
        Projects
      </Link>
      {error ? <p className="mt-6 text-rust">{error}</p> : null}
      {project ? (
        <>
          <p className="mt-3 text-xs uppercase tracking-wide text-muted">
            {project.language} · {project.difficulty}
          </p>
          <h1 className="font-serif text-5xl tracking-tight">{project.name}</h1>
          <p className="mt-3 text-muted">{project.summary}</p>
          <div className="mt-4 flex flex-wrap gap-3 text-sm">
            <a className="text-rust underline" href={project.html_url} target="_blank" rel="noopener noreferrer">
              {project.owner}/{project.repo}
            </a>
            <Link className="text-rust underline" href={`/chat?q=${encodeURIComponent(`How do I build ${project.name}?`)}`}>
              Ask the mentor
            </Link>
          </div>
          <Section title="Before you build" items={project.prerequisites} />
          <Section title="Setup" items={project.setup_steps} ordered />
          <Section title="Tests" items={project.test_steps} />
          <Section title="Contributing" items={project.contributing} />
          <h2 className="mt-8 font-serif text-2xl">Where to look</h2>
          <ul className="mt-2 space-y-2 text-sm">
            {project.code_map.map((item) => (
              <li key={item.path}>
                <code className="rounded bg-[#f3e6d4] px-1">{item.path}</code>
                <span className="text-muted"> — {item.why}</span>
              </li>
            ))}
          </ul>
          <h2 className="mt-8 font-serif text-2xl">Docs</h2>
          <ul className="mt-2 space-y-1 text-sm">
            {project.docs.map((doc) => (
              <li key={doc.url}>
                <a className="text-rust underline" href={doc.url} target="_blank" rel="noopener noreferrer">
                  {doc.title}
                </a>
              </li>
            ))}
          </ul>
          <button
            type="button"
            onClick={() => void loadIssues()}
            disabled={busy}
            className="mt-8 rounded-full bg-ink px-4 py-2 text-sm text-paper disabled:opacity-60"
          >
            {busy ? "Asking GitHub…" : "Find good first issues"}
          </button>
          {note ? <p className="mt-4 text-sm text-muted">{note}</p> : null}
          {issues ? (
            <ul className="mt-4 space-y-3">
              {issues.map((issue) => (
                <li key={issue.number} className="rounded-2xl border border-line bg-card p-4">
                  <a className="font-medium text-rust underline" href={issue.url} target="_blank" rel="noopener noreferrer">
                    #{issue.number} {issue.title}
                  </a>
                  <p className="mt-1 text-sm text-muted">{issue.why}</p>
                </li>
              ))}
            </ul>
          ) : null}
        </>
      ) : null}
    </main>
  );
}

function Section({ title, items, ordered = false }: { title: string; items: string[]; ordered?: boolean }) {
  const List = ordered ? "ol" : "ul";
  return (
    <>
      <h2 className="mt-8 font-serif text-2xl">{title}</h2>
      <List className={`mt-2 space-y-2 text-sm ${ordered ? "list-decimal pl-5" : "list-disc pl-5"}`}>
        {items.map((item) => (
          <li key={item}>{item}</li>
        ))}
      </List>
    </>
  );
}
