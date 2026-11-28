"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";

import { api, IdeProject, WorkspaceInfo } from "@/lib/api";

export default function WorkspacePage() {
  const router = useRouter();
  const [projects, setProjects] = useState<IdeProject[] | null>(null);
  const [workspaces, setWorkspaces] = useState<WorkspaceInfo[]>([]);
  const [model, setModel] = useState("qwen2.5-coder:1.5b");
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState<string | null>(null);

  useEffect(() => {
    api<{ projects: IdeProject[]; recommended_model: string }>("api/v1/workspaces/projects")
      .then((body) => {
        setProjects(body.projects);
        setModel(body.recommended_model);
      })
      .catch((err: unknown) => setError(err instanceof Error ? err.message : "Could not load projects"));
    api<{ workspaces: WorkspaceInfo[] }>("api/v1/workspaces")
      .then((body) => setWorkspaces(body.workspaces))
      .catch(() => setWorkspaces([]));
  }, []);

  async function clone(slug: string) {
    setBusy(slug);
    setError(null);
    try {
      const created = await api<WorkspaceInfo>("api/v1/workspaces", {
        method: "POST",
        body: JSON.stringify({ project: slug }),
      });
      router.push(`/workspace/${created.id}`);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Clone failed");
      setBusy(null);
    }
  }

  return (
    <main className="mx-auto max-w-5xl px-4 py-12">
      <p className="text-sm uppercase tracking-[0.18em] text-rust">Local IDE</p>
      <h1 className="mt-3 font-serif text-5xl tracking-tight">Work in the repository</h1>
      <p className="mt-4 max-w-2xl text-muted">
        Pick BDK or rust-bitcoin. OSMA clones a shallow copy onto this computer, outside its own source tree, with git
        hooks turned off. You can read and edit files here. OSMA will not run the project, commit, push, or open a
        pull request.
      </p>
      <p className="mt-3 max-w-2xl text-sm text-muted">
        Guide mode needs no API key. For a suggested diff, run{" "}
        <code className="whitespace-nowrap">ollama pull {model}</code> and set{" "}
        <code className="whitespace-nowrap">OPENAI_MODEL={model}</code>. A 3B build of the same model is the next step
        up if the laptop has the memory.
      </p>
      {error ? <p className="mt-6 text-rust">{error}</p> : null}
      <ul className="mt-8 grid gap-4 md:grid-cols-2">
        {(projects || []).map((project) => (
          <li key={project.slug} className="rounded-2xl border border-line bg-card p-5 shadow-card">
            <p className="text-xs uppercase tracking-wide text-muted">
              {project.language} · {project.owner}/{project.repo}
            </p>
            <h2 className="mt-1 font-serif text-3xl">{project.name}</h2>
            <p className="mt-2 text-sm text-muted">{project.summary}</p>
            <button
              type="button"
              disabled={busy !== null}
              onClick={() => void clone(project.slug)}
              className="mt-4 rounded-full bg-ink px-4 py-2 text-sm text-paper disabled:opacity-50"
            >
              {busy === project.slug ? "Cloning…" : "Clone locally"}
            </button>
          </li>
        ))}
      </ul>
      {workspaces.length ? (
        <section className="mt-12">
          <h2 className="font-serif text-2xl">On this computer</h2>
          <ul className="mt-4 space-y-2">
            {workspaces.map((workspace) => (
              <li key={workspace.id}>
                <Link href={`/workspace/${workspace.id}`} className="text-sm hover:text-rust">
                  {workspace.name}{" "}
                  <span className="text-muted">
                    {workspace.owner}/{workspace.repo}
                  </span>
                </Link>
              </li>
            ))}
          </ul>
        </section>
      ) : null}
    </main>
  );
}
