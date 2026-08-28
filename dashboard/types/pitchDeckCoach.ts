// Phase 10.8 -- Pitch Deck Coach V1. Deliberately its own type family,
// not reusing StartupAnalysisResponse/SIEMethodologyAnalysis/VPSResult --
// a pitch deck review is architecturally separate from a canonical
// Startup analysis AND from a modeled venture. See
// app/models/pitch_deck_coach.py's own docstring for the full reasoning.
//
// Part 14's decision: there is deliberately no numeric field anywhere in
// this file. `readiness_label` is the only aggregate judgment, a small
// fixed vocabulary computed deterministically on the backend -- never a
// number, never rendered like a grade.

export type SectionStatus = "missing" | "unclear" | "effective";

export type SectionCategory =
  | "cover"
  | "problem"
  | "solution"
  | "product"
  | "market"
  | "business_model"
  | "traction"
  | "gtm"
  | "competition"
  | "team"
  | "financials"
  | "ask"
  | "other";

export type DeckReadinessLabel = "Early Draft" | "Developing" | "Getting Clear" | "Pitch Ready";

export interface DeckStoryField {
  found: boolean;
  summary: string;
  page_refs: number[];
}

export interface DeckStory {
  company: DeckStoryField;
  customer: DeckStoryField;
  problem: DeckStoryField;
  solution: DeckStoryField;
  business: DeckStoryField;
  proof: DeckStoryField;
  ask: DeckStoryField;
}

export interface DeckSectionCoaching {
  category: SectionCategory;
  label: string;
  status: SectionStatus;
  page_refs: number[];
  what_its_saying: string | null;
  whats_working: string | null;
  may_confuse: string | null;
  // Fixed educational copy per category -- always populated, not a
  // claim about this specific deck. See Part 8.
  why_investors_care: string;
  try_this: string | null;
}

export interface PriorityFix {
  title: string;
  issue: string;
  why_it_matters: string;
  try_this: string;
  related_category: SectionCategory;
}

export interface DeckStrength {
  title: string;
  why_it_works: string;
  related_category: SectionCategory;
}

export interface OpenQuestion {
  question: string;
  related_category: SectionCategory;
}

export interface PrepQuestion {
  question: string;
  related_category: SectionCategory;
}

export interface PitchDeckReview {
  id: number;
  deck_filename: string;
  page_count: number;
  readiness_label: DeckReadinessLabel;
  story: DeckStory;
  sections: DeckSectionCoaching[];
  top_fixes: PriorityFix[];
  strengths: DeckStrength[];
  open_questions: OpenQuestion[];
  prep_questions: PrepQuestion[];
  created_at: string;
}

export interface PitchDeckReviewSummary {
  id: number;
  deck_filename: string;
  readiness_label: DeckReadinessLabel;
  created_at: string;
}
