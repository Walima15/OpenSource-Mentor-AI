import Link from "next/link";

const links = [
  { href: "/learn", label: "Learn" },
  { href: "/projects", label: "Projects" },
  { href: "/chat", label: "Mentor" },
];

export function Nav() {
  return (
    <header className="border-b border-line/80 bg-paper/80 backdrop-blur">
      <div className="mx-auto flex max-w-6xl items-center justify-between gap-4 px-4 py-3">
        <Link href="/" className="group flex items-baseline gap-2">
          <span className="font-serif text-xl tracking-tight text-ink">OSMA</span>
          <span className="hidden text-sm text-muted sm:inline">Open Source Mentor</span>
        </Link>
        <nav className="flex items-center gap-1 text-sm">
          {links.map((link) => (
            <Link
              key={link.href}
              href={link.href}
              className="rounded-full px-3 py-1.5 text-ink hover:bg-card"
            >
              {link.label}
            </Link>
          ))}
        </nav>
      </div>
    </header>
  );
}
