// Phase 10.9 -- Founder Playbooks V1 tests.
//
// No JS test runner exists in this repo (no jest/vitest/test script in
// package.json) -- the established test culture here is a hand-rolled
// expect()/PASS-FAIL/main() script, run directly (mirrors every
// app/tests/test_*.py file's own convention). Node 26's native TypeScript
// support runs this file with no build step and no bundler, which is
// exactly why dashboard/content/playbooks/* and
// dashboard/lib/playbooks/resourceMap.ts are written with zero "@/..."
// path-alias imports (plain node has no alias resolver) -- see those
// files' own docstrings.
//
// Run with (from dashboard/):
//   node tests/playbooks.test.ts
// or:
//   npm run test:playbooks
import { readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import path from "node:path";

import { getAllPlaybooks, getJourneyGroups, getPlaybookBySlug } from "../content/playbooks/index.ts";
import {
  getPlaybookForDeckSection,
  getPlaybookForMission,
  getPlaybookForReadinessGap,
  getPlaybookForVpsCategory,
} from "../lib/playbooks/resourceMap.ts";

function expect(condition: boolean, message: string): void {
  if (!condition) {
    throw new Error(message);
  }
}

// Part 3's exact required list.
const REQUIRED_SLUGS = [
  "customer-discovery",
  "problem-validation",
  "mvp",
  "market-sizing",
  "pricing",
  "go-to-market",
  "pitch-deck",
  "fundraising",
  "cap-table",
  "company-formation",
  "hiring",
];

// Phase 12 (Founder Playbooks V1) -- the five playbooks this phase
// targets: 3 upgraded in place (customer-discovery, problem-validation,
// mvp keep their original, already-shipped slugs) + 2 new
// (pricing-validation, early-traction). All five must carry the deeper
// Phase-12 structure (good/weak signal, before-you-start, etc.) -- the
// other 9 playbooks are explicitly out of this phase's scope and are not
// required to.
const PHASE_12_TARGET_SLUGS = [
  "customer-discovery",
  "problem-validation",
  "mvp",
  "pricing-validation",
  "early-traction",
];

function test_valid_playbook_resolution(): void {
  const playbook = getPlaybookBySlug("customer-discovery");
  expect(playbook !== undefined, "A known slug must resolve to a playbook");
  expect(playbook?.slug === "customer-discovery", "The resolved playbook must have the requested slug");
}

function test_invalid_slug_returns_undefined(): void {
  expect(getPlaybookBySlug("not-a-real-playbook-slug") === undefined, "An unknown slug must return undefined, not throw");
  expect(getPlaybookBySlug("") === undefined, "An empty slug must return undefined");
}

function test_required_playbooks_exist(): void {
  for (const slug of REQUIRED_SLUGS) {
    expect(getPlaybookBySlug(slug) !== undefined, `Part 3 requires a playbook at slug "${slug}"`);
  }
}

function test_content_completeness(): void {
  const VALID_STAGES = new Set(["start", "model", "build", "pitch", "fundraise"]);
  const VALID_AUDIENCES = new Set(["founder", "investor", "general"]);

  for (const playbook of getAllPlaybooks()) {
    expect(playbook.title.trim().length > 0, `${playbook.slug}: title must not be empty`);
    expect(playbook.description.trim().length > 0, `${playbook.slug}: description must not be empty`);
    expect(playbook.whatIsThis.length > 0 && playbook.whatIsThis.every((p) => p.trim().length > 0), `${playbook.slug}: whatIsThis must have at least one non-empty paragraph`);
    expect(playbook.whyItMatters.trim().length > 0, `${playbook.slug}: whyItMatters must not be empty`);
    expect(playbook.steps.length >= 3, `${playbook.slug}: expected at least 3 steps, got ${playbook.steps.length}`);
    expect(playbook.commonMistakes.length >= 2, `${playbook.slug}: expected at least 2 common mistakes, got ${playbook.commonMistakes.length}`);
    expect(playbook.checklist.length >= 3, `${playbook.slug}: expected at least 3 checklist items, got ${playbook.checklist.length}`);
    expect(playbook.whatGoodLooksLike.trim().length > 0, `${playbook.slug}: whatGoodLooksLike must not be empty`);
    expect(playbook.estimatedMinutes > 0, `${playbook.slug}: estimatedMinutes must be positive`);
    expect(VALID_STAGES.has(playbook.journeyStage), `${playbook.slug}: journeyStage "${playbook.journeyStage}" is not a recognized stage`);
    expect(VALID_AUDIENCES.has(playbook.audience), `${playbook.slug}: audience "${playbook.audience}" is not recognized`);
  }
}

function test_related_playbooks_resolve(): void {
  for (const playbook of getAllPlaybooks()) {
    for (const relatedSlug of playbook.relatedPlaybooks) {
      expect(
        getPlaybookBySlug(relatedSlug) !== undefined,
        `${playbook.slug} references relatedPlaybooks slug "${relatedSlug}", which does not exist -- dangling reference`
      );
    }
  }
}

function test_journey_groups_cover_every_playbook_exactly_once(): void {
  const groups = getJourneyGroups();
  const total = groups.reduce((sum, group) => sum + group.playbooks.length, 0);
  expect(total === getAllPlaybooks().length, "Every playbook must appear in exactly one journey group");

  for (const group of groups) {
    for (const playbook of group.playbooks) {
      expect(playbook.journeyStage === group.stage, `${playbook.slug} is grouped under "${group.stage}" but its own journeyStage is "${playbook.journeyStage}"`);
    }
  }
}

// --- Phase 12 tests: exactly 5 target playbooks, deeper structure ----------

function test_exactly_five_phase_12_playbooks_exist(): void {
  expect(PHASE_12_TARGET_SLUGS.length === 5, "Phase 12 targets exactly 5 playbooks");
  for (const slug of PHASE_12_TARGET_SLUGS) {
    expect(getPlaybookBySlug(slug) !== undefined, `Phase 12 target playbook "${slug}" must exist`);
  }
}

function test_no_duplicate_playbook_slugs(): void {
  const slugs = getAllPlaybooks().map((p) => p.slug);
  const unique = new Set(slugs);
  expect(unique.size === slugs.length, `Playbook slugs must be unique, got duplicates in: ${slugs.join(", ")}`);
}

function test_phase_12_playbooks_have_the_deeper_structure(): void {
  for (const slug of PHASE_12_TARGET_SLUGS) {
    const playbook = getPlaybookBySlug(slug)!;
    expect(!!playbook.objective?.trim(), `${slug}: objective (what you're trying to learn) must be present`);
    expect((playbook.beforeYouStart?.length ?? 0) >= 2, `${slug}: beforeYouStart must have at least 2 items`);
    expect((playbook.questionsToAskOrDo?.length ?? 0) >= 3, `${slug}: questionsToAskOrDo must have at least 3 items`);
    expect((playbook.goodSignal?.length ?? 0) >= 2, `${slug}: goodSignal must have at least 2 items`);
    expect((playbook.weakSignal?.length ?? 0) >= 2, `${slug}: weakSignal must have at least 2 items`);
    expect(!!playbook.whenYoureDone?.trim(), `${slug}: whenYoureDone must be present`);
    expect((playbook.whatToDoNext?.length ?? 0) >= 2, `${slug}: whatToDoNext must have at least 2 items`);
    expect((playbook.relatedMissionTypes?.length ?? 0) >= 1, `${slug}: relatedMissionTypes must name at least one mission_type`);
  }
}

function test_customer_discovery_has_an_example_script(): void {
  const playbook = getPlaybookBySlug("customer-discovery")!;
  expect((playbook.exampleScript?.length ?? 0) >= 4, "customer-discovery must include a worked example interview script");
  for (const line of playbook.exampleScript ?? []) {
    expect(line.speaker.trim().length > 0, "Every script line needs a speaker label");
    expect(line.line.trim().length > 0, "Every script line needs actual dialogue");
  }
}

function test_content_avoids_filler_language(): void {
  // Part 22's explicit filler examples must not appear verbatim as
  // standalone advice anywhere in the 5 target playbooks' steps or
  // questionsToAskOrDo -- a light guard against regressing into vague
  // advice, not a literary style-checker.
  const FILLER_PHRASES = ["talk to your customers.", "validate your idea.", "focus on value.", "iterate based on feedback."];
  for (const slug of PHASE_12_TARGET_SLUGS) {
    const playbook = getPlaybookBySlug(slug)!;
    const haystack = [...playbook.steps, ...(playbook.questionsToAskOrDo ?? [])].join(" ").toLowerCase();
    for (const filler of FILLER_PHRASES) {
      expect(!haystack.includes(filler), `${slug}: contains filler-level advice ("${filler}") instead of concrete guidance`);
    }
  }
}

// --- Phase 14 (Founder Journey Audit) regression: Part 11 -------------------
//
// missionSuggestions.ts lives outside this file's alias-free module family
// (it imports "@/types", which plain node can't resolve -- see this file's
// own header comment) so it can't be imported directly here. This reads its
// source as text instead (the same cross-boundary technique the firewall
// tests below already use) -- a lightweight guard against silently
// regressing the exact classification this phase corrected: "Secure a
// first paying customer to validate willingness to pay." must be tagged
// missionType: "pricing", not "validation" -- which is what caused it to
// resolve to the wrong playbook both as a raw Next Move (Customer
// Discovery, via the old category-only lookup) and, even after Phase 12's
// own mission-level fix, once turned into a Mission (Problem Validation,
// neither of which is Pricing & Willingness-to-Pay).
function test_willingness_to_pay_milestone_is_tagged_pricing_not_validation(): void {
  const source = readFileSync(path.join(DASHBOARD_ROOT, "components/idea-lab/missionSuggestions.ts"), "utf-8");
  const milestoneIndex = source.indexOf("Secure a first paying customer to validate willingness to pay.");
  expect(milestoneIndex !== -1, "Expected milestone string not found in missionSuggestions.ts -- has it been reworded?");

  const entryText = source.slice(milestoneIndex, milestoneIndex + 300);
  expect(
    /missionType:\s*"pricing"/.test(entryText),
    `"Secure a first paying customer..." must be tagged missionType: "pricing" (not "validation"), got surrounding text: ${entryText}`
  );
}

// Confirms the SAME resolution mechanism NextMoves.tsx and MissionsSection
// use agree, by construction, for this milestone -- not just that the
// underlying tag is correct in isolation.
function test_willingness_to_pay_milestone_resolves_to_pricing_validation_playbook(): void {
  const playbook = getPlaybookForMission({ missionType: "pricing", relatedCategory: "validation" });
  expect(
    playbook?.slug === "pricing-validation",
    `Expected the pricing/willingness-to-pay milestone to resolve to "pricing-validation", got: ${playbook?.slug}`
  );
}

// --- Centralized mapping tests (Part 6/15) ----------------------------------

function test_vps_category_mapping_covers_all_six_categories(): void {
  // app/ai/vps_scoring.py::VPS_CATEGORIES -- every category Idea Lab's
  // VPSResultPanel/NextMoves can ever show must resolve to a REAL,
  // existing playbook (never a dangling slug).
  const categories = ["market_potential", "problem_solution", "founder_readiness", "gtm_feasibility", "economic_potential", "validation"];

  for (const category of categories) {
    const playbook = getPlaybookForVpsCategory(category);
    expect(playbook !== null, `VPS category "${category}" should map to a playbook`);
  }

  expect(getPlaybookForVpsCategory("validation")?.slug === "customer-discovery", "Part 5's own worked example: validation -> Customer Discovery");
}

function test_mission_type_mapping_examples() {
  // Part 5A's own worked examples, updated by Phase 12 Part 12: "Test
  // willingness to pay" -> pricing_validation, "Acquire first customers"
  // -> early_traction (both repointed in resourceMap.ts's
  // MISSION_TYPE_TO_PLAYBOOK -- see that file's own comment for why).
  expect(
    getPlaybookForMission({ missionType: "customer_discovery" })?.slug === "customer-discovery",
    "Customer interview mission (mission_type=customer_discovery) should map to Customer Discovery"
  );
  expect(
    getPlaybookForMission({ missionType: "validation" })?.slug === "problem-validation",
    "Validate-severity/frequency mission (mission_type=validation) should map to Problem Validation"
  );
  expect(
    getPlaybookForMission({ missionType: "product" })?.slug === "mvp",
    "Test-prototype mission (mission_type=product) should map to MVP"
  );
  expect(
    getPlaybookForMission({ missionType: "pricing" })?.slug === "pricing-validation",
    "Pricing/willingness-to-pay mission (mission_type=pricing) should map to Pricing & Willingness-to-Pay"
  );
  expect(
    getPlaybookForMission({ missionType: "gtm" })?.slug === "early-traction",
    "Acquire-first-customers mission (mission_type=gtm) should map to Early Traction & First Customers"
  );
  // "Market research" from missionSuggestions.ts's own table has
  // missionType="other" + relatedCategory="market_potential" -- mission_type
  // alone has no confident mapping, so this must fall back to the category.
  expect(
    getPlaybookForMission({ missionType: "other", relatedCategory: "market_potential" })?.slug === "market-sizing",
    "A mission with no specific mission_type mapping must fall back to related_category"
  );
}

function test_unknown_resource_ref_returns_undefined_not_a_guess(): void {
  // Mirrors exactly how MissionsSection.tsx resolves a mission's own
  // resource_ref (getPlaybookBySlug(primaryMission.resource_ref)) --
  // an unrecognized/stale resource_ref value must resolve to undefined,
  // never throw and never silently guess a fallback playbook.
  expect(getPlaybookBySlug("this-slug-does-not-exist") === undefined, "An unknown resource_ref must resolve to undefined");
}

function test_mission_with_no_mapping_remains_usable_without_a_playbook(): void {
  const playbook = getPlaybookForMission({ missionType: "other", relatedCategory: null });
  expect(playbook === null, "A mission with no confident mapping must resolve to null, not a guessed playbook");
}

function test_deck_section_mapping_examples(): void {
  // Part 5C's own worked examples.
  expect(getPlaybookForDeckSection("problem")?.slug === "problem-validation", "Deck Problem section -> Problem Validation");
  expect(getPlaybookForDeckSection("market")?.slug === "market-sizing", "Deck Market section -> Market & Competition");
  expect(getPlaybookForDeckSection("business_model")?.slug === "pricing", "Deck Business Model section -> Business Model & Pricing");
  expect(getPlaybookForDeckSection("ask")?.slug === "fundraising", "Deck Ask section -> Fundraising");
  expect(getPlaybookForDeckSection("traction") !== null, "Deck Traction section should map to a playbook (Go-to-Market or Fundraising, per Part 5C)");
}

function test_deck_section_with_no_clear_resource_returns_null(): void {
  expect(getPlaybookForDeckSection("cover") === null, "Cover has no dedicated educational resource -- must not force a guess");
  expect(getPlaybookForDeckSection("other") === null, "An uncategorized deck section must not force a guess");
}

function test_readiness_gap_mapping_examples(): void {
  // Part 5D's own explicit four-playbook list: Fundraising, Pitch Deck,
  // Go-to-Market, Cap Table.
  expect(
    getPlaybookForReadinessGap({ category: "materials", pillar: null })?.slug === "pitch-deck",
    "A 'no pitch deck analyzed' gap must map to the Pitch Deck playbook regardless of pillar"
  );
  expect(
    getPlaybookForReadinessGap({ category: "weak_evidence", pillar: "team" })?.slug === "hiring",
    "A team-pillar gap should map to Hiring & Team"
  );
  expect(
    getPlaybookForReadinessGap({ category: "weak_evidence", pillar: "execution" })?.slug === "go-to-market",
    "An execution-pillar gap should map to Go-to-Market"
  );
  expect(
    getPlaybookForReadinessGap({ category: "insufficient_evidence_for_stage", pillar: "financial_health" })?.slug === "cap-table",
    "A financial_health-pillar gap should map to Cap Table & Dilution"
  );
  expect(
    getPlaybookForReadinessGap({ category: "likely_investor_scrutiny", pillar: null })?.slug === "fundraising",
    "A gap with no pillar and no special category should fall back to the generic Fundraising playbook"
  );
}

// --- Firewall tests (Part 10) ------------------------------------------------
//
// These modules have zero I/O by construction -- no fetch, no database
// call, no mutation of anything -- so the meaningful automated check is
// that the SOURCE CODE itself never references anything from the
// scoring/persistence layers. This isn't a behavioral test (there is no
// behavior to provoke); it's a structural guard against a future edit
// accidentally introducing exactly the coupling Part 10 forbids.
const __dirname = path.dirname(fileURLToPath(import.meta.url));
const DASHBOARD_ROOT = path.resolve(__dirname, "..");

const FORBIDDEN_SUBSTRINGS = [
  "apiFetch",
  "fetch(",
  "compute_vps",
  "updateVenture(",
  "updateVentureMissionStatus",
  "createFounderAction",
  "save_analysis",
  "localStorage.setItem",
];

const FILES_THAT_MUST_STAY_PURE = [
  "content/playbooks/types.ts",
  "content/playbooks/data.ts",
  "content/playbooks/index.ts",
  "lib/playbooks/resourceMap.ts",
];

function test_playbook_modules_contain_no_scoring_or_persistence_calls(): void {
  for (const relativePath of FILES_THAT_MUST_STAY_PURE) {
    const source = readFileSync(path.join(DASHBOARD_ROOT, relativePath), "utf-8");

    for (const forbidden of FORBIDDEN_SUBSTRINGS) {
      expect(!source.includes(forbidden), `${relativePath} must never reference "${forbidden}" (Part 10 firewall)`);
    }
  }
}

const TESTS: [string, () => void][] = [
  ["test_valid_playbook_resolution", test_valid_playbook_resolution],
  ["test_invalid_slug_returns_undefined", test_invalid_slug_returns_undefined],
  ["test_required_playbooks_exist", test_required_playbooks_exist],
  ["test_content_completeness", test_content_completeness],
  ["test_related_playbooks_resolve", test_related_playbooks_resolve],
  ["test_journey_groups_cover_every_playbook_exactly_once", test_journey_groups_cover_every_playbook_exactly_once],
  ["test_willingness_to_pay_milestone_is_tagged_pricing_not_validation", test_willingness_to_pay_milestone_is_tagged_pricing_not_validation],
  ["test_willingness_to_pay_milestone_resolves_to_pricing_validation_playbook", test_willingness_to_pay_milestone_resolves_to_pricing_validation_playbook],
  ["test_exactly_five_phase_12_playbooks_exist", test_exactly_five_phase_12_playbooks_exist],
  ["test_no_duplicate_playbook_slugs", test_no_duplicate_playbook_slugs],
  ["test_phase_12_playbooks_have_the_deeper_structure", test_phase_12_playbooks_have_the_deeper_structure],
  ["test_customer_discovery_has_an_example_script", test_customer_discovery_has_an_example_script],
  ["test_content_avoids_filler_language", test_content_avoids_filler_language],
  ["test_vps_category_mapping_covers_all_six_categories", test_vps_category_mapping_covers_all_six_categories],
  ["test_mission_type_mapping_examples", test_mission_type_mapping_examples],
  ["test_unknown_resource_ref_returns_undefined_not_a_guess", test_unknown_resource_ref_returns_undefined_not_a_guess],
  ["test_mission_with_no_mapping_remains_usable_without_a_playbook", test_mission_with_no_mapping_remains_usable_without_a_playbook],
  ["test_deck_section_mapping_examples", test_deck_section_mapping_examples],
  ["test_deck_section_with_no_clear_resource_returns_null", test_deck_section_with_no_clear_resource_returns_null],
  ["test_readiness_gap_mapping_examples", test_readiness_gap_mapping_examples],
  ["test_playbook_modules_contain_no_scoring_or_persistence_calls", test_playbook_modules_contain_no_scoring_or_persistence_calls],
];

function main(): void {
  console.log("\nFounder Playbooks V1 tests");
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
