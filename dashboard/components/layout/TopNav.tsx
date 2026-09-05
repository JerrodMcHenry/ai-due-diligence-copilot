"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { Show } from "@clerk/nextjs";

import PersonalMenu from "./PersonalMenu";
import ThemeToggle from "@/components/ui/ThemeToggle";

// Phase 10.3 -- Shell & Navigation Reset. The universal primary
// navigation started as exactly three consumer-facing destinations --
// see the Phase 10.2 audit's own "That is the product" framing. Phase 15
// -- Founder Beta Surface Audit removed "Explore" (see PRIMARY_NAVIGATION's
// own comment below for why), leaving two; the Founder Experience Model
// correction added "Learn" back as the third (a genuinely global product
// mode, not an account-specific destination -- see that entry's own
// comment). Do NOT add another top-level item here without a real
// product decision; personal/account-specific destinations (My Ideas, My
// Startup) live in PersonalMenu instead, never here. Fundraising and
// Simulate/Model-What-If are explicitly EXCLUDED from this list --
// founder tools reachable from inside a venture's workspace, never
// promoted to the global switcher (Founder Experience Model correction,
// Part 2's own explicit instruction).
type PrimaryDestination = {
  name: string;
  href: string;
  // Which route prefixes count as "this section is active" -- broader
  // than an exact match, since e.g. Explore conceptually covers
  // /rankings, /search, /startup/*, and /compare (Part 4: "strong
  // active-route state"), not just its own primary href. Checked with
  // startsWith, so a trailing "/" isn't required for single-segment
  // prefixes like "/analyze".
  activeOn: string[];
};

// Phase 15 -- Founder Beta Surface Audit, Part 6/21: "Explore" removed
// from primary navigation. Not a deletion -- /rankings, /search,
// /compare, /startup/[id] remain fully functional at their existing
// URLs (Part 16/17's "hide, don't delete" principle) and
// isPrimaryDestinationActive below is untouched, so nothing about how a
// destination becomes "active" changed. This is a visibility decision
// only, backed by a verified, concrete finding: the live discovery
// dataset (GET /rankings, GET /discover, GET /top-startups) currently
// returns exactly one row, and that row's own company_name is "Unknown"
// -- a co-equal, always-visible 1-of-3 primary nav slot pointing at that
// experience actively damages Founder Beta credibility (Part 22/23's
// "empty product surface" test). Revert this the moment the discovery
// dataset is credible again -- see docs/validation/
// SPS_V3_ADAPTER_HARDENING.md's sibling doc for this phase's own report
// and the deferred Intelligence Dataset Strategy recommendation.
//
// "Analyze" is NOT part of this cold-start problem -- POST /analyze
// evaluates exactly the one company a founder describes, using the same
// complete, frozen SPS pipeline regardless of how many OTHER companies
// exist in the database, so it stays a primary destination.
// Founder Experience Model correction, Part 2. "Learn" added as the
// third primary destination -- Part 5's own instruction that Learn is a
// GLOBAL product mode, not just a founder-tool link buried inside one
// venture's workspace. Routes into the exact same /playbooks experience
// PersonalMenu's own "Learn" entry and every contextual "Learn how ->"
// link across the app already point into -- no second Learn
// implementation, just a more visible entry point to the one that
// exists. Deliberately does NOT add Fundraising or Simulate here (the
// directive's own explicit instruction) -- those stay founder tools
// reachable from inside a venture's workspace ("Explore"), never
// promoted to the global switcher a signed-out visitor or a founder with
// no venture yet would also see.
// Phase 31C -- Founder Experience Simplification, Part 3: evaluated
// adding a fourth "Test" destination (Build | Test | Analyze | Learn,
// for "test assumptions, run experiments, capture evidence") and
// deliberately did NOT add one. Investigation found no real, single
// cross-venture "test" destination to point it at -- What-If and Capture
// are both scoped to ONE venture's own workspace (a founder with several
// ventures has per-venture testing tools, not a shared test hub), so a
// global nav item here would either duplicate a venture's own workspace
// or require building a genuinely new cross-venture aggregation page --
// the exact kind of new surface Part 13 explicitly prohibits ("prefer
// deletion and simplification over adding components"). The JOB itself
// (test an assumption, capture what happened) is real and is served --
// inside the venture workspace, where What If and Capture already live,
// with "What If" itself renamed off internal terminology (see
// VentureWorkspace.tsx's own Tabs comment) to match this same plain-
// language principle. Revisit this decision only if a real, single,
// cross-venture "test" surface is ever built for its own reasons -- never
// add the nav label first and grow a page to justify it.
export const PRIMARY_NAVIGATION: PrimaryDestination[] = [
  { name: "Build", href: "/idea-lab", activeOn: ["/idea-lab"] },
  { name: "Analyze", href: "/analyze", activeOn: ["/analyze"] },
  { name: "Learn", href: "/playbooks", activeOn: ["/playbooks"] },
];

