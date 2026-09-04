"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

const NAV_LINKS = [
  { href: "/dashboard", label: "Dashboard" },
  { href: "/missions/new", label: "New Mission" },
  { href: "/alerts", label: "Alerts" },
] as const;

export default function Navbar() {
  const pathname = usePathname();

  // A nested route keeps its section highlighted, so /missions/new/step-2
  // still marks "New Mission" as active.
  const isActive = (href: string) =>
    pathname === href || pathname.startsWith(`${href}/`);

  return (
    <nav className="bg-gray-900 border-b border-gray-800">
      <div className="mx-auto flex h-14 max-w-7xl items-center gap-8 px-4">
        <Link
          href="/dashboard"
          className="flex items-center gap-2 text-lg font-semibold tracking-tight text-white"
        >
          <span aria-hidden className="text-sky-400">
            ◆
          </span>
          AeroMind
        </Link>

        <div className="flex items-center gap-1">
          {NAV_LINKS.map((link) => {
            const active = isActive(link.href);
            return (
              <Link
                key={link.href}
                href={link.href}
                aria-current={active ? "page" : undefined}
                className={`rounded-md px-3 py-1.5 text-sm transition-colors ${
                  active
                    ? "bg-gray-800 font-medium text-white"
                    : "text-gray-400 hover:bg-gray-800/60 hover:text-gray-100"
                }`}
              >
                {link.label}
              </Link>
            );
          })}
        </div>
      </div>
    </nav>
  );
}
