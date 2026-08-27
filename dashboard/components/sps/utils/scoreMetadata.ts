// Design System V2 (Phase 10.4): glowClass values below were literal
// hardcoded rgba() shadows (e.g. "rgba(34,197,94,0.18)") duplicating the
// success/primary/warning token colors in raw form -- a hardcoded-color
// bypass of the token system (Part 1's audit explicitly calls this out).
// Rewritten to derive the glow from the same --success/--primary/--warning
// custom properties every other token-driven color in this app uses, via
// the same color-mix() pattern globals.css already uses for ::selection.
// Each class string below is written out in full (not assembled from
// pieces at runtime) because Tailwind's build-time scanner extracts
// candidate classes by matching literal text in source files -- a
// dynamically-interpolated class name would never be generated. Visual
// output (color, radius, opacity, and how intensity scales with score) is
// unchanged -- this only changes where the color comes from, not what it
// looks like, and touches no score or grade boundary.

export type SPSMetadata = {
  grade: string;
  label: string;
  description: string;
  strokeClass: string;
  textClass: string;
  backgroundClass: string;
  glowClass: string;
};

export function normalizeSPS(score: number) {
  return Math.max(0, Math.min(score, 100));
}

export function getSPSMetadata(score: number): SPSMetadata {
  const normalizedScore = normalizeSPS(score);

  if (normalizedScore >= 95) {
    return {
      grade: "A+",
      label: "Exceptional",
      description:
        "Elite startup strength with outstanding overall performance.",
      strokeClass: "stroke-success",
      textClass: "text-success",
      backgroundClass: "bg-success/10",
      glowClass: "shadow-[0_0_40px_color-mix(in_srgb,var(--success)_18%,transparent)]",
    };
  }

  if (normalizedScore >= 90) {
    return {
      grade: "A",
      label: "Exceptional",
      description: "Outstanding performance across the core startup pillars.",
      strokeClass: "stroke-success",
      textClass: "text-success",
      backgroundClass: "bg-success/10",
      glowClass: "shadow-[0_0_36px_color-mix(in_srgb,var(--success)_16%,transparent)]",
    };
  }

  if (normalizedScore >= 85) {
    return {
      grade: "A−",
      label: "Excellent",
      description:
        "A highly competitive startup with limited major weaknesses.",
      strokeClass: "stroke-success",
      textClass: "text-success",
      backgroundClass: "bg-success/10",
      glowClass: "shadow-[0_0_32px_color-mix(in_srgb,var(--success)_14%,transparent)]",
    };
  }

  if (normalizedScore >= 80) {
    return {
      grade: "B+",
      label: "Excellent",
      description:
        "Strong performance with a clear path toward elite readiness.",
      strokeClass: "stroke-success",
      textClass: "text-success",
      backgroundClass: "bg-success/10",
      glowClass: "shadow-[0_0_28px_color-mix(in_srgb,var(--success)_12%,transparent)]",
    };
  }

  if (normalizedScore >= 75) {
    return {
      grade: "B",
      label: "Strong",
      description:
        "A strong startup with several meaningful competitive advantages.",
      strokeClass: "stroke-primary",
      textClass: "text-primary",
      backgroundClass: "bg-primary/10",
      glowClass: "shadow-[0_0_28px_color-mix(in_srgb,var(--primary)_12%,transparent)]",
    };
  }

  if (normalizedScore >= 70) {
    return {
      grade: "B−",
      label: "Strong",
      description:
        "Solid overall performance with identifiable areas to improve.",
      strokeClass: "stroke-primary",
      textClass: "text-primary",
      backgroundClass: "bg-primary/10",
      glowClass: "shadow-[0_0_24px_color-mix(in_srgb,var(--primary)_10%,transparent)]",
    };
  }

  if (normalizedScore >= 65) {
    return {
      grade: "C+",
      label: "Promising",
      description:
        "Promising fundamentals with important execution gaps remaining.",
      strokeClass: "stroke-warning",
      textClass: "text-warning",
      backgroundClass: "bg-warning/10",
      glowClass: "shadow-[0_0_24px_color-mix(in_srgb,var(--warning)_10%,transparent)]",
    };
  }

  if (normalizedScore >= 60) {
    return {
      grade: "C",
      label: "Promising",
      description:
        "Early strength is visible, but the startup still needs development.",
      strokeClass: "stroke-warning",
      textClass: "text-warning",
      backgroundClass: "bg-warning/10",
      glowClass: "shadow-[0_0_22px_color-mix(in_srgb,var(--warning)_9%,transparent)]",
    };
  }

  if (normalizedScore >= 50) {
    return {
      grade: "D",
      label: "Developing",
      description:
        "The startup has potential but several core areas need attention.",
      strokeClass: "stroke-warning",
      textClass: "text-warning",
      backgroundClass: "bg-warning/10",
      glowClass: "",
    };
  }

  if (normalizedScore >= 40) {
    return {
      grade: "D−",
      label: "Developing",
      description:
        "Foundational weaknesses are limiting current startup readiness.",
      strokeClass: "stroke-warning",
      textClass: "text-warning",
      backgroundClass: "bg-warning/10",
      glowClass: "",
    };
  }

  return {
    grade: "F",
    label: "Needs attention",
    description:
      "Major weaknesses require focused improvement before the startup is ready.",
    strokeClass: "stroke-danger",
    textClass: "text-danger",
    backgroundClass: "bg-danger/10",
    glowClass: "",
  };
}
