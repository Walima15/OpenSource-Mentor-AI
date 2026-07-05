"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useState } from "react";
import { createClient } from "@/lib/supabase/client";
import { useRouter } from "next/navigation";

const NAV = [
  { href: "/dashboard", label: "Overview", icon: "M3 12l9-9 9 9M5 10v10h14V10" },
  { href: "/dashboard/repos", label: "Repositories", icon: "M4 4h16v16H4z M4 9h16" },
  { href: "/dashboard/recommendations", label: "Recommendations", icon: "M12 3l2.5 5.5L20 9l-4 4 1 6-5-3-5 3 1-6-4-4 5.5-.5z" },
  { href: "/dashboard/sessions", label: "Mentor sessions", icon: "M4 5h16v10H7l-3 3z" },
  { href: "/dashboard/profile", label: "Profile", icon: "M12 12a4 4 0 100-8 4 4 0 000 8z M4 20a8 8 0 0116 0" },
];

export function Sidebar() {
  const pathname = usePathname();
  const router = useRouter();
  const [collapsed, setCollapsed] = useState(false);

  async function signOut() {
    const supabase = createClient();
    await supabase.auth.signOut();
    router.push("/login");
  }

  return (
    <aside
      className={`flex shrink-0 flex-col border-r border-surface-border bg-surface-card transition-all ${
        collapsed ? "w-16" : "w-60"
      }`}
    >
      <div className="flex items-center justify-between px-4 py-5">
        {!collapsed && (
          <Link href="/dashboard" className="font-semibold">
            OSMA<span className="text-brand-400"> AI</span>
          </Link>
        )}
        <button
          onClick={() => setCollapsed((c) => !c)}
          className="btn-ghost px-2 py-1"
          aria-label="Toggle sidebar"
        >
          {collapsed ? "›" : "‹"}
        </button>
      </div>

      <nav className="flex-1 space-y-1 px-2">
        {NAV.map((item) => {
          const active =
            item.href === "/dashboard"
              ? pathname === "/dashboard"
              : pathname.startsWith(item.href);
          return (
            <Link
              key={item.href}
              href={item.href}
              className={`flex items-center gap-3 rounded-lg px-3 py-2 text-sm transition-colors ${
                active
                  ? "bg-brand-600/15 text-brand-200"
                  : "text-slate-400 hover:bg-surface-muted hover:text-slate-200"
              }`}
            >
              <svg
                width="18"
                height="18"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                strokeWidth="1.7"
                strokeLinecap="round"
                strokeLinejoin="round"
              >
                <path d={item.icon} />
              </svg>
              {!collapsed && item.label}
            </Link>
          );
        })}
      </nav>

      <button
        onClick={signOut}
        className="m-2 flex items-center gap-3 rounded-lg px-3 py-2 text-sm text-slate-400 hover:bg-surface-muted hover:text-slate-200"
      >
        <svg
          width="18"
          height="18"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          strokeWidth="1.7"
          strokeLinecap="round"
          strokeLinejoin="round"
        >
          <path d="M16 17l5-5-5-5M21 12H9M9 21H5a2 2 0 01-2-2V5a2 2 0 012-2h4" />
        </svg>
        {!collapsed && "Sign out"}
      </button>
    </aside>
  );
}
