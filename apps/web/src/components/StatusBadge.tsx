import type { IndexStatus } from "@/types";

const STYLES: Record<IndexStatus, string> = {
  pending: "bg-slate-500/15 text-slate-300",
  indexing: "bg-amber-500/15 text-amber-300",
  ready: "bg-emerald-500/15 text-emerald-300",
  failed: "bg-red-500/15 text-red-300",
};

const LABELS: Record<IndexStatus, string> = {
  pending: "Not indexed",
  indexing: "Indexing...",
  ready: "Indexed",
  failed: "Index failed",
};

export function StatusBadge({ status }: { status: IndexStatus }) {
  return <span className={`badge ${STYLES[status]}`}>{LABELS[status]}</span>;
}

export function LabelChip({ label }: { label: string }) {
  const lower = label.toLowerCase();
  const tone =
    lower.includes("good first")
      ? "bg-emerald-500/15 text-emerald-300"
      : lower.includes("help wanted")
        ? "bg-brand-500/15 text-brand-300"
        : "bg-surface-muted text-slate-300";
  return <span className={`badge ${tone}`}>{label}</span>;
}
