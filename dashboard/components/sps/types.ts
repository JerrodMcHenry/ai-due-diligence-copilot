export type Confidence = "Low" | "Medium" | "High";

export type SPSPillar =
  | "Market"
  | "Team"
  | "Product"
  | "Execution"
  | "Traction"
  | "Financial";

export interface SPSRingProps {
  // Phase 10.9, Part 15: null is a legitimate, common value -- "not
  // enough evidence to responsibly publish a score" -- and MUST render
  // as a distinct, honest "unavailable" state, never as a 0. See
  // unavailableLabel below.
  score: number | null;

  // Shown inside the ring, and as the ring's own aria-label, when score
  // is null. Keep this short -- it replaces the numeric score, not a
  // caption below it.
  unavailableLabel?: string;

  trend?: number;

  percentile?: number;

  confidence?: Confidence;

  grade?: string;

  label?: string;

  size?: "xs" | "sm" | "md" | "lg" | "xl";

  animated?: boolean;

  showDetails?: boolean;

  ariaLabel?: string;
}
