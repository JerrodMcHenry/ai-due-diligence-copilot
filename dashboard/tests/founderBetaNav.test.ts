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
  expect(/label="My Ideas"/.test(source), "\"My Ideas\" must remain in the account menu");
  expect(/label="My Startup"/.test(source), "\"My Startup\" must remain in the account menu");
  expect(/label="Learn"/.test(source), "\"Learn\" (Playbooks) must remain in the account menu");
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

function test_entry_paths_no_longer_offers_explore_startups_card(): void {
  const source = readSource("components/home/EntryPaths.tsx");
  expect(
    !/title:\s*"Explore startups"/.test(source),
    "EntryPaths must not offer an \"Explore startups\" entry path on the Founder Beta homepage"
  );
  // The other three founder-relevant paths must still be there.
  for (const title of ["Build an idea", "Analyze my startup", "Review my pitch deck"]) {
    expect(source.includes(`title:\n    "${title}",`) || source.includes(`title: "${title}",`) || source.includes(title), `EntryPaths must still offer "${title}"`);
  }
}

const TESTS: [string, () => void][] = [
  ["test_explore_removed_from_primary_navigation", test_explore_removed_from_primary_navigation],
  ["test_mobile_tab_bar_shares_the_same_primary_navigation_source", test_mobile_tab_bar_shares_the_same_primary_navigation_source],
  ["test_watchlist_and_investor_removed_from_account_menu", test_watchlist_and_investor_removed_from_account_menu],
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
