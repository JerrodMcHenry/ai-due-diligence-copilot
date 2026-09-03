"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

import { PRIMARY_NAVIGATION, isPrimaryDestinationActive } from "./TopNav";

// Phase 10.3 -- Shell & Navigation Reset, Part 5. A purpose-built mobile
// primary navigation -- the SAME destinations as the desktop top nav
// (single source of truth, imported from TopNav.tsx, so the two surfaces
// can never disagree about what "Build/Analyze/Learn" means or which
// routes count as active), presented as a native-feeling bottom tab bar
// instead of a hamburger drawer replicating every route. Account/
// personal navigation deliberately stays in the header (PersonalMenu),
// not duplicated here -- Part 5: "Account/personal functionality can
// remain accessible from the top/header account affordance."
//
// Hidden at the md breakpoint and up -- desktop uses TopNav's own
// horizontal nav instead (see AppShell.tsx for the matching content
// bottom-padding that keeps this bar from covering page content on
// mobile).
const TAB_ICONS: Record<string, React.ReactNode> = {
  // Founder Experience Model correction, Part 2: "Learn" replaces the
  // stale, no-longer-referenced "Explore" icon entry (Phase 15 already
  // removed "Explore" from PRIMARY_NAVIGATION itself; this map simply
  // hadn't been cleaned up since).
  Learn: (
    <svg aria-hidden="true" viewBox="0 0 24 24" fill="none" className="size-5">
      <path
        d="M4 5.5A2.5 2.5 0 0 1 6.5 3H12v16H6.5A2.5 2.5 0 0 0 4 21.5v-16z"
        stroke="currentColor"
        strokeWidth="1.6"
        strokeLinejoin="round"
      />
      <path
        d="M20 5.5A2.5 2.5 0 0 0 17.5 3H12v16h5.5a2.5 2.5 0 0 1 2.5 2.5v-16z"
        stroke="currentColor"
        strokeWidth="1.6"
        strokeLinejoin="round"
      />
    </svg>
  ),
  Build: (
    <svg aria-hidden="true" viewBox="0 0 24 24" fill="none" className="size-5">
      <path
        d="M12 3l2.4 5.3 5.6.6-4.2 3.9 1.2 5.6L12 15.8l-5 2.6 1.2-5.6-4.2-3.9 5.6-.6L12 3z"
        stroke="currentColor"
        strokeWidth="1.6"
        strokeLinejoin="round"
      />
    </svg>
  ),
  Analyze: (
    <svg aria-hidden="true" viewBox="0 0 24 24" fill="none" className="size-5">
      <path d="M12 3v4M12 17v4M3 12h4M17 12h4" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" />
      <circle cx="12" cy="12" r="4.5" stroke="currentColor" strokeWidth="1.8" />
    </svg>
  ),
};

export default function MobileTabBar() {
  const pathname = usePathname();

  return (
    <nav
      aria-label="Primary"
      className="fixed inset-x-0 bottom-0 z-40 border-t border-border bg-surface/95 backdrop-blur supports-[backdrop-filter]:bg-surface/80 md:hidden"
      style={{ paddingBottom: "env(safe-area-inset-bottom)" }}
    >
      <div className="mx-auto flex max-w-[1600px] items-stretch justify-around px-2">
        {PRIMARY_NAVIGATION.map((item) => {
          const active = isPrimaryDestinationActive(pathname, item);

          return (
            <Link
              key={item.href}
              href={item.href}
              aria-current={active ? "page" : undefined}
              className={[
                "flex min-h-14 flex-1 flex-col items-center justify-center gap-0.5 rounded-xl py-1.5 text-xs font-semibold transition-colors",
                "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary focus-visible:ring-inset",
                active ? "text-primary" : "text-text-muted",
              ].join(" ")}
            >
              {TAB_ICONS[item.name]}
              {item.name}
            </Link>
          );
        })}
      </div>
    </nav>
  );
}
