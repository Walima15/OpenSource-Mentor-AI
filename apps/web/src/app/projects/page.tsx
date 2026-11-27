"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

import { api, ProjectCard } from "@/lib/api";

export default function ProjectsPage() {
  const [projects, setProjects] = useState<ProjectCard[] | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api<{ projects: ProjectCard[] }>("api/v1/projects")
      .then((body) => setProjects(body.projects))
      .catch((err: unknown) => setError(err instanceof Error ? err.message : "Could not load projects"));
  }, []);

  return (
    <main className="mx-auto max-w-5xl px-4 py-12">
      <h1 className="font-serif text-5xl tracking-tight">Projects</h1>
      <p className="mt-3 max-w-2xl text-muted">
        A short list, not a directory of everything that mentions Bitcoin. Setup commands point at each project&apos;s
        own docs because those commands change.
      </p>
      {error ? <p className="mt-6 text-rust">{error}</p> : null}
      <ul className="mt-8 grid gap-4 md:grid-cols-2">
        {(projects || []).map((project) => (
          <li key={project.slug} className="rounded-2xl border border-line bg-card p-5 shadow-card">
            <p className="text-xs uppercase tracking-wide text-muted">
              {project.language} · {project.difficulty}
            </p>
            <h2 className="mt-1 font-serif text-3xl">
              <Link href={`/projects/${project.slug}`}>{project.name}</Link>
            </h2>
            <p className="mt-2 text-sm text-muted">{project.summary}</p>
            <p className="mt-3 text-xs text-muted">
              {project.owner}/{project.repo}
            </p>
          </li>
        ))}
      </ul>
    </main>
  );
}
