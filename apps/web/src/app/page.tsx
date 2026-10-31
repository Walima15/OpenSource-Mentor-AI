import Link from "next/link";

const steps = [
  {
    title: "Learn the protocol",
    text: "UTXOs, transactions, scripts, blocks, consensus, the peer-to-peer network, the mempool, BIPs, and Lightning. Each lesson ends in a quiz.",
    href: "/learn",
  },
  {
    title: "Learn the culture",
    text: "ACK and NACK, review club, tests, signed commits, pull request etiquette, mailing lists, and IRC. The mentor will not ACK a patch for you.",
    href: "/learn/contribution-craft",
  },
  {
    title: "Practice on a real repo",
    text: "Bitcoin Core, BDK, LDK, rust-bitcoin, LND, Core Lightning, BTCPay Server, and the BOLTs, with setup notes and live good-first issues.",
    href: "/projects",
  },
];

export default function HomePage() {
  return (
    <main className="mx-auto max-w-6xl px-4 py-14">
      <p className="text-sm uppercase tracking-[0.18em] text-rust">Bitcoin open source</p>
      <h1 className="mt-3 max-w-3xl font-serif text-5xl leading-[1.05] tracking-tight sm:text-6xl">
        A mentor for the work, not a machine that opens pull requests.
      </h1>
      <p className="mt-5 max-w-2xl text-lg text-muted">
        OSMA teaches you how to contribute to Bitcoin projects: the protocol, the review culture, how to build the
        code, and how to read a diff. You still write the patch and show up for review.
      </p>
      <div className="mt-8 flex flex-wrap gap-3">
        <Link href="/chat" className="rounded-full bg-ink px-5 py-2.5 text-sm text-paper">
          Start a session
        </Link>
        <Link href="/learn" className="rounded-full border border-line bg-card px-5 py-2.5 text-sm">
          Browse the curriculum
        </Link>
      </div>
      <div className="mt-14 grid gap-4 md:grid-cols-3">
        {steps.map((step) => (
          <Link key={step.title} href={step.href} className="rounded-2xl border border-line bg-card p-5 shadow-card">
            <h2 className="font-serif text-2xl">{step.title}</h2>
            <p className="mt-2 text-sm leading-6 text-muted">{step.text}</p>
          </Link>
        ))}
      </div>
    </main>
  );
}
