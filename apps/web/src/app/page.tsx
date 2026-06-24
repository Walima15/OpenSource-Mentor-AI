import Link from "next/link";

const FEATURES = [
  {
    title: "Find good first issues",
    body: "Discover beginner-friendly issues labeled 'good first issue' and 'help wanted' across any repository.",
  },
  {
    title: "Understand any codebase",
    body: "The AI mentor analyzes architecture and explains how a project is organized in plain language.",
  },
  {
    title: "Get guided contributions",
    body: "Receive an implementation plan, file recommendations, code suggestions, and tests.",
  },
  {
    title: "Ship pull requests",
    body: "Generate commit messages, PR descriptions, and change summaries ready to submit.",
  },
];

export default function LandingPage() {
  return (
    <main className="min-h-screen">
      <header className="mx-auto flex max-w-6xl items-center justify-between px-6 py-6">
        <span className="text-lg font-semibold">
          OpenSource <span className="text-brand-400">Mentor AI</span>
        </span>
        <Link href="/login" className="btn-primary">
          Sign in with GitHub
        </Link>
      </header>

      <section className="mx-auto max-w-4xl px-6 pb-16 pt-12 text-center">
        <span className="badge bg-brand-500/10 text-brand-300">
          Your AI pair-mentor for open source
        </span>
        <h1 className="mt-6 text-4xl font-bold tracking-tight sm:text-5xl">
          Contribute to open source
          <span className="block text-brand-400">with confidence.</span>
        </h1>
        <p className="mx-auto mt-6 max-w-2xl text-lg text-slate-400">
          OpenSource Mentor AI guides you from finding an issue to opening a pull
          request: it explains the codebase, plans your work, suggests code and
          tests, and drafts your PR.
        </p>
        <div className="mt-8 flex justify-center gap-3">
          <Link href="/login" className="btn-primary px-6 py-3 text-base">
            Get started
          </Link>
          <a
            href="https://github.com"
            className="btn-secondary px-6 py-3 text-base"
          >
            Learn more
          </a>
        </div>
      </section>

      <section className="mx-auto grid max-w-5xl gap-4 px-6 pb-24 sm:grid-cols-2">
        {FEATURES.map((f) => (
          <div key={f.title} className="card">
            <h3 className="text-lg font-semibold text-slate-100">{f.title}</h3>
            <p className="mt-2 text-sm text-slate-400">{f.body}</p>
          </div>
        ))}
      </section>
    </main>
  );
}
