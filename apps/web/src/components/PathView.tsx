"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

import { api, LearningPath } from "@/lib/api";

export function PathView({ pathId }: { pathId: string }) {
  const [path, setPath] = useState<LearningPath | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api<LearningPath>(`api/v1/curriculum/paths/${pathId}`)
      .then(setPath)
      .catch((err: unknown) => setError(err instanceof Error ? err.message : "Path not found"));
  }, [pathId]);

  return (
    <main className="mx-auto max-w-3xl px-4 py-12">
      <Link href="/learn" className="text-sm text-muted hover:text-rust">
        Curriculum
      </Link>
      {error ? <p className="mt-6 text-rust">{error}</p> : null}
      {path ? (
        <>
          <h1 className="mt-3 font-serif text-5xl tracking-tight">{path.title}</h1>
          <p className="mt-3 text-muted">{path.summary}</p>
          <ol className="mt-8 space-y-3">
            {path.lessons.map((lesson, index) => (
              <li key={lesson.id} className="rounded-2xl border border-line bg-card p-4">
                <Link href={`/learn/${path.id}/${lesson.id}`} className="font-serif text-2xl hover:text-rust">
                  {index + 1}. {lesson.title}
                </Link>
                <p className="mt-1 text-sm text-muted">{lesson.summary}</p>
              </li>
            ))}
          </ol>
        </>
      ) : null}
    </main>
  );
}