export function isPrimaryDestinationActive(pathname: string, destination: PrimaryDestination): boolean {
  return destination.activeOn.some(
    (prefix) => pathname === prefix || pathname.startsWith(`${prefix}/`)
  );
}

export default function TopNav() {
  const pathname = usePathname();

  return (
    <header className="sticky top-0 z-40 border-b border-border bg-surface/95 backdrop-blur supports-[backdrop-filter]:bg-surface/80">
      <div className="mx-auto flex h-16 w-full max-w-[1600px] items-center justify-between gap-4 px-4 sm:px-6 lg:px-10">
        {/* Logo/home affordance -- Part 2: "The logo/brand should link to
            /. Do not redesign / content yet." Deliberately the ONLY way
            to reach / from the shell -- Home is not one of the three
            primary destinations. */}
        <Link
          href="/"
          className="flex shrink-0 items-center gap-2.5 rounded-xl focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary"
          aria-label="SIE home"
        >
          <span className="flex size-9 items-center justify-center rounded-xl bg-primary text-sm font-bold text-white shadow-sm">
            SI
          </span>
          <span className="hidden text-sm font-semibold text-text-primary sm:inline">
            Startup Intelligence
          </span>
        </Link>

        {/* Desktop primary navigation. Hidden on mobile -- the same three
            destinations reappear as the bottom tab bar (MobileTabBar),
            never squeezed in here (Part 5: "No horizontally squeezed
            desktop nav"). */}
        <nav
          aria-label="Primary"
          className="hidden items-center gap-1 rounded-full border border-border bg-surface-muted p-1 md:flex"
        >
          {PRIMARY_NAVIGATION.map((item) => {
            const active = isPrimaryDestinationActive(pathname, item);

            return (
              <Link
                key={item.href}
                href={item.href}
                aria-current={active ? "page" : undefined}
                className={[
                  "rounded-full px-4 py-2 text-sm font-semibold transition-colors",
                  "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary",
                  active
                    ? "bg-primary text-white shadow-sm"
                    : "text-text-secondary hover:bg-surface hover:text-text-primary",
                ].join(" ")}
              >
                {item.name}
              </Link>
            );
          })}
        </nav>

        <div className="flex shrink-0 items-center gap-3">
          {/* Phase 10.3 follow-up: the old Sidebar rendered ThemeToggle
              unconditionally (regardless of sign-in state), so signed-out
              visitors could switch themes. That parity broke when
              ThemeToggle briefly lived only inside PersonalMenu (signed-in
              only) -- restored here in the header itself, visible to
              everyone, so it isn't lost for signed-out visitors again. */}
          <ThemeToggle />

          <Show when="signed-out">
            <Link
              href="/sign-in"
              className="rounded-full bg-primary px-4 py-2 text-sm font-semibold text-white transition-colors hover:bg-primary-hover focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary"
            >
              Sign In
            </Link>
          </Show>

          <Show when="signed-in">
            <PersonalMenu />
          </Show>
        </div>
      </div>
    </header>
  );
}
