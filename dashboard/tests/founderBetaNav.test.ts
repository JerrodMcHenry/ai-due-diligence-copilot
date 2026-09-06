// Phase 15 -- Founder Beta Surface Audit tests.
//
// Same hand-rolled expect()/PASS-FAIL/main() convention as
// tests/playbooks.test.ts and tests/journey.test.ts (this repo has no
// jest/vitest). TopNav.tsx and PersonalMenu.tsx are "use client"
// components that import next/link, next/navigation, and @clerk/nextjs --
// none of which plain node can resolve outside Next's own build -- so
// this file reads them as source text (the same cross-boundary technique
// the other two test files' own firewall tests already use) rather than
// importing them.
//
// Run with:
//   node tests/founderBetaNav.test.ts
// or:
//   npm run test:founderBetaNav
import { existsSync, readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import path from "node:path";

function expect(condition: boolean, message: string): void {
  if (!condition) {
    throw new Error(message);
  }
}

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const DASHBOARD_ROOT = path.resolve(__dirname, "..");

function readSource(relativePath: string): string {
  return readFileSync(path.join(DASHBOARD_ROOT, relativePath), "utf-8");
}

// --- Primary navigation (TopNav.tsx / MobileTabBar.tsx share PRIMARY_NAVIGATION) ---

function test_explore_removed_from_primary_navigation(): void {
  const source = readSource("components/layout/TopNav.tsx");
  const arrayStart = source.indexOf("export const PRIMARY_NAVIGATION");
  expect(arrayStart !== -1, "PRIMARY_NAVIGATION export not found -- has TopNav.tsx been restructured?");

  const arrayEnd = source.indexOf("];", arrayStart);
  const arrayText = source.slice(arrayStart, arrayEnd);

  expect(
    !/name:\s*"Explore"/.test(arrayText),
    "Phase 15: \"Explore\" must not be a primary navigation destination -- the live discovery dataset is not credible enough for Founder Beta (see this phase's own report)"
  );
  expect(/name:\s*"Build"/.test(arrayText), "\"Build\" (Idea Lab) must remain a primary destination");
  expect(/name:\s*"Analyze"/.test(arrayText), "\"Analyze\" must remain a primary destination -- it has no cold-start dependency");
}

// Founder Experience Model correction, Part 2. The global primary
// switcher is Build | Analyze | Learn -- Learn promoted from an
// account-menu-only link to a genuinely global product mode, per that
// phase's own explicit instruction. Fundraising/Simulate must never
// appear here (they stay founder tools inside a venture's workspace).
function test_global_nav_is_build_analyze_learn(): void {
  const source = readSource("components/layout/TopNav.tsx");
  const arrayStart = source.indexOf("export const PRIMARY_NAVIGATION");
  const arrayEnd = source.indexOf("];", arrayStart);
  const arrayText = source.slice(arrayStart, arrayEnd);

  expect(/name:\s*"Build"/.test(arrayText), "\"Build\" must remain a primary destination");
  expect(/name:\s*"Analyze"/.test(arrayText), "\"Analyze\" must remain a primary destination");
  expect(/name:\s*"Learn"/.test(arrayText), "\"Learn\" must be a primary destination -- Founder Experience Model correction, Part 2");
  expect(/href:\s*"\/playbooks"/.test(arrayText), "\"Learn\" must route into the existing /playbooks experience, not a new one");
  expect(!/name:\s*"Fundraising"/.test(arrayText), "\"Fundraising\" must never be a global primary destination -- it stays a founder tool inside the venture workspace");
  expect(!/name:\s*"Simulate"/.test(arrayText), "\"Simulate\" must never be a global primary destination -- it stays a founder tool inside the venture workspace");
}

function test_mobile_tab_bar_shares_the_same_primary_navigation_source(): void {
  // MobileTabBar must import PRIMARY_NAVIGATION from TopNav rather than
  // defining its own list -- otherwise a desktop nav change (like this
  // phase's own Explore removal) could silently fail to apply on mobile
  // (Part 32's explicit concern).
  const source = readSource("components/layout/MobileTabBar.tsx");
  expect(
    /import\s*\{[^}]*PRIMARY_NAVIGATION[^}]*\}\s*from\s*"\.\/TopNav"/.test(source),
    "MobileTabBar must import PRIMARY_NAVIGATION from TopNav.tsx (single source of truth), not define its own destinations"
  );
}

