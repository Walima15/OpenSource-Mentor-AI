"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

import { Markdown } from "@/components/Markdown";
import { Quiz } from "@/components/Quiz";
import { api, Lesson } from "@/lib/api";

export function LessonView({ pathId, lessonId }: { pathId: string; lessonId: string }) {
  const [lesson, setLesson] = useState<Lesson | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api<Lesson>(`api/v1/curriculum/lessons/${lessonId}`)
      .then(setLesson)
      .catch((err: unknown) => setError(err instanceof Error ? err.message : "Lesson not found"));
  }, [lessonId]);

  return (
    <main className="mx-auto max-w-3xl px-4 py-12">
      <Link href={`/learn/${pathId}`} className="text-sm text-muted hover:text-rust">
        Back to the path
      </Link>
      {error ? <p className="mt-6 text-rust">{error}</p> : null}
      {lesson ? (
        <>
          <h1 className="mt-3 font-serif text-5xl tracking-tight">{lesson.title}</h1>
          <p className="mt-3 text-lg text-muted">{lesson.summary}</p>
          <article className="mt-6">
            <Markdown text={lesson.body} />
          </article>
          {lesson.sources?.length ? (
            <ul className="mt-6 space-y-1 text-sm">
              {lesson.sources.map((source) => (
                <li key={source.url}>
                  <a className="text-rust underline" href={source.url} target="_blank" rel="noopener noreferrer">
                    {source.title}
                  </a>
                </li>
              ))}
            </ul>
          ) : null}
          <Quiz lessonId={lesson.id} questions={lesson.quiz} />
          <p className="mt-6 text-sm">
            <Link className="text-rust underline" href={`/chat?q=${encodeURIComponent(`Explain ${lesson.title}`)}`}>
              Ask the mentor about this lesson
            </Link>
          </p>
        </>
      ) : null}
    </main>
  );
}
