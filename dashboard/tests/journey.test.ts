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
import { resolveRecentLearning } from "../lib/journey/resolveRecentLearning.ts";
import { resolveLatestModelChange } from "../lib/journey/resolveLatestModelChange.ts";
import { inferEvidenceStepIndex, resolveVentureStepIndex, resolveVentureState } from "../lib/journey/inferVentureStage.ts";
import { getAllPlaybooks } from "../content/playbooks/index.ts";
import { getWhatIfScenarios } from "../components/idea-lab/whatIfScenarios.ts";
import { summarizeConceptForCard } from "../components/idea-lab/summarizeConceptForCard.ts";
import { formatHistoryDateGroupLabel, groupHistoryEventsByDate, formatVpsDelta } from "../lib/journey/formatVentureHistory.ts";

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

// --- resolveRecentLearning (Phase 13, Part 13) --------------------------

function test_recent_learning_empty_when_no_missions(): void {
  expect(resolveRecentLearning([]) === null, "Zero missions must resolve to null, not a fabricated empty-state value");
}

function test_recent_learning_empty_when_no_mission_has_learning(): void {
  const missions = [
    { title: "Interview target customers", learning_summary: null, learning_recorded_at: null },
    { title: "Test pricing", learning_summary: null, learning_recorded_at: "2026-01-01T00:00:00Z" },
  ];
  expect(resolveRecentLearning(missions) === null, "A mission with a recorded_at but no summary text must not surface as learning");
}

function test_recent_learning_picks_most_recent_by_recorded_at(): void {
  const missions = [
    { title: "Older mission", learning_summary: "Talked to 5 people, mixed signal.", learning_recorded_at: "2026-01-01T00:00:00Z" },
    { title: "Newer mission", learning_summary: "3 of 10 customers agreed to a paid pilot.", learning_recorded_at: "2026-03-15T00:00:00Z" },
  ];
  const result = resolveRecentLearning(missions);
  expect(result !== null, "Expected a real result");
  expect(result?.missionTitle === "Newer mission", `Must pick the most recently recorded learning, got: ${result?.missionTitle}`);
  expect(result?.summary === "3 of 10 customers agreed to a paid pilot.", "Must return the exact founder-written text, not a summary of it");
}

function test_recent_learning_considers_completed_missions_too(): void {
  // The core Phase 13 gap this function closes: a completed mission's
  // learning must not become invisible just because it's no longer the
  // "active" mission MissionsSection shows inline.
  const missions = [
    { title: "Completed mission", learning_summary: "No useful signal yet.", learning_recorded_at: "2026-05-01T00:00:00Z" },
  ];
  const result = resolveRecentLearning(missions);
  expect(result !== null && result.summary === "No useful signal yet.", "A completed mission's real learning must still surface");
}

function test_recent_learning_is_pure_and_deterministic(): void {
  const missions = [{ title: "A mission", learning_summary: "Learned something.", learning_recorded_at: "2026-02-01T00:00:00Z" }];
  const first = resolveRecentLearning(missions);
  const second = resolveRecentLearning(missions);
  expect(JSON.stringify(first) === JSON.stringify(second), "Identical input must always produce identical output");
}

// --- resolveLatestModelChange (Phase 26, Part 8/9/11) --------------------

function test_latest_model_change_null_when_no_updates(): void {
  const events = [
    { event_type: "venture_created", occurred_at: "2026-01-01T00:00:00Z", before_vps: null, after_vps: 5.0, assumption_changes: [] },
    { event_type: "action_added", occurred_at: "2026-01-02T00:00:00Z", before_vps: null, after_vps: null, assumption_changes: [] },
  ];
  expect(resolveLatestModelChange(events) === null, "Zero model_updated events must resolve to null, not a fabricated value");
}