// --- Account menu (PersonalMenu.tsx) ---

// Phase 32 -- Product Information Architecture + Seamless User Journey,
// Part 2/9, updated this test's own assertions (renamed from
// test_watchlist_and_investor_removed_from_account_menu's original
// "these must remain" shape): "My Ideas"/"My Startup"/"Learn" are no
// longer in the account menu at all -- they were promoted to always-
// visible primary nav destinations (TopNav.tsx's own PRIMARY_NAVIGATION,
// "My Startup" now "My Startups"), and Section 9's own "duplicate
// destinations" failure mode is exactly why they were removed from here
// rather than left as a second copy. Watchlist/Investor intelligence
// stay removed, unchanged from Phase 15.
function test_watchlist_and_investor_removed_from_account_menu(): void {
  const source = readSource("components/layout/PersonalMenu.tsx");
  expect(
    !/label="Watchlist"/.test(source),
    "Phase 15: \"Watchlist\" must not appear in the account menu -- it watches the same cold-start-affected discovery population as Explore"
  );
  expect(
    !/label="Investor intelligence"/.test(source),
    "Phase 15: \"Investor intelligence\" must not appear in the account menu -- this is a Founder Beta, and the investor surface is not populated enough to expose"
  );
  expect(
    !/label="My Ideas"/.test(source),
    "Phase 32: \"My Ideas\" must NOT appear in the account menu -- it is now a primary nav destination (Build), and duplicating it here is exactly the \"duplicate destination\" failure Part 9 asks to remove"
  );
  expect(
    !/label="My Startup"/.test(source),
    "Phase 32: \"My Startup\" must NOT appear in the account menu -- it is now the primary nav destination \"My Startups\""
  );
  expect(
    !/label="Learn"/.test(source),
    "Phase 32: \"Learn\" must NOT appear in the account menu -- it is now a primary nav destination"
  );
  expect(/label="Send feedback"/.test(source), "\"Send feedback\" must remain -- it has no other home in the shell");
}

// Phase 32, Part 2. The exact same destinations must be reachable from
// the primary nav now that PersonalMenu no longer carries them --
// otherwise removing them from the account menu would be a net loss of
// access, not a deduplication.
function test_promoted_destinations_are_reachable_from_primary_nav(): void {
  const source = readSource("components/layout/TopNav.tsx");
  const arrayStart = source.indexOf("export const PRIMARY_NAVIGATION");
  const arrayEnd = source.indexOf("];", arrayStart);
  const arrayText = source.slice(arrayStart, arrayEnd);

  expect(/name:\s*"My Startups"/.test(arrayText), "\"My Startups\" must be a primary nav destination now that PersonalMenu no longer links to /founder");
  expect(/href:\s*"\/founder"/.test(arrayText), "The primary nav's \"My Startups\" entry must route into the existing /founder Founder Workspace chooser, not a new page");
}

// --- Hide, don't delete: every de-emphasized route's page file must still exist ---

function test_deemphasized_routes_remain_present_on_disk(): void {
  const preservedRoutes = [
    "app/rankings/page.tsx",
    "app/search/page.tsx",
    "app/compare/page.tsx",
    "app/saved/page.tsx",
    "app/investor/page.tsx",
    "app/startup/[id]/page.tsx",
  ];

  for (const route of preservedRoutes) {
    expect(
      existsSync(path.join(DASHBOARD_ROOT, route)),
      `Phase 15 Part 16/17: ${route} must still exist -- de-emphasizing navigation must never delete a route`
    );
  }
}

