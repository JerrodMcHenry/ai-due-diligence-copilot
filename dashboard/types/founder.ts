import type { SIEMethodologyAnalysis, SPSHistoryPoint } from "./startup";

// Phase 31 -- Venture -> Startup Graduation V1, Part 11. Mirrors
// app/models/founder.py's GraduatedFromVenture exactly.
export interface GraduatedFromVenture {
  venture_id: number;
  venture_name: string;
}

// Phase 7.2 -- Founder Workspace V1. Mirrors app/models/founder.py's
// FounderStartupWorkspace exactly. Deliberately reuses SIEMethodologyAnalysis
// and SPSHistoryPoint as-is -- this is the same canonical intelligence the
// public Startup Profile shows, not a parallel shape.
export interface FounderStartupWorkspace {
  startup_id: number;
  canonical_name: string;
  created_at: string | null;
  methodology: SIEMethodologyAnalysis | null;
  sps_history: SPSHistoryPoint[];
  graduated_from_venture: GraduatedFromVenture | null;
}