function test_latest_model_change_picks_first_since_events_are_newest_first(): void {
  // The backend already returns events newest-first (app/api.py's own
  // events.sort(..., reverse=True)) -- this function must NOT re-sort;
  // it trusts that ordering and takes the first model_updated match.
  const events = [
    { event_type: "action_added", occurred_at: "2026-03-01T00:00:00Z", before_vps: null, after_vps: null, assumption_changes: [] },
    { event_type: "model_updated", occurred_at: "2026-02-15T00:00:00Z", before_vps: 6.5, after_vps: 6.9, assumption_changes: [{ label: "Price point", before: "$500", after: "$299" }] },
    { event_type: "model_updated", occurred_at: "2026-01-01T00:00:00Z", before_vps: 5.0, after_vps: 6.5, assumption_changes: [] },
  ];
  const result = resolveLatestModelChange(events);
  expect(result !== null, "Expected a real result");
  expect(result?.beforeVps === 6.5 && result?.afterVps === 6.9, `Must pick the newest-first (already-sorted) model_updated event, got before=${result?.beforeVps} after=${result?.afterVps}`);
  expect(result?.primaryAssumptionChange?.label === "Price point", "Must surface the first curated assumption change on that update");
}

function test_latest_model_change_handles_no_assumption_diff(): void {
  const events = [
    { event_type: "model_updated", occurred_at: "2026-01-01T00:00:00Z", before_vps: 6.9, after_vps: 6.9, assumption_changes: [] },
  ];
  const result = resolveLatestModelChange(events);
  expect(result !== null && result.primaryAssumptionChange === null, "An update with no curated assumption diff must report null, not a fabricated one");
}

