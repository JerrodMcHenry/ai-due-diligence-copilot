// Phase 8 -- Fundraising Readiness V1. Mirrors
// app/models/fundraising_readiness.py exactly. This is a separate,
// deterministic assessment -- never SPS, never written to SPS history,
// never shown in Rankings/Compare. See
// app/ai/fundraising_readiness.py's own module docstring for the full
// design record.

export interface PillarReadiness {
  pillar: string;
  label: string;
  score: number | null;
  confidence: string;
  evidence_coverage: number;
  weight: number;
  readiness_contribution: number | null;
  top_strength: string | null;
  top_weakness: string | null;
}

export interface ReadinessGap {
  category: string;
  pillar: string | null;
  issue: string;
  why_it_matters: string;
  recommended_next_step: string;
  source_text: string;
}

export interface ChecklistItem {
  category: string;
  status: string;
  note: string;
}

export interface FundraisingReadiness {
  startup_id: number;
  canonical_name: string;
  has_canonical_analysis: boolean;
  stage_label: string;
  stage_recognized: boolean;
  readiness_score: number | null;
  readiness_band: string | null;
  pillar_readiness: PillarReadiness[];
  gaps: ReadinessGap[];
  investor_questions: string[];
  checklist: ChecklistItem[];
  has_pitch_deck: boolean;
  pitch_deck_note: string;
  current_sps: number | null;
  analyzed_at: string | null;
  // Phase 37D -- Unified Workspace Simplification + Legacy Containment.
  // Ownership-checked; non-null means this startup is linked to a
  // venture the caller owns, so the page redirects into that Venture
  // Workspace's Analyze tab instead of rendering here.
  linked_venture_id: number | null;
}
