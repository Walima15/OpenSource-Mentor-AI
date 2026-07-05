"use client";

import { useCallback, useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { PageHeader } from "@/components/PageHeader";
import { api, ApiError } from "@/lib/api-client";
import type { Recommendation } from "@/types";

function scoreTone(score: number): string {
  if (score >= 75) return "bg-emerald-500/15 text-emerald-300";
  if (score >= 55) return "bg-brand-600/15 text-brand-200";
  return "bg-surface-muted text-slate-300";
}

export default function RecommendationsPage() {
  const router = useRouter();
  const [recs, setRecs] = useState<Recommendation[]>([]);
  const [loading, setLoading] = useState(true);
  const [scanning, setScanning] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [note, setNote] = useState<string | null>(null);

  const load = useCallback(async () => {
    try {
      setRecs(await api.getRecommendations());
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Could not load matches");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  async function scan() {
    setScanning(true);
    setError(null);
    setNote(null);
    try {
      const result = await api.scanRecommendations();
      setNote(
        `Scanned ${result.scanned_repos} repo(s), cached ${result.cached_issues} issue(s).`,
      );
      await load();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Scan failed");
    } finally {
      setScanning(false);
    }
  }

  async function mentor(rec: Recommendation) {
    try {
      const session = await api.createSession({
        repo_id: rec.repo_id,
        issue_number: rec.issue_number,
        title: `Issue #${rec.issue_number}: ${rec.title}`,
      });
      router.push(
        `/dashboard/repos/${rec.repo_id}/sessions/${session.id}`,
      );
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Could not start session");
    }
  }

  return (
    <div>
      <PageHeader
        title="Recommended issues"
        subtitle="Beginner-friendly opportunities matched to your skills"
        action={
          <button
            onClick={scan}
            className="btn-primary"
            disabled={scanning}
          >
            {scanning ? "Scanning..." : "Scan for new issues"}
          </button>
        }
      />

      <div className="p-6">
        {error && (
          <p className="mb-4 rounded-lg bg-red-500/10 px-3 py-2 text-sm text-red-300">
            {error}
          </p>
        )}
        {note && (
          <p className="mb-4 rounded-lg bg-emerald-500/10 px-3 py-2 text-sm text-emerald-300">
            {note}
          </p>
        )}

        {loading ? (
          <p className="text-sm text-slate-500">Loading matches...</p>
        ) : recs.length === 0 ? (
          <div className="card">
            <p className="text-sm text-slate-300">No matches yet.</p>
            <p className="mt-1 text-sm text-slate-500">
              Track a few repositories, then run a scan to discover
              beginner-friendly issues matched to your skills.
            </p>
          </div>
        ) : (
          <div className="space-y-3">
            {recs.map((rec) => (
              <div
                key={`${rec.repo_id}-${rec.issue_number}`}
                className="card"
              >
                <div className="flex items-start justify-between gap-3">
                  <div className="min-w-0">
                    <p className="text-xs text-slate-500">
                      {rec.repo_full_name} · #{rec.issue_number}
                      {rec.language ? ` · ${rec.language}` : ""}
                    </p>
                    <a
                      href={rec.url}
                      target="_blank"
                      rel="noreferrer"
                      className="mt-1 block truncate font-medium text-slate-100 hover:text-brand-200"
                    >
                      {rec.title}
                    </a>
                  </div>
                  <span
                    className={`shrink-0 rounded-full px-2.5 py-1 text-xs font-semibold ${scoreTone(
                      rec.score,
                    )}`}
                    title="Match score"
                  >
                    {Math.round(rec.score)}
                  </span>
                </div>

                {rec.labels.length > 0 && (
                  <div className="mt-2 flex flex-wrap gap-1.5">
                    {rec.labels.slice(0, 6).map((label) => (
                      <span
                        key={label}
                        className="rounded-full bg-surface-muted px-2 py-0.5 text-xs text-slate-400"
                      >
                        {label}
                      </span>
                    ))}
                  </div>
                )}

                {rec.reasons.length > 0 && (
                  <ul className="mt-3 space-y-1 text-sm text-slate-400">
                    {rec.reasons.map((reason) => (
                      <li key={reason} className="flex items-start gap-2">
                        <span className="text-brand-400">•</span>
                        {reason}
                      </li>
                    ))}
                  </ul>
                )}

                <div className="mt-3 flex items-center justify-between">
                  <span className="text-xs text-slate-500">
                    {rec.comments} comment{rec.comments === 1 ? "" : "s"}
                  </span>
                  <button
                    onClick={() => mentor(rec)}
                    className="btn-secondary"
                  >
                    Start mentor session
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
