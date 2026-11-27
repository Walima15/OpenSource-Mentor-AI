"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

import { api, LearningPath } from "@/lib/api";

export default function LearnPage() {
  const [paths, setPaths] = useState<LearningPath[] | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api<{ paths: LearningPath[] }>("api/v1/curriculum/paths")
      .then((body) => setPaths(body.paths))
      .catch((err: unknown) => setError(err instanceof Error ? err.message : "Could not load the curriculum"));
  }, []);

  return (
    <main className="mx-auto max-w-4xl px-4 py-12">
      <h1 className="font-serif text-5xl tracking-tight">Curriculum</h1>
      <p className="mt-3 max-w-2xl text-muted">
        Three paths: the protocol, Lightning, and the contribution craft Bitcoin projects expect. Lessons are short
        enough to finish, and the quizzes do not show the answer until you commit.
      </p>
      {error ? <p className="mt-6 text-rust">{error}</p> : null}
      <div className="mt-8 space-y-6">
        {(paths || []).map((path) => (
          <section key={path.id} className="rounded-2xl border border-line bg-card p-5 shadow-card">
            <h2 className="font-serif text-3xl">
              <Link href={`/learn/${path.id}`}>{path.title}</Link>
            </h2>
            <p className="mt-2 text-sm text-muted">{path.summary}</p>
            <p className="mt-1 text-xs uppercase tracking-wide text-muted">{path.audience}</p>
            <ol className="mt-4 space-y-2 text-sm">
              {path.lessons.map((lesson, index) => (
                <li key={lesson.id}>
                  <Link href={`/learn/${path.id}/${lesson.id}`} className="hover:text-rust">
                    {index + 1}. {lesson.title}
                  </Link>
                  <span className="text-muted"> — {lesson.summary}</span>
                </li>
              ))}
            </ol>
          </section>
        ))}
      </div>
    </main>
  );
}
