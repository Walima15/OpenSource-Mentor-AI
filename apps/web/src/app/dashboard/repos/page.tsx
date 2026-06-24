"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { PageHeader } from "@/components/PageHeader";
import { StatusBadge } from "@/components/StatusBadge";
import { api, ApiError } from "@/lib/api-client";
import { parseRepoInput } from "@/lib/github";
import type { RepoSearchResult, TrackedRepo } from "@/types";

export default function ReposPage() {
  const router = useRouter();
  const [tracked, setTracked] = useState<TrackedRepo[]>([]);
  const [query, setQuery] = useState("");
  const [results, setResults] = useState<RepoSearchResult[]>([]);
  const [searching, setSearching] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const refresh = () => api.listRepos().then(setTracked).catch(() => undefined);

  useEffect(() => {
    refresh();
  }, []);

  async function search(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    const direct = parseRepoInput(query);
    setSearching(true);
    try {
      if (direct) {
        const repo = await api.trackRepo(direct.owner, direct.name);
        await refresh();
        router.push(`/dashboard/repos/${repo.id}`);
        return;
      }
      setResults(await api.searchRepos(query));
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Search failed");
    } finally {
      setSearching(false);
    }
  }

  async function track(r: RepoSearchResult) {
    try {
      const repo = await api.trackRepo(r.owner, r.name);
      await refresh();
      router.push(`/dashboard/repos/${repo.id}`);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Could not track repo");
    }
  }

  return (
    <div>
      <PageHeader
        title="Repositories"
        subtitle="Search GitHub or paste an owner/name to start contributing"
      />

      <div className="p-6">
        <form onSubmit={search} className="flex gap-2">
          <input
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="e.g. vercel/next.js, language:python topic:cli, or a GitHub URL"
            className="input"
          />
          <button className="btn-primary" disabled={searching || !query.trim()}>
            {searching ? "Searching..." : "Search"}
          </button>
        </form>

        {error && (
          <p className="mt-3 rounded-lg bg-red-500/10 px-3 py-2 text-sm text-red-300">
            {error}
          </p>
        )}

        {results.length > 0 && (
          <section className="mt-6">
            <h2 className="mb-3 text-sm font-semibold uppercase tracking-wide text-slate-400">
              Search results
            </h2>
            <div className="grid gap-3 md:grid-cols-2">
              {results.map((r) => (
                <div key={r.full_name} className="card">
                  <div className="flex items-start justify-between gap-2">
                    <div>
                      <p className="font-medium text-slate-100">{r.full_name}</p>
                      <p className="mt-1 line-clamp-2 text-sm text-slate-400">
                        {r.description ?? "No description"}
                      </p>
                    </div>
                  </div>
                  <div className="mt-3 flex items-center justify-between">
                    <div className="flex items-center gap-3 text-xs text-slate-500">
                      <span>★ {r.stars.toLocaleString()}</span>
                      {r.language && <span>{r.language}</span>}
                    </div>
                    <button onClick={() => track(r)} className="btn-secondary">
                      Track
                    </button>
                  </div>
                </div>
              ))}
            </div>
          </section>
        )}

        <section className="mt-8">
          <h2 className="mb-3 text-sm font-semibold uppercase tracking-wide text-slate-400">
            Tracked repositories
          </h2>
          {tracked.length === 0 ? (
            <p className="text-sm text-slate-500">
              You are not tracking any repositories yet.
            </p>
          ) : (
            <div className="grid gap-3 md:grid-cols-2">
              {tracked.map((r) => (
                <Link
                  key={r.id}
                  href={`/dashboard/repos/${r.id}`}
                  className="card hover:border-brand-600/50"
                >
                  <div className="flex items-center justify-between">
                    <p className="font-medium text-slate-100">
                      {r.owner}/{r.name}
                    </p>
                    <StatusBadge status={r.index_status} />
                  </div>
                  <p className="mt-1 line-clamp-2 text-sm text-slate-400">
                    {r.description ?? "No description"}
                  </p>
                  <p className="mt-3 text-xs text-slate-500">
                    ★ {r.stars.toLocaleString()}
                  </p>
                </Link>
              ))}
            </div>
          )}
        </section>
      </div>
    </div>
  );
}