function test_explore_preview_component_untouched_not_deleted(): void {
  expect(
    existsSync(path.join(DASHBOARD_ROOT, "components/home/ExplorePreview.tsx")),
    "components/home/ExplorePreview.tsx must still exist -- removed from the homepage's render, not deleted from the codebase"
  );
}

// --- Homepage: ExplorePreview no longer rendered, EntryPaths has no dangling Explore card ---

function test_homepage_no_longer_renders_explore_preview(): void {
  // Checks the actual import/JSX usage, not prose -- this file's own
  // comments legitimately reference "ExplorePreview" by name to explain
  // why it was removed and where it still lives.
  const source = readSource("app/page.tsx");
  expect(
    !/from\s+"@\/components\/home\/ExplorePreview"/.test(source),
    "app/page.tsx must not import ExplorePreview (Phase 15 Part 14/19)"
  );
  expect(!/<ExplorePreview\s*\/>/.test(source), "app/page.tsx must not render <ExplorePreview />");
}

// Phase 32, Part 6: EntryPaths' own three cards were rebuilt around user
// intent per the directive's exact recommended structure -- "Build an
// idea"/"Analyze my startup"/"Review my pitch deck" (the Phase 15-era
// titles this test originally asserted) are gone from the card grid
// itself; pitch deck review is deliberately subordinated to a small link
// below the three cards instead of a co-equal fourth card. The
// Founder-Beta-era assertion this test keeps -- no "Explore startups"
// card -- is still correct and unchanged.
function test_entry_paths_no_longer_offers_explore_startups_card(): void {
  const source = readSource("components/home/EntryPaths.tsx");
  expect(
    !/title:\s*"Explore startups"/.test(source),
    "EntryPaths must not offer an \"Explore startups\" entry path on the Founder Beta homepage"
  );
  // The three intent-based paths Phase 32 replaced them with must be there.
  for (const title of ["Explore an Idea", "Work on My Startup", "Analyze a Company"]) {
    expect(source.includes(title), `EntryPaths must still offer "${title}"`);
  }
  // Pitch deck review must remain reachable, just not as a fourth
  // co-equal card (Part 6's own explicit instruction).
  expect(source.includes("/analyze/deck"), "Pitch deck review must remain reachable from the homepage, even if subordinate to the three primary cards");
}

const TESTS: [string, () => void][] = [
  ["test_explore_removed_from_primary_navigation", test_explore_removed_from_primary_navigation],
  ["test_global_nav_is_build_analyze_learn", test_global_nav_is_build_analyze_learn],
  ["test_mobile_tab_bar_shares_the_same_primary_navigation_source", test_mobile_tab_bar_shares_the_same_primary_navigation_source],
  ["test_watchlist_and_investor_removed_from_account_menu", test_watchlist_and_investor_removed_from_account_menu],
  ["test_promoted_destinations_are_reachable_from_primary_nav", test_promoted_destinations_are_reachable_from_primary_nav],
  ["test_deemphasized_routes_remain_present_on_disk", test_deemphasized_routes_remain_present_on_disk],
  ["test_explore_preview_component_untouched_not_deleted", test_explore_preview_component_untouched_not_deleted],
  ["test_homepage_no_longer_renders_explore_preview", test_homepage_no_longer_renders_explore_preview],
  ["test_entry_paths_no_longer_offers_explore_startups_card", test_entry_paths_no_longer_offers_explore_startups_card],
];

function main(): void {
  console.log("\nFounder Beta Surface Audit tests");
  console.log("-".repeat(72));

  const failures: string[] = [];

  for (const [name, test] of TESTS) {
    try {
      test();
      console.log(`PASS  ${name}`);
    } catch (error) {
      console.log(`FAIL  ${name}\n      ${(error as Error).message}`);
      failures.push(name);
    }
  }

  console.log("-".repeat(72));
  console.log(`${TESTS.length - failures.length}/${TESTS.length} passed`);

  if (failures.length > 0) {
    process.exit(1);
  }
}

main();
