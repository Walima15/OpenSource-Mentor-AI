"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { PageHeader } from "@/components/PageHeader";
import { api } from "@/lib/api-client";
import type { MentorSession, TrackedRepo } from "@/types";

export default function DashboardOverview() {
  const [repos, setRepos] = useState<TrackedRepo[]>([]);
  const [sessions, setSessions] = useState<MentorSession[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([api.listRepos(), api.listSessions()])
      .then(([r, s]) => {
        setRepos(r);
        setSessions(s);
      })
      .catch(() => undefined)
      .finally(() => setLoading(false));
  }, []);

  const indexed = repos.filter((r) => r.index_status === "ready").length;

  return (
    <div>
      <PageHeader
        title="Overview"
        subtitle="Your open-source contribution workspace"
        action={
          <Link href="/dashboard/repos" className="btn-primary">
            Add a repository
          </Link>
        }
      />

      <div className="grid gap-4 p-6 sm:grid-cols-3">
        <Stat label="Tracked repositories" value={repos.length} />
        <Stat label="Indexed repositories" value={indexed} />
        <Stat label="Mentor sessions" value={sessions.length} />
      </div>

      <div className="grid gap-6 px-6 pb-10 lg:grid-cols-2">
        <section>
          <h2 className="mb-3 text-sm font-semibold uppercase tracking-wide text-slate-400">
            Recent repositories
          </h2>
          <div className="space-y-2">
            {loading && <p className="text-sm text-slate-500">Loading...</p>}
            {!loading && repos.length === 0 && (
              <EmptyState
                text="No repositories yet."
                href="/dashboard/repos"
                cta="Find a repository to contribute to"
              />
            )}
            {repos.slice(0, 5).map((r) => (
              <Link
                key={r.id}
                href={`/dashboard/repos/${r.id}`}
                className="card flex items-center justify-between hover:border-brand-600/50"
              >
                <span className="font-medium">
                  {r.owner}/{r.name}
                </span>
                <span className="text-xs text-slate-500">
                  ★ {r.stars.toLocaleString()}
                </span>
              </Link>
            ))}
          </div>
        </section>

        <section>
          <h2 className="mb-3 text-sm font-semibold uppercase tracking-wide text-slate-400">
            Recent sessions
          </h2>
          <div className="space-y-2">
            {!loading && sessions.length === 0 && (
              <EmptyState text="No mentor sessions yet." />
            )}
            {sessions.slice(0, 5).map((s) => (
              <div key={s.id} className="card">
                <p className="font-medium">{s.title}</p>
                <p className="text-xs text-slate-500">
                  {new Date(s.created_at).toLocaleString()}
                </p>
              </div>
            ))}
          </div>
        </section>
      </div>
    </div>
  );
}

function Stat({ label, value }: { label: string; value: number }) {
  return (
    <div className="card">
      <p className="text-3xl font-semibold text-slate-100">{value}</p>
      <p className="mt-1 text-sm text-slate-400">{label}</p>
    </div>
  );
}

function EmptyState({
  text,
  href,
  cta,
}: {
  text: string;
  href?: string;
  cta?: string;
}) {
  return (
    <div className="card text-sm text-slate-400">
      <p>{text}</p>
      {href && cta && (
        <Link href={href} className="mt-2 inline-block text-brand-400">
          {cta} →
        </Link>
      )}
    </div>
  );
}
