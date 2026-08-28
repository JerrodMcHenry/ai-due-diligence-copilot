// Phase 10.10 -- Founder Journey Integration tests.
//
// Same hand-rolled expect()/PASS-FAIL/main() convention as
// tests/playbooks.test.ts (this repo has no jest/vitest), run directly by
// Node's native TypeScript support -- no build step, no bundler, which is
// why founderJourney.ts and resolveIdeaLabNextStep.ts are written with
// zero "@/..." alias imports (see those files' own docstrings).
//
// Run with:
//   node tests/journey.test.ts
// or:
//   npm run test:journey
import { readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import path from "node:path";

import {
  JOURNEY_STAGES,
  PLAYBOOK_STAGE_TO_JOURNEY_STAGE,
  VENTURE_JOURNEY_STEP_IDS,
  VENTURE_STAGE_TO_JOURNEY_STAGE,
  getJourneyStage,
} from "../lib/founderJourney.ts";
import { resolveIdeaLabNextStep } from "../lib/journey/resolveIdeaLabNextStep.ts";
import { getAllPlaybooks } from "../content/playbooks/index.ts";

function expect(condition: boolean, message: string): void {
  if (!condition) {
    throw new Error(message);
  }
}

const VALID_STAGE_IDS = new Set(JOURNEY_STAGES.map((stage) => stage.id));

// --- Journey stage definitions -----------------------------------------

function test_journey_stages_have_eight_unique_ids(): void {
  expect(JOURNEY_STAGES.length === 8, `Expected exactly 8 journey stages (Part 2's own list), got ${JOURNEY_STAGES.length}`);
  expect(VALID_STAGE_IDS.size === 8, "Journey stage ids must be unique");
}

function test_journey_stages_are_complete(): void {
  for (const stage of JOURNEY_STAGES) {
    expect(stage.label.trim().length > 0, `${stage.id}: label must not be empty`);
    expect(stage.plainLanguageLabel.trim().length > 0, `${stage.id}: plainLanguageLabel must not be empty`);
    expect(stage.description.trim().length > 0, `${stage.id}: description must not be empty`);
    // Part 2's own explicit requirement: never imply a deterministic
    // sequence or a completion percentage.
    expect(!/\d+%/.test(stage.description), `${stage.id}: description must never contain a completion percentage`);
  }
}

function test_get_journey_stage_resolves_every_id(): void {
  for (const id of VALID_STAGE_IDS) {
    const stage = getJourneyStage(id as never);
    expect(stage !== undefined && stage.id === id, `getJourneyStage("${id}") must return the matching stage`);
  }
}

// --- Normalization maps target real stage ids ---------------------------

function test_venture_stage_normalization_targets_real_stages(): void {
  for (const [ventureStage, journeyId] of Object.entries(VENTURE_STAGE_TO_JOURNEY_STAGE)) {
    expect(VALID_STAGE_IDS.has(journeyId), `VENTURE_STAGE_TO_JOURNEY_STAGE["${ventureStage}"] = "${journeyId}" is not a real journey stage id`);
  }
  expect(Object.keys(VENTURE_STAGE_TO_JOURNEY_STAGE).length === 5, "Expected all 5 VENTURE_STAGES values to be mapped");
}

function test_venture_journey_step_ids_are_valid_and_five(): void {
  expect(VENTURE_JOURNEY_STEP_IDS.length === 5, "VentureJourney's stepper shows exactly 5 of the 8 stages");
  for (const id of VENTURE_JOURNEY_STEP_IDS) {
    expect(VALID_STAGE_IDS.has(id), `VENTURE_JOURNEY_STEP_IDS contains "${id}", which is not a real journey stage id`);
  }
}

function test_playbook_stage_normalization_targets_real_stages(): void {
  for (const [playbookStage, journeyId] of Object.entries(PLAYBOOK_STAGE_TO_JOURNEY_STAGE)) {
    expect(VALID_STAGE_IDS.has(journeyId), `PLAYBOOK_STAGE_TO_JOURNEY_STAGE["${playbookStage}"] = "${journeyId}" is not a real journey stage id`);
  }
}

// Cross-check against the REAL playbook content -- catches the case
// where a future playbook uses a journeyStage value this normalization
// map doesn't know about yet (a silent gap, not just a typo).
function test_every_playbook_journey_stage_is_normalizable(): void {
  const knownPlaybookStages = new Set(Object.keys(PLAYBOOK_STAGE_TO_JOURNEY_STAGE));

  for (const playbook of getAllPlaybooks()) {
    expect(
      knownPlaybookStages.has(playbook.journeyStage),
      `Playbook "${playbook.slug}" has journeyStage "${playbook.journeyStage}", which PLAYBOOK_STAGE_TO_JOURNEY_STAGE does not normalize`
    );
  }
}

// --- resolveIdeaLabNextStep (deterministic, no LLM, no score) -----------

function test_resolve_next_step_no_model_result(): void {
  const step = resolveIdeaLabNextStep(null);
  expect(step.kind === "add_assumptions", "A null model result must resolve to add_assumptions");
}

function test_resolve_next_step_null_vps(): void {
  const step = resolveIdeaLabNextStep({ vps: null, next_milestones: ["Interview 20+ target customers to validate the problem is real."] });
  expect(step.kind === "add_assumptions", "A null vps must resolve to add_assumptions regardless of milestones");
}

function test_resolve_next_step_with_milestones(): void {
  const step = resolveIdeaLabNextStep({ vps: 4.6, next_milestones: ["Define a primary customer-acquisition strategy.", "Estimate a pricing model and expected gross margin."] });
  expect(step.kind === "work_on_milestone", "A scored model with open milestones must resolve to work_on_milestone");
  expect(
    step.kind === "work_on_milestone" && step.milestoneText === "Define a primary customer-acquisition strategy.",
    "Must surface the FIRST milestone, not a random or summarized one"
  );
}

function test_resolve_next_step_no_open_milestones(): void {
  const step = resolveIdeaLabNextStep({ vps: 8.2, next_milestones: [] });
  expect(step.kind === "ready_for_real_startup", "A scored model with no open milestones must resolve to ready_for_real_startup");
}

function test_resolve_next_step_is_pure_and_deterministic(): void {
  const input = { vps: 5.0, next_milestones: ["Assess how intense competition is in your target market."] };
  const first = resolveIdeaLabNextStep(input);
  const second = resolveIdeaLabNextStep(input);
  expect(JSON.stringify(first) === JSON.stringify(second), "Identical input must always produce identical output -- no hidden randomness or state");
}

// --- Firewall: journey modules touch no scoring/persistence layer -------

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
];

