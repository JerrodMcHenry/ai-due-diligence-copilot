"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

import ThemeToggle from "@/components/ui/ThemeToggle";

type NavigationItem = {
  name: string;
  href: string;
};

type SidebarProps = {
  onNavigate?: () => void;
};

const navigation: NavigationItem[] = [
  {
    name: "Dashboard",
    href: "/",
  },
  {
    name: "Rankings",
    href: "/rankings",
  },
  {
    name: "Search",
    href: "/search",
  },
];

function isActiveRoute(pathname: string, href: string) {
  if (href === "/") {
    return pathname === "/";
  }

  return pathname === href || pathname.startsWith(`${href}/`);
}

export default function Sidebar({ onNavigate }: SidebarProps) {
  const pathname = usePathname();

  return (
    <aside className="flex h-full w-72 flex-col border-r border-border bg-sidebar">
      <div className="border-b border-border px-6 py-6">
        <Link
          href="/"
          onClick={onNavigate}
          className="flex items-center gap-4 rounded-xl focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary"
        >
          <div className="flex size-11 shrink-0 items-center justify-center rounded-2xl bg-primary font-bold text-white shadow-lg">
            SI
          </div>

          <div className="min-w-0">
            <p className="truncate text-sm font-semibold text-sidebar-foreground">
              Startup Intelligence
            </p>

            <p className="text-xs text-sidebar-muted">Powered by SPS™</p>
          </div>
        </Link>
      </div>

      <nav
        aria-label="Main navigation"
        className="flex-1 space-y-2 overflow-y-auto px-4 py-6"
      >
        {navigation.map((item) => {
          const active = isActiveRoute(pathname, item.href);

          return (
            <Link
              key={item.href}
              href={item.href}
              onClick={onNavigate}
              aria-current={active ? "page" : undefined}
              className={[
                "flex min-h-11 items-center rounded-xl px-4 py-3 text-sm font-medium transition-all duration-200",
                "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary",
                active
                  ? "bg-sidebar-active text-primary shadow-sm"
                  : "text-sidebar-muted hover:bg-sidebar-hover hover:text-sidebar-foreground",
              ].join(" ")}
            >
              {item.name}
            </Link>
          );
        })}
      </nav>

      <div className="space-y-4 border-t border-border p-6">
        <ThemeToggle />

        <div className="rounded-xl border border-border bg-surface p-4">
          <p className="text-xs font-semibold text-text-primary">
            Startup Power Score™
          </p>

          <p className="mt-1 text-xs text-text-muted">
            Intelligence Methodology v1
          </p>
        </div>
      </div>
    </aside>
  );
}
