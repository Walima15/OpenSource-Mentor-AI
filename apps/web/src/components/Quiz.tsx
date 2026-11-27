"use client";

import { FormEvent, useState } from "react";

import { api, QuizQuestion } from "@/lib/api";

type Grade = {
  score: number;
  total: number;
  results: { prompt: string; correct: boolean; explanation: string; correct_choice: string }[];
};

export function Quiz({ lessonId, questions }: { lessonId: string; questions: QuizQuestion[] }) {
  const [answers, setAnswers] = useState<number[]>(() => questions.map(() => -1));
  const [grade, setGrade] = useState<Grade | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  async function onSubmit(event: FormEvent) {
    event.preventDefault();
    if (answers.some((answer) => answer < 0)) {
      setError("Answer every question first.");
      return;
    }
    setBusy(true);
    setError(null);
    try {
      const result = await api<Grade>(`api/v1/curriculum/lessons/${lessonId}/quiz`, {
        method: "POST",
        body: JSON.stringify({ answers }),
      });
      setGrade(result);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not grade the quiz");
    } finally {
      setBusy(false);
    }
  }

  return (
    <form onSubmit={onSubmit} className="mt-8 rounded-2xl border border-line bg-card p-5 shadow-card">
      <h2 className="font-serif text-2xl">Check yourself</h2>
      <p className="mt-1 text-sm text-muted">The lesson page does not reveal the answers until you submit.</p>
      <ol className="mt-4 space-y-5">
        {questions.map((question, index) => (
          <li key={question.prompt}>
            <p className="font-medium">
              {index + 1}. {question.prompt}
            </p>
            <div className="mt-2 space-y-1.5">
              {question.choices.map((choice, choiceIndex) => (
                <label key={choice} className="flex cursor-pointer items-start gap-2 text-sm">
                  <input
                    type="radio"
                    className="mt-1"
                    name={`q-${index}`}
                    checked={answers[index] === choiceIndex}
                    onChange={() => {
                      const next = [...answers];
                      next[index] = choiceIndex;
                      setAnswers(next);
                    }}
                  />
                  <span>{choice}</span>
                </label>
              ))}
            </div>
          </li>
        ))}
      </ol>
      {error ? <p className="mt-4 text-sm text-rust">{error}</p> : null}
      <button
        type="submit"
        disabled={busy}
        className="mt-5 rounded-full bg-ink px-4 py-2 text-sm text-paper disabled:opacity-60"
      >
        {busy ? "Grading…" : "Grade quiz"}
      </button>
      {grade ? (
        <div className="mt-5 border-t border-line pt-4">
          <p className="font-serif text-xl">
            {grade.score}/{grade.total}
          </p>
          <ul className="mt-3 space-y-3 text-sm">
            {grade.results.map((result) => (
              <li key={result.prompt}>
                <p className={result.correct ? "text-moss" : "text-rust"}>
                  {result.correct ? "Correct" : "Not yet"}. {result.prompt}
                </p>
                <p className="text-muted">{result.explanation}</p>
              </li>
            ))}
          </ul>
        </div>
      ) : null}
    </form>
  );
}
