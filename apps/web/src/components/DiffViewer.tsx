// Renders a unified diff with simple line coloring.

export function DiffViewer({ diff }: { diff: string }) {
  if (!diff.trim()) {
    return (
      <p className="text-sm text-slate-500">No diff was produced.</p>
    );
  }
  const lines = diff.split("\n");
  return (
    <pre className="scrollbar-thin overflow-x-auto rounded-lg border border-surface-border bg-surface font-mono text-xs leading-relaxed">
      <code>
        {lines.map((line, i) => {
          let tone = "text-slate-300";
          if (line.startsWith("+") && !line.startsWith("+++"))
            tone = "bg-emerald-500/10 text-emerald-300";
          else if (line.startsWith("-") && !line.startsWith("---"))
            tone = "bg-red-500/10 text-red-300";
          else if (line.startsWith("@@")) tone = "text-brand-300";
          else if (line.startsWith("diff ") || line.startsWith("+++") || line.startsWith("---"))
            tone = "text-slate-500";
          return (
            <div key={i} className={`px-3 ${tone}`}>
              {line || " "}
            </div>
          );
        })}
      </code>
    </pre>
  );
}
