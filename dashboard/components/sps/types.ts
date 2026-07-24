export type Confidence = "Low" | "Medium" | "High";

export type SPSPillar =
  | "Market"
  | "Team"
  | "Product"
  | "Execution"
  | "Traction"
  | "Financial";

export interface SPSRingProps {
  score: number;

  trend?: number;

  percentile?: number;

  confidence?: Confidence;

  grade?: string;

  label?: string;

  size?: "sm" | "md" | "lg" | "xl";

  animated?: boolean;

  showDetails?: boolean;
}
