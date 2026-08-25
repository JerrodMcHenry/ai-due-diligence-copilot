"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useEffect, useState } from "react";
import { Show, UserButton } from "@clerk/nextjs";

import ThemeToggle from "@/components/ui/ThemeToggle";
import { getVersion } from "@/lib/api";

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
    name: "Analyze Startup",
    href: "/analyze",
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

  // Sidebar lives in the root layout, so this fetches once per app
  // session, not per navigation. Starts null (renders nothing rather than
  // a wrong/stale version) until the real value is confirmed from the
  // backend's single source of truth (app/ai/sie_v2_methodology.py, via
  // the existing /version endpoint) -- never falls back to a hardcoded
  // guess if the request fails.
  const [methodologyVersion, setMethodologyVersion] = useState<string | null>(
    null
  );

  useEffect(() => {
    let isMounted = true;

    getVersion()
      .then((data) => {
        if (isMounted) {
          setMethodologyVersion(data.methodology_version);
        }
      })
      .catch(() => {
        // Leave it unset rather than showing something false.
      });

    return () => {
      isMounted = false;
    };
  }, []);

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
        {/* SIE Authentication Phase 1: smallest placement consistent with
            the existing nav -- one row in the same footer area as the
            theme toggle. <Show> is Clerk's current control component
            (Core 3 removed <SignedIn>/<SignedOut> in favor of it -- see
            proxy.ts's comment for the same finding). Signed out gets a
            plain Link styled like a nav item (not Clerk's <SignInButton>)
            so it navigates to our own /sign-in page with the exact same
            styling as everything else here, nothing Clerk-hosted. Signed
            in gets Clerk's real <UserButton />, which includes sign-out. */}
        <Show when="signed-out">
          <Link
            href="/sign-in"
            onClick={onNavigate}
            className="flex min-h-11 items-center justify-center rounded-xl bg-primary px-4 py-3 text-sm font-semibold text-white transition-colors hover:bg-primary-hover focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary"
          >
            Sign In
          </Link>
        </Show>

        <Show when="signed-in">
          <div className="flex items-center gap-3 rounded-xl border border-border bg-surface px-4 py-3">
            <UserButton />
            <span className="text-sm font-medium text-sidebar-foreground">
              Account
            </span>
          </div>
        </Show>

        <ThemeToggle />

        <div className="rounded-xl border border-border bg-surface p-4">
          <p className="text-xs font-semibold text-text-primary">
            Startup Power Score™
          </p>

          {methodologyVersion ? (
            <p className="mt-1 text-xs text-text-muted">
              Methodology {methodologyVersion}
            </p>
          ) : null}
        </div>
      </div>
    </aside>
  );
}
