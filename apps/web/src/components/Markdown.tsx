import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import rehypeHighlight from "rehype-highlight";
import "highlight.js/styles/github-dark.css";

// Rich markdown renderer with GitHub-flavored markdown + syntax highlighting.
export function Markdown({ content }: { content: string }) {
  return (
    <div className="osma-prose text-sm leading-relaxed text-slate-300">
      <ReactMarkdown
        remarkPlugins={[remarkGfm]}
        rehypePlugins={[rehypeHighlight]}
        components={{
          h1: ({ children }) => (
            <h1 className="mb-2 mt-3 text-lg font-semibold text-slate-100">
              {children}
            </h1>
          ),
          h2: ({ children }) => (
            <h2 className="mb-2 mt-3 text-base font-semibold text-slate-100">
              {children}
            </h2>
          ),
          h3: ({ children }) => (
            <h3 className="mb-1 mt-2 text-sm font-semibold text-slate-100">
              {children}
            </h3>
          ),
          p: ({ children }) => <p className="mb-2">{children}</p>,
          a: ({ children, href }) => (
            <a
              href={href}
              target="_blank"
              rel="noreferrer"
              className="text-brand-300 underline hover:text-brand-200"
            >
              {children}
            </a>
          ),
          ul: ({ children }) => (
            <ul className="mb-2 ml-4 list-disc space-y-1">{children}</ul>
          ),
          ol: ({ children }) => (
            <ol className="mb-2 ml-4 list-decimal space-y-1">{children}</ol>
          ),
          strong: ({ children }) => (
            <strong className="font-semibold text-slate-100">{children}</strong>
          ),
          code: ({ className, children }) => {
            const isBlock = (className ?? "").includes("language-");
            if (isBlock) {
              return <code className={className}>{children}</code>;
            }
            return (
              <code className="rounded bg-surface-muted px-1 py-0.5 font-mono text-[0.85em] text-brand-200">
                {children}
              </code>
            );
          },
          pre: ({ children }) => (
            <pre className="scrollbar-thin mb-3 overflow-x-auto rounded-lg border border-surface-border bg-surface p-3 font-mono text-xs">
              {children}
            </pre>
          ),
          table: ({ children }) => (
            <div className="mb-3 overflow-x-auto">
              <table className="w-full border-collapse text-xs">{children}</table>
            </div>
          ),
          th: ({ children }) => (
            <th className="border border-surface-border bg-surface-muted px-2 py-1 text-left">
              {children}
            </th>
          ),
          td: ({ children }) => (
            <td className="border border-surface-border px-2 py-1">{children}</td>
          ),
          blockquote: ({ children }) => (
            <blockquote className="mb-2 border-l-2 border-brand-500/50 pl-3 text-slate-400">
              {children}
            </blockquote>
          ),
        }}
      >
        {content}
      </ReactMarkdown>
    </div>
  );
}