function test_latest_model_change_is_pure_and_deterministic(): void {
  const events = [
    { event_type: "model_updated", occurred_at: "2026-01-01T00:00:00Z", before_vps: 6.0, after_vps: 6.4, assumption_changes: [] },
  ];
  const first = resolveLatestModelChange(events);
  const second = resolveLatestModelChange(events);
  expect(JSON.stringify(first) === JSON.stringify(second), "Identical input must always produce identical output");
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
  "lib/journey/resolveRecentLearning.ts",
  "lib/journey/resolveLatestModelChange.ts",
  "lib/journey/inferVentureStage.ts",
  "components/idea-lab/whatIfScenarios.ts",
  "components/idea-lab/summarizeConceptForCard.ts",
  "lib/journey/formatVentureHistory.ts",
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

// --- Founder Loop V2, Section 10: evidence-based journey stage ------------

function emptyMinimalAssumptions(): {
  market: { estimated_market_size: string | null; competition_intensity: string | null; market_description: string | null };
  problem_solution: { problem_statement: string | null; solution_description: string | null };
  founder: { founder_count: number | null };
  gtm: { primary_acquisition_strategy: string | null };
  economics: { pricing_model: string | null };
  validation: { customer_interviews: number | null; waitlist_signups: number | null; paying_customers: number | null; monthly_revenue: number | null };
} {
  return {
    market: { estimated_market_size: null, competition_intensity: null, market_description: null },
    problem_solution: { problem_statement: null, solution_description: null },
    founder: { founder_count: null },
    gtm: { primary_acquisition_strategy: null },
    economics: { pricing_model: null },
    validation: { customer_interviews: null, waitlist_signups: null, paying_customers: null, monthly_revenue: null },
  };
}

function test_infer_evidence_step_idea_with_nothing_modeled(): void {
  expect(inferEvidenceStepIndex(null) === 0, "null assumptions must infer Idea (index 0)");
  expect(inferEvidenceStepIndex(emptyMinimalAssumptions()) === 0, "An empty venture must infer Idea (index 0)");
}

function test_infer_evidence_step_model_when_assumptions_present(): void {
  const a = emptyMinimalAssumptions();
  a.market.estimated_market_size = "Large";
  expect(inferEvidenceStepIndex(a) === 1, "A venture with a modeled assumption but no real signal should infer Model (index 1)");
}

function test_infer_evidence_step_experiment_when_interviews_reported(): void {
  const a = emptyMinimalAssumptions();
  a.validation.customer_interviews = 10;
  expect(inferEvidenceStepIndex(a) === 2, "A venture with reported interviews but no traction should infer Experiment (index 2)");
}

function test_infer_evidence_step_build_when_real_traction_exists(): void {
  const a = emptyMinimalAssumptions();
  a.validation.paying_customers = 14;
  a.validation.monthly_revenue = 70000;
  expect(inferEvidenceStepIndex(a) === 3, "A venture with real paying customers/revenue should infer Build (index 3)");
}

function test_infer_evidence_step_never_reaches_fundraise(): void {
  // Section 10's own point: fundraising isn't every venture's destination
  // -- evidence of traction alone must never auto-imply it. Index 4
  // ("Fundraise") is reachable only via the founder's own explicit stage.
  const a = emptyMinimalAssumptions();
  a.validation.paying_customers = 1_000_000;
  a.validation.monthly_revenue = 10_000_000;
  expect(inferEvidenceStepIndex(a) <= 3, `Evidence alone must never infer past Build (index 3), got ${inferEvidenceStepIndex(a)}`);
}

function test_resolve_step_index_prefers_the_more_advanced_of_manual_and_evidence(): void {
  const traction = emptyMinimalAssumptions();
  traction.validation.paying_customers = 14;

  // A stale/default manual stage (index 0, "Idea") must not hide real
  // evidence of traction (index 3, "Build") -- this is the exact
  // ClaimPilot-shaped bug this phase's own investigation confirmed live.
  expect(resolveVentureStepIndex(0, traction) === 3, "Real evidence must win over a stale manual 'Idea' selection");

  // An UNMAPPED manual stage (-1, e.g. a nonstandard/free-typed value)
  // must never outrank real evidence either.
  expect(resolveVentureStepIndex(-1, traction) === 3, "An unmapped manual stage must not suppress real evidence");

  // A founder's own explicit, FURTHER-ALONG choice (e.g. "Launched",
  // manual index 4) must never be walked backward by evidence alone.
  expect(resolveVentureStepIndex(4, traction) === 4, "An explicit further-along founder choice must never be overridden by evidence");

  // No evidence and no manual signal: Idea.
  expect(resolveVentureStepIndex(-1, null) === 0, "With neither manual nor evidence signal, the result must be Idea (index 0)");
}

// --- Founder Experience Model correction: resolveVentureState() ------------
// Re-buckets the SAME 0-4 index the tests above already exercise into one
// of three plain-language descriptions -- no new inference, so these
// tests mirror the ones above exactly, just asserting the bucketed label
// instead of the raw index.

function test_venture_state_idea_with_nothing_modeled(): void {
  expect(resolveVentureState(-1, null).id === "idea", "No evidence and no manual signal must resolve to 'idea'");
}

function test_venture_state_idea_when_only_assumptions_modeled(): void {
  const a = emptyMinimalAssumptions();
  a.problem_solution.problem_statement = "Something";
  expect(resolveVentureState(-1, a).id === "idea", "Modeled assumptions alone (evidence index 1) must still bucket to 'idea', not a separate state");
}

function test_venture_state_validating_when_interviews_reported(): void {
  const a = emptyMinimalAssumptions();
  a.validation.customer_interviews = 10;
  expect(resolveVentureState(-1, a).id === "validating", "Reported interviews (evidence index 2) must bucket to 'validating'");
}

function test_venture_state_building_when_real_traction_exists(): void {
  const a = emptyMinimalAssumptions();
  a.validation.paying_customers = 14;
  expect(resolveVentureState(-1, a).id === "building", "Real paying customers (evidence index 3) must bucket to 'building'");
}

function test_venture_state_never_reaches_a_fundraise_state(): void {
  // Part 3/5's own explicit instruction: fundraising is a tool, never a
  // maturity state or entrepreneurship's destination -- there must be no
  // fourth bucket a venture "graduates" into, no matter how strong its
  // evidence, and even a founder's own explicit "Launched" manual stage
  // (index 4) must still read as "building," not a separate state.
  const a = emptyMinimalAssumptions();
  a.validation.paying_customers = 1_000_000;
  a.validation.monthly_revenue = 10_000_000;
  expect(resolveVentureState(-1, a).id === "building", "Even extreme traction must bucket to 'building', never a separate 'fundraise' state");
  expect(resolveVentureState(4, a).id === "building", "An explicit 'Launched' manual stage must still read as 'building', not a separate state");
}

function test_venture_state_manual_stage_can_advance_but_not_invent_a_fourth_state(): void {
  // A stale/default manual stage must not hide real evidence, mirroring
  // test_resolve_step_index_prefers_the_more_advanced_of_manual_and_evidence
  // above -- but expressed as the bucketed state a founder actually reads.
  const traction = emptyMinimalAssumptions();
  traction.validation.paying_customers = 14;
  expect(resolveVentureState(0, traction).id === "building", "Real evidence must win over a stale manual 'Idea' selection");
}

function test_venture_state_descriptions_are_plain_language_not_a_score(): void {
  // Every state's description must read as a description of current
  // activity, never a percentage, a level number, or a claim of
  // completion -- Part 4's own explicit instruction against fabricating
  // false precision.
  const indexByState: Record<string, number> = { idea: 0, validating: 2, building: 3 };
  for (const [id, index] of Object.entries(indexByState)) {
    const state = resolveVentureState(index, null);
    expect(state.id === id, `resolveVentureState(${index}, null) must resolve to '${id}', got '${state.id}'`);
    expect(typeof state.label === "string" && state.label.length > 0, `${id}: must have a non-empty plain-language label`);
    expect(!/%|\blevel\b|\bstage \d\b/i.test(state.description), `${id}: description must not imply a percentage or numbered level: "${state.description}"`);
  }
}

// --- Founder Loop V2, Section 6: context-aware What If scenarios ----------

function assumptionsWithTraction() {
  return {
    market: { competition_intensity: "Medium" },
    founder: { has_technical_cofounder: true, has_business_cofounder: false },
    gtm: { expected_cac: null },
    economics: { price_point: null, expected_gross_margin_pct: 60 },
    validation: { customer_interviews: 85, paying_customers: 14, monthly_revenue: 70000, retention_pct: null },
  };
}

function assumptionsIdeaStage() {
  return {
    market: { competition_intensity: null },
    founder: { has_technical_cofounder: null, has_business_cofounder: null },
    gtm: { expected_cac: null },
    economics: { price_point: null, expected_gross_margin_pct: null },
    validation: { customer_interviews: null, paying_customers: null, monthly_revenue: null, retention_pct: null },
  };
}

function test_what_if_never_suggests_a_lower_interview_count_than_already_reported(): void {
  // A pre-commercial venture (no paying customers/revenue yet) with 85
  // already-reported interviews -- the interview scenario must still
  // move forward from the real current value, never reset it downward.
  const preCommercialManyInterviews = {
    ...assumptionsIdeaStage(),
    validation: { customer_interviews: 85, paying_customers: null, monthly_revenue: null, retention_pct: null },
  };
  const scenarios = getWhatIfScenarios(preCommercialManyInterviews);
  const interviewScenario = scenarios.find((s) => s.id === "interview-20" || s.id === "interview-more");
  expect(!!interviewScenario, "Expected an interview scenario to be present for a pre-commercial venture");

  const result = interviewScenario!.apply(preCommercialManyInterviews);
  expect(
    (result.validation.customer_interviews ?? 0) > 85,
    `A venture with 85 already-reported interviews must never be offered a scenario that lowers it (got ${result.validation.customer_interviews})`
  );
  expect(interviewScenario!.id !== "interview-20", "The stale fixed-20 preset must not be offered once interviews already exceed 20");
}

function test_what_if_suppresses_interview_scenario_at_commercial_scale(): void {
  // The confirmed regression case (Section 15 of the SIE Intelligence
  // Reset phase): a venture with real commercial scale (paying >= 10 or
  // revenue >= $10K/mo) must not be offered ANY "what if I interview N
  // customers" scenario -- not deprioritized, fully absent. Whether the
  // problem is real is no longer a meaningful open question at this
  // scale.
  const scenarios = getWhatIfScenarios(assumptionsWithTraction()); // 14 paying, $70K/mo
  const interviewScenario = scenarios.find((s) => s.id === "interview-20" || s.id === "interview-more");
  expect(
    interviewScenario === undefined,
    `A venture with real commercial scale must not be offered an interview scenario, got: ${interviewScenario?.question}`
  );
}

function test_what_if_scenarios_are_tagged_upside_or_downside(): void {
  const scenarios = getWhatIfScenarios(assumptionsWithTraction());
  expect(scenarios.length > 0, "Expected at least one scenario for a traction-stage venture");
  for (const scenario of scenarios) {
    expect(scenario.direction === "upside" || scenario.direction === "downside", `Every scenario must be tagged upside or downside, got: ${scenario.direction}`);
  }
  expect(scenarios.some((s) => s.direction === "downside"), "A traction-stage venture should be offered at least one downside/risk scenario");
}

function test_what_if_offers_churn_downside_only_when_paying_customers_exist(): void {
  const withTraction = getWhatIfScenarios(assumptionsWithTraction());
  expect(withTraction.some((s) => s.id === "churn"), "A venture with paying customers should be offered a churn/downside scenario");

  const ideaStage = getWhatIfScenarios(assumptionsIdeaStage());
  expect(!ideaStage.some((s) => s.id === "churn"), "An idea-stage venture with no paying customers must not be offered a churn scenario");
}

function test_what_if_never_overwrites_a_real_value_and_presents_it_as_progress(): void {
  // Every "upside" scenario's applied result must be >= the current value
  // for any numeric validation field it touches -- the core "never
  // silently downgrade and call it progress" rule.
  const current = assumptionsWithTraction();
  const scenarios = getWhatIfScenarios(current);

  for (const scenario of scenarios.filter((s) => s.direction === "upside")) {
    const result = scenario.apply(current);
    if (result.validation.paying_customers !== null && current.validation.paying_customers !== null) {
      expect(
        result.validation.paying_customers >= current.validation.paying_customers,
        `Upside scenario "${scenario.id}" must never lower paying_customers (${current.validation.paying_customers} -> ${result.validation.paying_customers})`
      );
    }
    if (result.validation.customer_interviews !== null && current.validation.customer_interviews !== null) {
      expect(
        result.validation.customer_interviews >= current.validation.customer_interviews,
        `Upside scenario "${scenario.id}" must never lower customer_interviews`
      );
    }
  }
}

function test_what_if_is_pure_and_does_not_mutate_the_input(): void {
  const original = assumptionsWithTraction();
  const snapshot = JSON.parse(JSON.stringify(original));
  const scenarios = getWhatIfScenarios(original);
  for (const scenario of scenarios) {
    scenario.apply(original);
  }
  expect(JSON.stringify(original) === JSON.stringify(snapshot), "getWhatIfScenarios/apply must never mutate the input assumptions object");
}

// --- Founder Loop V2 Acceptance Pass: venture card no longer dumps the ---
// --- entire raw description -----------------------------------------------

function test_summarize_concept_returns_null_for_no_description(): void {
  expect(summarizeConceptForCard(null) === null, "null description must summarize to null");
  expect(summarizeConceptForCard("   ") === null, "whitespace-only description must summarize to null");
}

function test_summarize_concept_uses_first_sentence_when_short(): void {
  const description = "ClaimPilot recovers denied healthcare claims. It also does other things in later sentences.";
  expect(
    summarizeConceptForCard(description) === "ClaimPilot recovers denied healthcare claims.",
    `Expected just the first sentence, got: ${summarizeConceptForCard(description)}`
  );
}

function test_summarize_concept_never_returns_the_entire_long_description(): void {
  // The real bug this test guards against: VentureWorkspace.tsx used to
  // pass the ENTIRE raw multi-paragraph description straight into
  // VentureCard's oneLineConcept prop.
  const longDescription = "ClaimPilot is an AI-powered revenue-cycle automation platform for independent medical practices and regional healthcare groups without a single period anywhere near the start of this very long run-on sentence that just keeps going and going and going and going and going and going and going and going and going and going and going well past a hundred and sixty characters to prove the point.";
  const result = summarizeConceptForCard(longDescription);
  expect(result !== null, "Expected a non-null summary");
  expect(result!.length < longDescription.length, "Summary must be shorter than the full description");
  expect(result!.length <= 165, `Summary must stay near the length cap, got ${result!.length} chars: "${result}"`);
}

function test_summarize_concept_is_pure(): void {
  const description = "A first sentence. A second sentence.";
  expect(summarizeConceptForCard(description) === summarizeConceptForCard(description), "Must be deterministic");
}

// --- Founder Progress / Venture History V1 ---------------------------------

function test_format_history_date_group_label_today_and_yesterday(): void {
  const now = new Date(2026, 8, 12, 15, 0, 0); // Sept 12, 2026, 3pm local
  const today = new Date(2026, 8, 12, 9, 0, 0).toISOString();
  const yesterday = new Date(2026, 8, 11, 23, 0, 0).toISOString();
  const older = new Date(2026, 7, 28, 10, 0, 0).toISOString();

  expect(formatHistoryDateGroupLabel(today, now) === "Today", `Expected "Today", got ${formatHistoryDateGroupLabel(today, now)}`);
  expect(formatHistoryDateGroupLabel(yesterday, now) === "Yesterday", `Expected "Yesterday", got ${formatHistoryDateGroupLabel(yesterday, now)}`);
  expect(formatHistoryDateGroupLabel(older, now) === "AUG 28", `Expected "AUG 28", got ${formatHistoryDateGroupLabel(older, now)}`);
}

function test_group_history_events_by_date_preserves_order_and_groups_consecutive_same_day(): void {
  const now = new Date(2026, 8, 12, 15, 0, 0);
  const events = [
    { event_type: "model_updated", occurred_at: new Date(2026, 8, 12, 10, 0, 0).toISOString() },
    { event_type: "learning_recorded", occurred_at: new Date(2026, 8, 12, 9, 0, 0).toISOString() },
    { event_type: "action_completed", occurred_at: new Date(2026, 8, 5, 9, 0, 0).toISOString() },
    { event_type: "venture_created", occurred_at: new Date(2026, 7, 28, 9, 0, 0).toISOString() },
  ];
  const groups = groupHistoryEventsByDate(events, now);
  expect(groups.length === 3, `Expected 3 date groups, got ${groups.length}`);
  expect(groups[0].label === "Today" && groups[0].events.length === 2, "The two Sept 12 events must be grouped under one 'Today' header, in original order");
  expect(groups[0].events[0].event_type === "model_updated", "Original chronological order (most-recent-first) must be preserved within a group");
  expect(groups[1].events.length === 1 && groups[2].events.length === 1, "Non-adjacent single-event days must not be merged");
}

function test_format_vps_delta(): void {
  expect(formatVpsDelta(7.4, 7.4) === "7.4 (unchanged)", `Expected unchanged framing, got "${formatVpsDelta(7.4, 7.4)}"`);
  expect(formatVpsDelta(7.0, 8.0) === "7.0 → 8.0", `Expected an arrow for a real change, got "${formatVpsDelta(7.0, 8.0)}"`);
  expect(formatVpsDelta(7.4, 6.9) === "7.4 → 6.9", "A decline must still be shown as a plain fact, not hidden");
  expect(formatVpsDelta(null, 7.4) === "7.4", "A null before value (e.g. a newly-scored category) must not crash or fabricate a delta");
}

// Founder Loop Final Acceptance Audit -- a real, demonstrated bug: the two
// quick-tag buttons in the "Record What I Learned" flow ("I learned
// something useful" / "No useful signal yet") unconditionally called
// setReflectionText(...), silently destroying any real reflection the
// founder had already typed. A live walkthrough reproduced this exactly.
// MissionsSection.tsx has no test coverage of its own (it's a stateful
// React component with real API calls, outside this repo's plain-node
// pure-file test family, and this repo has no jest/RTL to mount it) --
// this is a source-inspection guard in the same spirit as
// tests/playbooks.test.ts's own missionSuggestions.ts checks: it can't
// exercise the click behavior itself, but it makes reverting the guard
// (re-introducing the unconditional overwrite) fail CI.
function test_reflection_quick_tags_never_unconditionally_overwrite_founder_text(): void {
  const source = readFileSync(path.join(DASHBOARD_ROOT, "components/idea-lab/MissionsSection.tsx"), "utf-8");

  expect(
    source.includes("CANNED_REFLECTIONS"),
    "Expected a CANNED_REFLECTIONS guard constant -- has the reflection-preservation fix been removed?"
  );

  // Every setReflectionText("...") call that sets one of the two canned
  // phrases must appear only inside a guarded block (the literal
  // unconditional call form must not be reachable directly off onClick).
  expect(
    !/onClick=\{\(\) => setReflectionText\("I learned something useful\.?"?\)\}/.test(source),
    "The \"I learned something useful\" button must not unconditionally overwrite reflectionText"
  );
  expect(
    !/onClick=\{\(\) => setReflectionText\("No useful signal yet\.?"?\)\}/.test(source),
    "The \"No useful signal yet\" button must not unconditionally overwrite reflectionText"
  );
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
  ["test_recent_learning_empty_when_no_missions", test_recent_learning_empty_when_no_missions],
  ["test_recent_learning_empty_when_no_mission_has_learning", test_recent_learning_empty_when_no_mission_has_learning],
  ["test_recent_learning_picks_most_recent_by_recorded_at", test_recent_learning_picks_most_recent_by_recorded_at],
  ["test_recent_learning_considers_completed_missions_too", test_recent_learning_considers_completed_missions_too],
  ["test_recent_learning_is_pure_and_deterministic", test_recent_learning_is_pure_and_deterministic],
  ["test_latest_model_change_null_when_no_updates", test_latest_model_change_null_when_no_updates],
  ["test_latest_model_change_picks_first_since_events_are_newest_first", test_latest_model_change_picks_first_since_events_are_newest_first],
  ["test_latest_model_change_handles_no_assumption_diff", test_latest_model_change_handles_no_assumption_diff],
  ["test_latest_model_change_is_pure_and_deterministic", test_latest_model_change_is_pure_and_deterministic],
  ["test_journey_modules_contain_no_scoring_or_persistence_calls", test_journey_modules_contain_no_scoring_or_persistence_calls],
  ["test_venture_handoff_only_uses_sessionstorage_no_network", test_venture_handoff_only_uses_sessionstorage_no_network],
  ["test_infer_evidence_step_idea_with_nothing_modeled", test_infer_evidence_step_idea_with_nothing_modeled],
  ["test_infer_evidence_step_model_when_assumptions_present", test_infer_evidence_step_model_when_assumptions_present],
  ["test_infer_evidence_step_experiment_when_interviews_reported", test_infer_evidence_step_experiment_when_interviews_reported],
  ["test_infer_evidence_step_build_when_real_traction_exists", test_infer_evidence_step_build_when_real_traction_exists],
  ["test_infer_evidence_step_never_reaches_fundraise", test_infer_evidence_step_never_reaches_fundraise],
  ["test_resolve_step_index_prefers_the_more_advanced_of_manual_and_evidence", test_resolve_step_index_prefers_the_more_advanced_of_manual_and_evidence],
  ["test_venture_state_idea_with_nothing_modeled", test_venture_state_idea_with_nothing_modeled],
  ["test_venture_state_idea_when_only_assumptions_modeled", test_venture_state_idea_when_only_assumptions_modeled],
  ["test_venture_state_validating_when_interviews_reported", test_venture_state_validating_when_interviews_reported],
  ["test_venture_state_building_when_real_traction_exists", test_venture_state_building_when_real_traction_exists],
  ["test_venture_state_never_reaches_a_fundraise_state", test_venture_state_never_reaches_a_fundraise_state],
  ["test_venture_state_manual_stage_can_advance_but_not_invent_a_fourth_state", test_venture_state_manual_stage_can_advance_but_not_invent_a_fourth_state],
  ["test_venture_state_descriptions_are_plain_language_not_a_score", test_venture_state_descriptions_are_plain_language_not_a_score],
  ["test_what_if_never_suggests_a_lower_interview_count_than_already_reported", test_what_if_never_suggests_a_lower_interview_count_than_already_reported],
  ["test_what_if_suppresses_interview_scenario_at_commercial_scale", test_what_if_suppresses_interview_scenario_at_commercial_scale],
  ["test_what_if_scenarios_are_tagged_upside_or_downside", test_what_if_scenarios_are_tagged_upside_or_downside],
  ["test_what_if_offers_churn_downside_only_when_paying_customers_exist", test_what_if_offers_churn_downside_only_when_paying_customers_exist],
  ["test_what_if_never_overwrites_a_real_value_and_presents_it_as_progress", test_what_if_never_overwrites_a_real_value_and_presents_it_as_progress],
  ["test_what_if_is_pure_and_does_not_mutate_the_input", test_what_if_is_pure_and_does_not_mutate_the_input],
  ["test_summarize_concept_returns_null_for_no_description", test_summarize_concept_returns_null_for_no_description],
  ["test_summarize_concept_uses_first_sentence_when_short", test_summarize_concept_uses_first_sentence_when_short],
  ["test_summarize_concept_never_returns_the_entire_long_description", test_summarize_concept_never_returns_the_entire_long_description],
  ["test_summarize_concept_is_pure", test_summarize_concept_is_pure],
  ["test_format_history_date_group_label_today_and_yesterday", test_format_history_date_group_label_today_and_yesterday],
  ["test_group_history_events_by_date_preserves_order_and_groups_consecutive_same_day", test_group_history_events_by_date_preserves_order_and_groups_consecutive_same_day],
  ["test_format_vps_delta", test_format_vps_delta],
  ["test_reflection_quick_tags_never_unconditionally_overwrite_founder_text", test_reflection_quick_tags_never_unconditionally_overwrite_founder_text],
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
