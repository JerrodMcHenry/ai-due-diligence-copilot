// Learn V1 -- mirrors content/playbooks/index.ts's own lookup-function
// pattern exactly (code/content-driven, zero I/O, zero "@/..." imports so
// this stays plain-`node`-testable -- see tests/concepts.test.ts).
import { METRIC_CONCEPTS, VPS_CATEGORY_CONCEPTS, WHAT_IF_SCENARIO_CONCEPTS } from "./data.ts";
import type { MetricConcept, VpsCategoryConcept } from "./types.ts";

export type { MetricConcept, VpsCategoryConcept } from "./types.ts";

export function getVpsCategoryConcept(categoryKey: string): VpsCategoryConcept | undefined {
  return VPS_CATEGORY_CONCEPTS[categoryKey];
}

export function getMetricConcept(key: string): MetricConcept | undefined {
  return METRIC_CONCEPTS[key];
}

export function getMetricConceptForWhatIfScenario(scenarioId: string): MetricConcept | undefined {
  const conceptKey = WHAT_IF_SCENARIO_CONCEPTS[scenarioId];
  return conceptKey ? METRIC_CONCEPTS[conceptKey] : undefined;
}
