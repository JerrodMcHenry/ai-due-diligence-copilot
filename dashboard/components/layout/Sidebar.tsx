"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

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
    <aside className="flex h-full w-72 flex-col border-r border-slate-800 bg-slate-950">
      <div className="flex h-20 items-center border-b border-slate-800 px-6">
        <Link
          href="/"
          onClick={onNavigate}
          className="group flex items-center gap-3"
        >
          <div className="flex size-9 items-center justify-center rounded-lg bg-blue-600 text-sm font-bold text-white shadow-sm shadow-blue-950">
            SI
          </div>

          <div className="min-w-0">
            <p className="truncate text-sm font-semibold text-white">
              Startup Intelligence
            </p>

            <p className="text-xs text-slate-500">Intelligence Platform</p>
          </div>
        </Link>
      </div>

      <nav
        aria-label="Main navigation"
        className="flex-1 space-y-1 overflow-y-auto px-4 py-6"
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
                "flex min-h-11 items-center rounded-lg px-3 text-sm font-medium transition-colors",
                "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-500",
                active
                  ? "bg-blue-600/15 text-blue-300"
                  : "text-slate-400 hover:bg-slate-900 hover:text-white",
              ].join(" ")}
            >
              {item.name}
            </Link>
          );
        })}
      </nav>

      <div className="border-t border-slate-800 px-6 py-5">
        <p className="text-xs font-medium text-slate-500">SIE Methodology v1</p>
      </div>
    </aside>
  );
}