const FILES_THAT_MUST_STAY_PURE = [
  "lib/founderJourney.ts",
  "lib/journey/resolveIdeaLabNextStep.ts",
];

function test_journey_modules_contain_no_scoring_or_persistence_calls(): void {
  for (const relativePath of FILES_THAT_MUST_STAY_PURE) {
    const source = readFileSync(path.join(DASHBOARD_ROOT, relativePath), "utf-8");

    for (const forbidden of FORBIDDEN_SUBSTRINGS) {
      expect(!source.includes(forbidden), `${relativePath} must never reference "${forbidden}" (Part 17 firewall)`);
    }
  }
}

function test_venture_handoff_only_uses_sessionstorage_no_network(): void {
  const source = readFileSync(path.join(DASHBOARD_ROOT, "lib/ventureToStartupHandoff.ts"), "utf-8");

  for (const forbidden of FORBIDDEN_SUBSTRINGS) {
    expect(!source.includes(forbidden), `lib/ventureToStartupHandoff.ts must never reference "${forbidden}" (Part 17 firewall)`);
  }
  expect(source.includes("sessionStorage"), "The handoff must use sessionStorage, not a new persistence mechanism");
}

const TESTS: [string, () => void][] = [
  ["test_journey_stages_have_eight_unique_ids", test_journey_stages_have_eight_unique_ids],
  ["test_journey_stages_are_complete", test_journey_stages_are_complete],
  ["test_get_journey_stage_resolves_every_id", test_get_journey_stage_resolves_every_id],
  ["test_venture_stage_normalization_targets_real_stages", test_venture_stage_normalization_targets_real_stages],
  ["test_venture_journey_step_ids_are_valid_and_five", test_venture_journey_step_ids_are_valid_and_five],
  ["test_playbook_stage_normalization_targets_real_stages", test_playbook_stage_normalization_targets_real_stages],
  ["test_every_playbook_journey_stage_is_normalizable", test_every_playbook_journey_stage_is_normalizable],
  ["test_resolve_next_step_no_model_result", test_resolve_next_step_no_model_result],
  ["test_resolve_next_step_null_vps", test_resolve_next_step_null_vps],
  ["test_resolve_next_step_with_milestones", test_resolve_next_step_with_milestones],
  ["test_resolve_next_step_no_open_milestones", test_resolve_next_step_no_open_milestones],
  ["test_resolve_next_step_is_pure_and_deterministic", test_resolve_next_step_is_pure_and_deterministic],
  ["test_journey_modules_contain_no_scoring_or_persistence_calls", test_journey_modules_contain_no_scoring_or_persistence_calls],
  ["test_venture_handoff_only_uses_sessionstorage_no_network", test_venture_handoff_only_uses_sessionstorage_no_network],
];

function main(): void {
  console.log("\nFounder Journey Integration tests");
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
