"use client";

import { Suspense } from "react";
import { useSearchParams } from "next/navigation";

function GitHubTokenNoticeInner() {
  const params = useSearchParams();
  if (params.get("error") !== "github_token") return null;
  return (
    <p className="mx-6 mt-4 rounded-lg bg-red-500/10 px-3 py-2 text-sm text-red-300">
      GitHub access could not be saved. Sign in with GitHub again before
      indexing repositories or opening pull requests.
    </p>
  );
}

export function GitHubTokenNotice() {
  return (
    <Suspense fallback={null}>
      <GitHubTokenNoticeInner />
    </Suspense>
  );
}
