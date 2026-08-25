// Compare Startups V1 -- GET /compare response shape. Deliberately
// slimmer than SIEMethodologyAnalysis (see app/models/startup.py's own
// comment on ComparisonPillar/ComparisonStartup): no raw evidence quotes,
// no executive_coaching_summary. Every field is read from the same
// stored methodology JSONB every other canonical surface reads.

import type { ConfidenceLevel } from "./startup";

export type EvidenceStatus = "Observed" | "Inferred" | "Unavailable";

export interface ComparisonSubscore {
  name: string;
  // null means this dimension could not be responsibly scored -- never
  // fabricated as 0.
  score: number | null;
  weight: number;
  confidence: ConfidenceLevel;
  evidence_status: EvidenceStatus;
  rationale: string;
  recommendations: string[];
  missing_information: string[];
}

export interface ComparisonPillar {
  pillar: string;
  // null means this whole pillar is Unavailable for this startup.
  score: number | null;
  confidence: ConfidenceLevel;
  evidence_coverage: number;
  summary: string;
  strengths: string[];
  weaknesses: string[];
  recommendations: string[];
  subscores: ComparisonSubscore[];
}

export interface ComparisonStartup {
  startup_id: number;
  company_name: string;
  industry: string;
  company_stage: string;
  business_model: string;
  latest_analysis_at: string;
  overall_score: number | null;

  market: ComparisonPillar;
  team: ComparisonPillar;
  product: ComparisonPillar;
  execution: ComparisonPillar;
  traction: ComparisonPillar;
  financial_health: ComparisonPillar;
}

export interface ComparisonResponse {
  startups: ComparisonStartup[];
  // Requested startup_ids that could not be resolved -- an invalid id, or
  // a real startup with no canonical analysis yet. Never silently
  // dropped without a trace.
  missing_startup_ids: number[];
}
