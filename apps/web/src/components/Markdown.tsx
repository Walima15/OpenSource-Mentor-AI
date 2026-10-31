import type { ReactNode } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";

function SafeLink({ href, children }: { href?: string; children?: ReactNode }) {
  if (!href || !/^https?:\/\//i.test(href)) {
    return <span>{children}</span>;
  }
  return (
    <a href={href} target="_blank" rel="noopener noreferrer">
      {children}
    </a>
  );
}

export function Markdown({ text }: { text: string }) {
  return (
    <div className="markdown">
      <ReactMarkdown
        remarkPlugins={[remarkGfm]}
        components={{
          a: ({ href, children }) => <SafeLink href={href}>{children}</SafeLink>,
        }}
      >
        {text}
      </ReactMarkdown>
    </div>
  );
}
