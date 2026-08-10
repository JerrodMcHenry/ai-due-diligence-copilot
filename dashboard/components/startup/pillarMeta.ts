// Shared pillar metadata and confidence-color mapping. Deliberately NOT a
// "use client" module — it's consumed by both server components
// (StartupHeroV2) and client components (IntelligencePillars, PillarNav,
// PillarWorkspace), and plain constants can't safely cross a "use client"
// boundary into server-rendered code in Next's RSC bundler. Single source
// of truth for pillar keys/labels and confidence badge colors either way.

import type { ConfidenceLevel } from "@/types";

export type PillarKey =
  | "market"
  | "team"
  | "product"
  | "execution"
  | "traction"
  | "financial_health";

export type PillarDefinition = {
  key: PillarKey;
  label: string;
};

export const PILLARS: PillarDefinition[] = [
  { key: "market", label: "Market" },
  { key: "team", label: "Team" },
  { key: "product", label: "Product" },
  { key: "execution", label: "Execution" },
  { key: "traction", label: "Traction" },
  { key: "financial_health", label: "Financial Health" },
];

export const CONFIDENCE_BADGE_CLASSES: Record<ConfidenceLevel, string> = {
  Low: "border border-border text-text-secondary",
  Medium: "bg-warning/10 text-warning",
  High: "bg-success/10 text-success",
};
