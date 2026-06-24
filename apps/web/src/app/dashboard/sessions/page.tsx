"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { PageHeader } from "@/components/PageHeader";
import { api } from "@/lib/api-client";
import type { MentorSession } from "@/types";

export default function SessionsPage() {
  const [sessions, setSessions] = useState<MentorSession[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api
      .listSessions()
      .then(setSessions)
      .catch(() => undefined)
      .finally(() => setLoading(false));
  }, []);

  return (
    <div>
      <PageHeader
        title="Mentor sessions"
        subtitle="Your previous and ongoing contribution sessions"
      />
      <div className="p-6">
        {loading && <p className="text-sm text-slate-500">Loading...</p>}
        {!loading && sessions.length === 0 && (
          <p className="text-sm text-slate-500">
            No sessions yet. Start one from a repository&apos;s issues tab.
          </p>
        )}
        <div className="space-y-3">
          {sessions.map((s) => (
            <Link
              key={s.id}
              href={`/dashboard/repos/${s.repo_id}/sessions/${s.id}`}
              className="card flex items-center justify-between hover:border-brand-600/50"
            >
              <div>
                <p className="font-medium text-slate-100">{s.title}</p>
                {s.issue_number && (
                  <p className="text-xs text-slate-500">
                    Issue #{s.issue_number}
                  </p>
                )}
              </div>
              <span className="text-xs text-slate-500">
                {new Date(s.created_at).toLocaleDateString()}
              </span>
            </Link>
          ))}
        </div>
      </div>
    </div>
  );
}
